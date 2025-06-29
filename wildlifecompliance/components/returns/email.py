import logging

from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.utils.encoding import smart_text
from django.conf import settings
from django.core.urlresolvers import reverse
from ledger.payments.pdf import create_invoice_pdf_bytes
from ledger.payments.models import Invoice

from wildlifecompliance.components.main.utils import (
    remove_url_internal_request,
)

from wildlifecompliance.components.emails.emails import TemplateEmailBase

logger = logging.getLogger(__name__)

SYSTEM_NAME = 'Wildlife Compliance Automated Message'


class ReturnExternalSubmitSendNotificationEmail(TemplateEmailBase):
    subject = 'Your Return with requirements has been submitted.'
    html_template = 'wildlifecompliance/emails/send_external_submit_email_notification.html'
    txt_template = 'wildlifecompliance/emails/send_external_submit_email_notification.txt'


class ReturnAcceptNotificationEmail(TemplateEmailBase):
    subject = 'Your Return with conditions has been accepted.'
    html_template = 'wildlifecompliance/emails/send_external_return_accept_notification.html'
    txt_template = 'wildlifecompliance/emails/send_external_return_accept_notification.txt'


class ReturnExternalSheetTransferNotification(TemplateEmailBase):
    subject = 'Stock has been transferred to your Licence.'
    html_template = 'wildlifecompliance/emails/send_external_sheet_transfer_notification.html'
    txt_template = 'wildlifecompliance/emails/send_external_sheet_transfer_notification.txt'


class ReturnAmendmentNotificationEmail(TemplateEmailBase):
    subject = 'An amendment has been requested for your licence return'
    html_template = 'wildlifecompliance/emails/send_return_amendment_notification.html'
    txt_template = 'wildlifecompliance/emails/send_return_amendment_notification.txt'


class ReturnInvoiceNotificationEmail(TemplateEmailBase):
    subject = 'Your payment for your return has been received'
    html_template = \
        'wildlifecompliance/emails/send_return_invoice_notification.html'
    txt_template = \
        'wildlifecompliance/emails/send_return_invoice_notification.txt'

class ReturnInvoiceNotificationEmail(TemplateEmailBase):
    subject = 'Attached: Return Totals Report'
    html_template = 'wildlifecompliance/emails/send_return_count_report.html'
    txt_template = 'wildlifecompliance/emails/send_return_count_report.txt'

def send_return_accept_email_notification(return_obj, request):
    email = ReturnAcceptNotificationEmail()
    url = request.build_absolute_uri(
        '/external/return/{}'.format(return_obj.id)
    )

    context = {
        'Return': return_obj,
        'url': remove_url_internal_request(request, url)
    }
    msg = email.send(return_obj.submitter.email, context=context)
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    _log_return_email(msg, return_obj, sender=sender)


def send_external_submit_email_notification(request, return_obj):
    '''
    Sends a notification email to submitter confirming return submission.
    '''
    email = ReturnExternalSubmitSendNotificationEmail()
    url = request.build_absolute_uri(
        '/external/return/{}'.format(return_obj.id)
    )

    context = {
        'Return': return_obj,
        'submitter': return_obj.submitter.get_full_name(),
        'url': remove_url_internal_request(request, url)
    }

    msg = email.send(return_obj.submitter.email, context=context)
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    _log_return_email(msg, return_obj, sender=sender)


def send_sheet_transfer_email_notification(request, return_obj, licence):
    email = ReturnExternalSheetTransferNotification()
    url = request.build_absolute_uri(
        '/external/return/{}'.format(return_obj.id)
    )

    context = {
        'return_no': return_obj.id,
        'licence_no': licence.id,
        'submitter': request.user.email,
        'url': remove_url_internal_request(request, url)
    }

    msg = email.send(request.user.email, context=context)
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    _log_return_email(msg, return_obj, sender=sender)


def send_return_amendment_email_notification(request, data, return_obj, licence):
    email = ReturnAmendmentNotificationEmail()
    url = request.build_absolute_uri(
        '/external/return/{}'.format(return_obj.id)
    )

    context = {
        'lodgement_number': return_obj.lodgement_number,
        'reason': data['reason'],
        'text': data['text'],
        'url': remove_url_internal_request(request, url)
    }

    msg = email.send(return_obj.submitter.email, context=context)
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    _log_return_email(msg, return_obj, sender=sender)


def send_return_invoice_notification(returns, invoice_ref, request):
    # An email with return invoice to submitter
    email = ReturnInvoiceNotificationEmail()
    url = request.build_absolute_uri(
        reverse(
            'external-return-detail',
            kwargs={'return_pk': returns.id}))
    invoice_url = request.build_absolute_uri(
        reverse(
            'payments:invoice-pdf',
            kwargs={
                'reference': invoice_ref}))
    filename = 'invoice-{}-{}({}).pdf'.format(
        returns.id,
        returns.licence_type_short_name.replace(" ", "-"),
        returns.lodgement_date.date())
    references = [a.invoice_reference for a in returns.invoices.all()]
    invoice = Invoice.objects.filter(
        reference__in=references).order_by('-created')[0]
    invoice_pdf = create_invoice_pdf_bytes(filename, invoice)

    context = {
        'return': returns,
        'url': remove_url_internal_request(request, url),
        'invoice_url': invoice_url
    }
    recipients = [returns.submitter.email]
    msg = email.send(recipients, context=context, attachments=[
                     (filename, invoice_pdf, 'returns/pdf')])
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    _log_return_email(msg, returns, sender=sender)


def _log_return_email(email_message, return_obj, sender=None):
    from wildlifecompliance.components.returns.models import ReturnLogEntry
    if isinstance(email_message, (EmailMultiAlternatives, EmailMessage,)):
        # TODO this will log the plain text body, should we log the html
        # instead
        text = email_message.body
        subject = email_message.subject
        fromm = smart_text(sender) if sender else smart_text(
            email_message.from_email)
        # the to email is normally a list
        if isinstance(email_message.to, list):
            to = ','.join(email_message.to)
        else:
            to = smart_text(email_message.to)
        # we log the cc and bcc in the same cc field of the log entry as a ','
        # comma separated string
        all_ccs = []
        if email_message.cc:
            all_ccs += list(email_message.cc)
        if email_message.bcc:
            all_ccs += list(email_message.bcc)
        all_ccs = ','.join(all_ccs)

    else:
        text = smart_text(email_message)
        subject = ''
        to = return_obj.submitter.email
        fromm = smart_text(sender) if sender else SYSTEM_NAME
        all_ccs = ''

    customer = return_obj.submitter

    staff = sender

    kwargs = {
        'subject': subject,
        'text': text,
        'return_obj': return_obj,
        'customer': customer,
        'staff': staff,
        'to': to,
        'fromm': fromm,
        'cc': all_ccs
    }

    email_entry = ReturnLogEntry.objects.create(**kwargs)

    return email_entry


def _log_org_email(email_message, organisation, customer, sender=None):
    from wildlifecompliance.components.organisations.models import OrganisationLogEntry
    if isinstance(email_message, (EmailMultiAlternatives, EmailMessage,)):
        # TODO this will log the plain text body, should we log the html
        # instead
        text = email_message.body
        subject = email_message.subject
        fromm = smart_text(sender) if sender else smart_text(
            email_message.from_email)
        # the to email is normally a list
        if isinstance(email_message.to, list):
            to = ','.join(email_message.to)
        else:
            to = smart_text(email_message.to)
        # we log the cc and bcc in the same cc field of the log entry as a ','
        # comma separated string
        all_ccs = []
        if email_message.cc:
            all_ccs += list(email_message.cc)
        if email_message.bcc:
            all_ccs += list(email_message.bcc)
        all_ccs = ','.join(all_ccs)

    else:
        text = smart_text(email_message)
        subject = ''
        to = customer.email
        fromm = smart_text(sender) if sender else SYSTEM_NAME
        all_ccs = ''

    customer = customer

    staff = sender

    kwargs = {
        'subject': subject,
        'text': text,
        'organisation': organisation,
        'customer': customer,
        'staff': staff,
        'to': to,
        'fromm': fromm,
        'cc': all_ccs
    }

    email_entry = OrganisationLogEntry.objects.create(**kwargs)

    return email_entry
