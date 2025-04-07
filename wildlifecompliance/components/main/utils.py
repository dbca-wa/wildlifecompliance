import ast
import re

import pytz
import json
import logging
from django.conf import settings
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse
from ledger_api_client.utils import (
    create_basket_session,
    create_checkout_session,
    place_order_submission
)
from django.db import transaction
from ledger_api_client.ledger_models import Invoice
from wildlifecompliance.exceptions import BindApplicationException
from django.core.cache import cache
from wildlifecompliance.components.main.models import RegionGIS, DistrictGIS

logger = logging.getLogger(__name__)


def singleton(cls):
    instance = [None]

    def wrapper(*args, **kwargs):
        if instance[0] is None:
            instance[0] = cls(*args, **kwargs)
        return instance[0]

    return wrapper


class ListEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, list):
            inv_str = ''
            for o in obj:
                inv_str += ' ' + str(o)
            return inv_str.lstrip()

    def encode_list(self, obj, iter=None):
        if isinstance(obj, (list)):
            return self.default(obj)
        else:
            return super(ListEncoder, self).encode_list(obj, iter)


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        from decimal import Decimal as D
        if isinstance(obj, D):
            return float(obj)
        return json.JSONEncoder.default(self, obj)


#def retrieve_department_users():
#    print(settings.CMS_URL)
#    try:
#        #res = requests.get('{}/api/users?minimal'.format(settings.CMS_URL), auth=(settings.LEDGER_USER,settings.LEDGER_PASS), verify=False)
#        #res = requests.get('{}/api/users?minimal'.format(settings.EXT_USER_API_ROOT_URL), auth=(settings.LEDGER_USER,settings.LEDGER_PASS), verify=False)
#        #res = requests.get('{}/api/users/fast?/compact'.format(settings.EXT_USER_API_ROOT_URL), 
#        res = requests.get('{}/api/v3/departmentuser/'.format(settings.EXT_USER_API_ROOT_URL), 
#                auth=(settings.LEDGER_USER,settings.LEDGER_PASS), verify=False)
#        res.raise_for_status()
#        cache.set('department_users',json.loads(res.content).get('objects'),10800)
#    except:
#        raise
#
#def get_department_user(email):
#    try:
#        res = requests.get(
#            '{}/api/users?email={}'.format(
#                settings.EXT_USER_API_ROOT_URL, email),
#            auth=(settings.LEDGER_USER, settings.LEDGER_PASS),
#            verify=False)
#        res.raise_for_status()
#        data = json.loads(res.content).get('objects')
#        if len(data) > 0:
#            return data[0]
#        else:
#            return None
#    except BaseException:
#        raise

def checkout(
        request,
        application,
        lines=[],
        invoice_text=None,
        vouchers=[],
        internal=False,
        add_checkout_params={}):
    
    basket_params = {
        'products': lines,
        'vouchers': vouchers,
        'system': settings.WC_PAYMENT_SYSTEM_ID,
        'custom_basket': True,
        'booking_reference': application.lodgement_number,
        'booking_reference_link': application.lodgement_number,
        'no_payment': False,
    }
    print(basket_params)
    basket_hash = create_basket_session(request, request.user.id, basket_params)

    checkout_params = {
        'system': settings.WC_PAYMENT_SYSTEM_ID,
        'fallback_url': request.build_absolute_uri('/'),
        'return_url': request.build_absolute_uri(reverse('external-application-success-invoice')),
        'return_preload_url': settings.WILDLIFECOMPLIANCE_EXTERNAL_URL + reverse('external-application-success-invoice-preload',kwargs={"lodgement_number": application.lodgement_number}),
        'force_redirect': True,
        #'proxy': True if internal else False,
        'invoice_text': invoice_text,
        'basket_owner': request.user.id,
        'session_type': 'ledger_api',
    }
    
    checkout_params.update(add_checkout_params)
    print(' -------- main utils > checkout > checkout_params ---------- ')
    print(checkout_params)
    create_checkout_session(request, checkout_params)

    response = HttpResponse(
        reverse('ledgergw-payment-details')
    )

    return response


def internal_create_application_invoice(application, reference):
    from wildlifecompliance.components.applications.models import ApplicationInvoice
    try:
        Invoice.objects.get(reference=reference)
    except Invoice.DoesNotExist:
        raise Exception(
            "There was a problem attaching an invoice for this application")
    app_inv = ApplicationInvoice.objects.create(
        application=application, invoice_reference=reference)
    return app_inv


@transaction.atomic
def create_other_application_invoice(application, request=None):
    '''
    Create and return an Invoice for an application.
    '''
    from wildlifecompliance.components.applications.models import (
        ApplicationInvoice,
        ActivityInvoice,
        ActivityInvoiceLine,
    )

    try:
        other_pay_method = get_session_other_pay_method(request.session)
        delete_session_other_pay_method(request.session)

        order = create_application_invoice(
            application, payment_method='other')
        invoice = Invoice.objects.get(order_number=order.number)

        app_inv, c = ApplicationInvoice.objects.get_or_create(
            application=application,
            invoice_reference=invoice.reference,
            other_payment_method=other_pay_method,
        )

        # record invoice payment for licence activities.
        for activity in application.activities:

            act_inv = ActivityInvoice.objects.get_or_create(
                activity=activity,
                invoice_reference=invoice.reference
            )

            paid_purposes = [
                p for p in activity.proposed_purposes.all()
                if p.is_payable
            ]

            for p in paid_purposes:

                fee = p.get_payable_licence_fee()
                l_type = ActivityInvoiceLine.LINE_TYPE_LICENCE
                ActivityInvoiceLine.objects.get_or_create(
                    invoice=act_inv[0],
                    licence_activity=activity.licence_activity,
                    licence_purpose=p.purpose,
                    amount=fee,
                    invoice_line_type=l_type,
                )

                fee = p.get_payable_application_fee()
                l_type = ActivityInvoiceLine.LINE_TYPE_APPLICATION
                ActivityInvoiceLine.objects.get_or_create(
                    invoice=act_inv[0],
                    licence_activity=activity.licence_activity,
                    licence_purpose=p.purpose,
                    amount=fee,
                    invoice_line_type=l_type,
                )

        return invoice

    except Exception as e:
        logger.error(
            'Fail to create OTHER invoice for {0} : {1}'.format(application, e)
        )


@transaction.atomic
def create_application_invoice(application, payment_method='cc'):
    '''
    This will create and invoice and order from a basket bypassing the session
    and payment bpoint code constraints.
    '''
    from wildlifecompliance.components.applications.services import (
        ApplicationService,
    )
    from ledger_api_client.utils import createCustomBasket
    from ledger.payments.invoice.utils import CreateInvoiceBasket

    products = ApplicationService.get_product_lines(application)
    user = application.submitter
    invoice_text = 'Payment Invoice'

    basket = createCustomBasket(
        products, user, settings.WC_PAYMENT_SYSTEM_ID
    )
    order = CreateInvoiceBasket(
        payment_method=payment_method,
        system=settings.WC_PAYMENT_SYSTEM_PREFIX

    ).create_invoice_and_order(
        basket, 0, None, None, user=user, invoice_text=invoice_text)

    return order


def set_session_application(session, application):
    print('setting session application')
    session['wc_application'] = application.id
    session.modified = True


def get_session_application(session):
    print('getting session application')
    from wildlifecompliance.components.applications.models import Application
    if 'wc_application' in session:
        application_id = session['wc_application']
    else:
        raise Exception('Application not in Session')

    try:
        return Application.objects.get(id=application_id)
    except Application.DoesNotExist:
        raise Exception(
            'Application not found for application_id {}'.format(application_id))


def delete_session_application(session):
    if 'wc_application' in session:
        del session['wc_application']
        session.modified = True


def set_session_other_pay_method(session, other_pay_method):
    '''
    Set the Other payment method type on the session for a ledger payment.
    '''
    OTHER_PAY_METHOD = 'wc_other_pay_method'

    session[OTHER_PAY_METHOD] = other_pay_method
    session.modified = True


def get_session_other_pay_method(session):
    '''
    Set the Other payment method type from the session for a ledger payment.
    '''
    OTHER_PAY_METHOD = 'wc_other_pay_method'

    if OTHER_PAY_METHOD in session:
        other_pay_method = session[OTHER_PAY_METHOD]

    else:
        raise Exception('Payment Method does not exist on Session')

    return other_pay_method


def delete_session_other_pay_method(session):
    '''
    Cleanup the Other payment method type from the session.
    '''
    OTHER_PAY_METHOD = 'wc_other_pay_method'

    if OTHER_PAY_METHOD in session:
        del session[OTHER_PAY_METHOD]
        session.modified = True


def flush_checkout_session(session):
    keys = [
        'checkout_data',
        'checkout_invoice',
        'checkout_order_id',
        'checkout_return_url',
        'checkout_data',
    ]
    for key in keys:
        try:
            del session[key]
        except KeyError:
            continue


def set_session_activity(session, activity):
    session['wc_activity'] = activity.id
    session.modified = True


def get_session_activity(session):
    from wildlifecompliance.components.applications.models import ApplicationSelectedActivity
    try:
        activity_id = session['wc_activity']
    except KeyError:
        raise Exception('Session does not contain Activity ID')

    try:
        return ApplicationSelectedActivity.objects.get(id=activity_id)
    except ApplicationSelectedActivity.DoesNotExist:
        raise Exception(
            'Activity ID not found: {}'.format(activity_id))


def delete_session_activity(session):
    try:
        del session['wc_activity']
        session.modified = True
    except KeyError:
        pass


def bind_application_to_invoice(application, invoice_ref):
    from wildlifecompliance.components.applications.models import ApplicationInvoice, ApplicationInvoiceLine
    logger = logging.getLogger('application_checkout')
    try:
        inv = Invoice.objects.get(reference=invoice_ref)
    except Invoice.DoesNotExist:
        logger.error(
            u'{} tried making an application with an incorrect invoice'.format(
                u'User {} with id {}'.format(
                    application.submitter.get_full_name(),
                    application.submitter.id) if application.submitter else u'An anonymous user'))
        raise BindApplicationException

    if inv.system not in [settings.WC_PAYMENT_SYSTEM_PREFIX]:
        logger.error(
            u'{} tried making an application with an invoice from another system with reference number {}'.format(
                u'User {} with id {}'.format(
                    application.submitter.get_full_name(),
                    application.submitter.id) if application.submitter else u'An anonymous user',
                inv.reference))
        raise BindApplicationException

    try:
        a = ApplicationInvoice.objects.get(invoice_reference=invoice_ref)
        logger.error(
            u'{} tried making an application with an already used invoice with reference number {}'.format(
                u'User {} with id {}'.format(
                    application.submitter.get_full_name(),
                    application.submitter.id) if application.submitter else u'An anonymous user',
                a.invoice_reference))
        raise BindApplicationException
    except ApplicationInvoice.DoesNotExist:
        logger.info(
            u'{} submitted application {}, creating new ApplicationInvoice with reference {}'.format(
                u'User {} with id {}'.format(
                    application.submitter.get_full_name(),
                    application.submitter.id) if application.submitter else u'An anonymous user',
                application.id,
                invoice_ref))
        app_inv, created = ApplicationInvoice.objects.get_or_create(
            application=application, invoice_reference=invoice_ref)
        for activity in application.activities:
            ApplicationInvoiceLine.objects.create(
                invoice=app_inv,
                licence_activity=activity.licence_activity,
                amount=activity.application_fee
            )
        application.save()

        #request.session['wc_last_application'] = application.id

        # send out the invoice before the confirmation is sent
        # send_application_invoice(application)
        # for fully paid applications, fire off confirmation email
        # if application.paid:
        #    send_application_confirmation(application, request)


def get_choice_value(key, choices):
    try:
        return [choice[1] for choice in choices if choice[0] == key][0]
    except IndexError:
        logger = logging.getLogger(__name__)
        logger.error("Key %s does not exist in choices: %s" % (key, choices))
        raise


def search_keywords(search_words, search_application, search_licence, search_return, is_internal=True):
    '''
    :param search_words: list object, keywords to search for
    :param search_application: Boolean, if true, search keywords against applications
    :param search_licence: Boolean, if true, search keywords against licences
    :param search_return: Boolean, if true, search keywords against returns
    :param is_internal: Boolean, if true, pre-load application, licence, return objects to lists
    :return:
    '''
    from wildlifecompliance.utils import search
    from wildlifecompliance.components.applications.models import Application, ApplicationFormDataRecord
    from wildlifecompliance.components.licences.models import WildlifeLicence
    from wildlifecompliance.components.returns.models import Return
    qs = []
    application_list = []
    licence_list = []
    return_list = []
    if search_words:
        search_words_regex = "(?:"
        for i in range(0,len(search_words)):
            search_words_regex = search_words_regex + search_words[i]
            if i == len(search_words)-1:
                search_words_regex = search_words_regex + ")"
            else:
                search_words_regex = search_words_regex + "|"

        #filter_regex = ".*\".*\":\s\"(\\\\\"|[^\"])*"+search_words_regex+"(\\\\\"|[^\"])*\".*"
        if is_internal:
            application_list = Application.objects.all().filter(form_data_records__value__iregex=search_words_regex)\
            .order_by('lodgement_number', '-id')\
            .distinct('lodgement_number') 
                #.computed_exclude(processing_status__in=[
                #    Application.PROCESSING_STATUS_DISCARDED
                #])\
            licence_list = WildlifeLicence.objects\
            .filter(licence_number__iregex=search_words_regex)\
            .order_by('licence_number', '-id')\
            .distinct('licence_number')  
            return_list = Return.objects.all()\
            .filter(lodgement_number__iregex=search_words_regex)\
            .order_by('lodgement_number', '-id')\
            .distinct('lodgement_number') 
            
        if search_application:
            for app in application_list:
                if app.data:
                    try:
                        app_data = {'data': []}
                        for record in app.data:
                            if 'thead' in record.value:
                                try:
                                    app_data.get('data').append({'value': ast.literal_eval(record.value).get('tbody')})
                                except:
                                    app_data.get('data').append({'value': record.value})
                            else:
                                app_data.get('data').append({'value': record.value})
                        results = search(app_data, search_words)
                        final_results = {}
                        if results:
                            for r in results:
                                for key, value in r.items():
                                    final_results.update({'key': key, 'value': value})
                            res = {
                                'number': app.lodgement_number,
                                'record_id': app.id,
                                'record_type': 'Application',
                                'applicant': app.applicant,
                                'text': final_results,
                                'licence_document': None
                            }
                            qs.append(res)
                    except BaseException:
                        raise
        if search_licence:
            for lic in licence_list:
                try:
                    results = []
                    final_results = {}
                    for s in search_words:
                        if s.lower() in lic.licence_number.lower():
                            results.append({
                                'number': lic.licence_number,
                            })
                    if results:
                        for r in results:
                            for key, value in r.items():
                                final_results.update({'key': key, 'value': value})
                        res = {
                            'number': lic.licence_number,
                            'record_id': lic.id,
                            'record_type': 'Licence',
                            'applicant': lic.current_application.applicant,
                            'text': final_results,
                            'licence_document': lic.licence_document
                        }
                        qs.append(res)
                except BaseException:
                    raise
        if search_return:
            for ret in return_list:
                try:
                    results = []
                    final_results = {}
                    for s in search_words:
                        if s.lower() in ret.lodgement_number.lower():
                            results.append({
                                'number': ret.lodgement_number,
                            })
                    if results:
                        for r in results:
                            for key, value in r.items():
                                final_results.update({'key': key, 'value': value})
                        res = {
                            'number': ret.lodgement_number,
                            'record_id': ret.id,
                            'record_type': 'Return',
                            'applicant': ret.application.applicant,
                            'text': final_results,
                            'licence_document': None
                        }
                        qs.append(res)
                except BaseException:
                    raise
        return qs


def search_reference(reference_number):
    from wildlifecompliance.components.applications.models import Application
    from wildlifecompliance.components.organisations.models import OrganisationRequest
    from wildlifecompliance.components.licences.models import WildlifeLicence
    from wildlifecompliance.components.returns.models import Return
    from wildlifecompliance.components.call_email.models import CallEmail
    from wildlifecompliance.components.offence.models import Offence
    from wildlifecompliance.components.legal_case.models import LegalCase
    from wildlifecompliance.components.inspection.models import Inspection
    from wildlifecompliance.components.sanction_outcome.models import SanctionOutcome
    from wildlifecompliance.components.artifact.models import Artifact
    application_list = Application.objects.all()
    #this makes the ref search go from under a second to up to 2 minutes - it is better to allow discarded applications to be searched
    #.computed_exclude(processing_status__in=[Application.PROCESSING_STATUS_DISCARDED])
    licence_list = WildlifeLicence.objects.all().order_by('licence_number').distinct('licence_number')
    returns_list = Return.objects.all().exclude(processing_status__in=[Return.RETURN_PROCESSING_STATUS_FUTURE])
    org_access_request_list = OrganisationRequest.objects.all()
    url_string = {}

    # Application
    result = application_list.filter(lodgement_number=reference_number)
    if result:
        url_string = {'url_string': '/internal/application/' + str(result[0].id)}
        return url_string
    # Licence
    result = licence_list.filter(licence_number=reference_number)
    if result and not url_string:
        url_string = {'url_string': result[0].licence_document._file.url}
        return url_string
    # Returns
    result = returns_list.filter(lodgement_number=reference_number)
    if result and not url_string:
        url_string = {'url_string': '/internal/return/' + str(result[0].id)}
        return url_string
    #import ipdb; ipdb.set_trace()
    # Org access reqeust
    result = org_access_request_list.filter(lodgement_number=reference_number)
    if result and not url_string:
        url_string = {'url_string': '/internal/organisations/access/' + str(result[0].id)}
        return url_string
    # CallEmail
    result = CallEmail.objects.filter(number=reference_number)
    if result and not url_string:
        url_string = {'url_string': '/internal/call_email/' + str(result[0].id)}
        return url_string
    # Offence
    result = Offence.objects.filter(lodgement_number=reference_number)
    if result and not url_string:
        url_string = {'url_string': '/internal/offence/' + str(result[0].id)}
        return url_string
    # Legal Case
    result = LegalCase.objects.filter(number=reference_number)
    if result and not url_string:
        url_string = {'url_string': '/internal/legal_case/' + str(result[0].id)}
        return url_string
    # Inspection
    result = Inspection.objects.filter(number=reference_number)
    if result and not url_string:
        url_string = {'url_string': '/internal/inspection/' + str(result[0].id)}
        return url_string
    # Sanction Outcome
    result = SanctionOutcome.objects.filter(lodgement_number=reference_number)
    if result and not url_string:
        url_string = {'url_string': '/internal/sanction_outcome/' + str(result[0].id)}
        return url_string
    # Offence
    result = Artifact.objects.filter(number=reference_number)
    if result and not url_string:
        url_string = {'url_string': '/internal/object/' + str(result[0].id)}
        return url_string

    if url_string:
        return url_string
    else:
        #raise ValidationError('Record with provided reference number does not exist')
        return {'error': 'Record with provided reference number does not exist'}


def add_url_internal_request(request, url):
    '''
    Add '-internal' for url link.
    '''
    from django.conf import settings
    if '-internal' not in url:
        url = "{0}://{1}{2}.{3}{4}".format(request.scheme,
                                           settings.SITE_PREFIX,
                                           '-internal',
                                           settings.SITE_DOMAIN,
                                           url.split(request.get_host())[1])

    return url


def remove_url_internal_request(request, url):
    '''
    Remove '-internal' from url link.
    '''
    from django.conf import settings
    if '-internal' in url:
        url = "{0}://{1}.{2}{3}".format(request.scheme,
                                        settings.SITE_PREFIX,
                                        settings.SITE_DOMAIN,
                                        url.split(request.get_host())[1])

    return url


class FakeRequest():
    def __init__(self, data):
        self.data = data
        self.user = None


def to_local_tz(_date):
    local_tz = pytz.timezone(settings.TIME_ZONE)
    return _date.astimezone(local_tz)


def get_region_district(wkb_geometry):
    try:
        regions = RegionGIS.objects.filter(wkb_geometry__contains=wkb_geometry)
        districts = DistrictGIS.objects.filter(wkb_geometry__contains=wkb_geometry)
        text_arr = []
        if regions:
            text_arr.append(regions.first().region_name)
        if districts:
            text_arr.append(districts.first().district_name)

        ret_text = '/'.join(text_arr)
        return ret_text
    except:
        return ''

def get_region_gis(wkb_geometry):
    try:
        regions = RegionGIS.objects.filter(wkb_geometry__contains=wkb_geometry)
        if regions:
            region_name = regions.first().region_name
            return region_name
        return ''
    except:
        return ''

def get_district_gis(wkb_geometry):
    try:
        districts = DistrictGIS.objects.filter(wkb_geometry__contains=wkb_geometry)
        if districts:
            district_name = districts.first().district_name
            return district_name
        return ''
    except:
        return ''

def get_first_name(obj):

    if hasattr(obj,"legal_first_name") and obj.legal_first_name:
        return obj.legal_first_name
    elif hasattr(obj,"first_name") and obj.first_name:
        return obj.first_name

    return ""

def get_last_name(obj):

    if hasattr(obj,"legal_last_name") and obj.legal_last_name:
        return obj.legal_last_name
    elif hasattr(obj,"last_name") and obj.last_name:
        return obj.last_name

    return ""

def get_full_name(obj):
    return get_first_name(obj)+" "+get_last_name(obj)

def get_dob(obj):

    if hasattr(obj,"legal_dob") and obj.legal_dob:
        return obj.legal_dob
    if hasattr(obj,"dob") and obj.dob:
        return obj.dob

    return ""

def remove_html_tags(text):

    if text is None:
        return None

    HTML_TAGS_WRAPPED = re.compile(r'<[^>]+>.+</[^>]+>')
    HTML_TAGS_NO_WRAPPED = re.compile(r'<[^>]+>')

    text = HTML_TAGS_WRAPPED.sub('', text)
    text = HTML_TAGS_NO_WRAPPED.sub('', text)
    return text

def remove_script_tags(text):

    if text is None:
        return None

    SCRIPT_TAGS_WRAPPED = re.compile(r'(?i)<script+>.+</script+>')
    SCRIPT_TAGS_NO_WRAPPED = re.compile(r'(?i)<script+>')

    text = SCRIPT_TAGS_WRAPPED.sub('', text)
    text = SCRIPT_TAGS_NO_WRAPPED.sub('', text)
    return text

def sanitise_fields(instance, exclude=[], error_on_change=[]):
    for i in instance.__dict__:
        #remove html tags for all string fields not in the exclude list
        if isinstance(instance.__dict__[i], str) and not i in exclude:
            check = instance.__dict__[i]
            setattr(instance, i, remove_html_tags(instance.__dict__[i]))
            if i in error_on_change and check != instance.__dict__[i]:
                #only fields that cannot be allowed to change through sanitisation just before saving will throw an error
                raise ValidationError("html tags included in field")
        elif isinstance(instance.__dict__[i], str) and i in exclude:
            #even though excluded, we still check to remove script tags
            setattr(instance, i, remove_script_tags(instance.__dict__[i]))
            if i in error_on_change and check != instance.__dict__[i]:
                #only fields that cannot be allowed to change through sanitisation just before saving will throw an error
                raise ValidationError("script tags included in field")

    return instance