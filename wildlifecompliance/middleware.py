import logging

from django.urls import reverse
from django.shortcuts import redirect
from urllib.parse import quote
from django.conf import settings

from wildlifecompliance.management.securebase_manager import (
    SecureBaseUtils,
    SecureAuthorisationEnforcer,
)
from wildlifecompliance.components.users.models import ComplianceManagementUserPreferences
from wildlifecompliance.components.applications.models import Application
from wildlifecompliance.components.sanction_outcome.models import SanctionOutcome
from wildlifecompliance.helpers import (
        is_compliance_management_callemail_readonly_user,
        is_compliance_management_readonly_user,
        is_compliance_management_user,
        )

logger = logging.getLogger(__name__)
import re
from django.http import HttpResponse
import hashlib
# logger = logging
CHECKOUT_PATH = re.compile('^/ledger/checkout/checkout')


class FirstTimeNagScreenMiddleware(object):
    '''
    Generic FirstTimeNagScreenMiddleware.
    '''
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if 'static' in request.path:
            return self.get_response
        if (request.method == 'GET' 
            and request.user.is_authenticated
            and 'api' not in request.path 
            and 'admin' not in request.path):
            # add CM Approved External users to CallEmail RO and volunteer groups
            #if is_compliance_management_approved_external_user(request):
            #    if not is_compliance_management_callemail_readonly_user(request):
            #        ComplianceManagementSystemGroup.objects.get(name=settings.GROUP_COMPLIANCE_MANAGEMENT_CALL_EMAIL_READ_ONLY).add_member(request.user)
            #    if not is_compliance_management_volunteer(request):
            #        ComplianceManagementSystemGroup.objects.get(name=settings.GROUP_VOLUNTEER).add_member(request.user)
            # Ensure CallEmail RO group users have prefer_compliance_management=True
            preference, created = ComplianceManagementUserPreferences.objects.get_or_create(email_user=request.user)
            if is_compliance_management_callemail_readonly_user(request) and not preference.prefer_compliance_management:
                preference.prefer_compliance_management = True
                preference.save()
            # If no CM read only role, revert to WL
            if not is_compliance_management_callemail_readonly_user(request) and not is_compliance_management_readonly_user(request):
                preference.prefer_compliance_management = False
                preference.save()

        if not is_compliance_management_user(request) and SecureBaseUtils.is_wildlifelicensing_request(request):
        #if SecureBaseUtils.is_wildlifelicensing_request(request):
            # Apply WildifeLicensing first-time checks.
            first_time_nag = SecureAuthorisationEnforcer(request)

        else:
            first_time_nag = FirstTimeDefaultNag()

        #response = first_time_nag.process_request(request)
        return self.get_response(request)


class FirstTimeDefaultNag(object):
    '''
    A specialised FirstTimeNagScreenMiddleware for non WildlifeLicensing.
    '''

    def process_request(self, request):

        if 'static' in request.path:
            return

        if (request.method == 'GET' 
            and request.user.is_authenticated
            and 'api' not in request.path 
            and 'admin' not in request.path 
            and 'ledger-private' not in request.path):

            #(not request.user.dob and not request.user.legal_dob) or \
            print(request.user.first_name,request.user.last_name)
            if (not request.user.first_name) or \
                    (not request.user.last_name) or \
                    (not request.user.dob ) or \
                    (not request.user.residential_address) or \
                    (not (
                        request.user.phone_number or request.user.mobile_number
                    )):
                path_ft = reverse('first_time')
                path_logout = reverse('logout')
                request.session['new_to_wildlifecompliance'] = True
                if request.path not in (path_ft, path_logout):
                    return redirect(
                        reverse('first_time') +
                        "?next=" +
                        quote(
                            request.get_full_path()))


class CacheControlMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.path[:5] == '/api/' or request.path == '/':
            response['Cache-Control'] = 'private, no-store'
        elif request.path[:8] == '/static/':
            response['Cache-Control'] = 'public, max-age=86400'
        else:
            response['Cache-Control'] = 'private, no-store'
        return response


class PaymentSessionMiddleware(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def process_view(self, request, view_func, view_args, view_kwargs):

        if (request.user.is_authenticated 
        and (CHECKOUT_PATH.match(request.path)
        or request.path.startswith("/ledger-api/process-payment") 
        or request.path.startswith('/ledger-api/payment-details'))):
            if 'payment_model' in request.session and 'payment_pk' in request.session:
                if request.path.startswith("/ledger-api/process-payment"):

                    checkouthash =  hashlib.sha256(str(str(request.session["payment_model"])+str(request.session["payment_pk"])).encode('utf-8')).hexdigest() 
                    checkouthash_cookie = request.COOKIES.get('checkouthash')
                    validation_cookie = request.COOKIES.get(request.POST['payment-csrfmiddlewaretoken'])

                    if request.session['payment_model'] == "application":
                        record_count = Application.objects.filter(pk=request.session['payment_pk']).count()
                    elif request.session['payment_model'] == "sanction_outcome":
                        record_count = SanctionOutcome.objects.filter(pk=request.session['payment_pk']).count() 

                    if checkouthash_cookie != checkouthash or checkouthash_cookie != validation_cookie or record_count == 0:                         
                        url_redirect = reverse("/")
                        response = HttpResponse("<script> window.location='"+url_redirect+"';</script> <center><div class='container'><div class='alert alert-primary' role='alert'><a href='"+url_redirect+"'> Redirecting please wait: "+url_redirect+"</a><div></div></center>")
                        return response  
            else:
                 if request.path.startswith("/ledger-api/process-payment"):
                    url_redirect = reverse("/")
                    response = HttpResponse("<script> window.location='"+url_redirect+"';</script> <center><div class='container'><div class='alert alert-primary' role='alert'><a href='"+url_redirect+"'> Redirecting please wait: "+url_redirect+"</a><div></div></center>")
                    return response
                 
        return None

    def __call__(self, request):

        response= self.get_response(request)

        if (request.user.is_authenticated 
        and (CHECKOUT_PATH.match(request.path)
        or request.path.startswith("/ledger-api/process-payment") 
        or request.path.startswith('/ledger-api/payment-details'))):
            if 'payment_model' in request.session and 'payment_pk' in request.session:
                try:
                    if request.session['payment_model'] == "application":
                        Application.objects.get(pk=request.session['payment_pk'])
                    elif request.session['payment_model'] == "sanction_outcome":
                        SanctionOutcome.objects.get(pk=request.session['payment_pk'])
                except Exception as e:
                    del request.session['payment_model']
                    del request.session['payment_pk']
                    return response
                
                if request.path.startswith("/ledger-api/process-payment"):

                    if "payment_pk" not in request.session:
                        url_redirect = reverse("/")
                        response = HttpResponse("<script> window.location='"+url_redirect+"';</script> <center><div class='container'><div class='alert alert-primary' role='alert'><a href='"+url_redirect+"'> Redirecting please wait: "+url_redirect+"</a><div></div></center>")
                        return response    

                    checkouthash =  hashlib.sha256(str(str(request.session["payment_model"])+str(request.session["payment_pk"])).encode('utf-8')).hexdigest() 
                    checkouthash_cookie = request.COOKIES.get('checkouthash')
                    validation_cookie = request.COOKIES.get(request.POST['payment-csrfmiddlewaretoken'])
                    
                    record_count = 0

                    if request.session['payment_model'] == "application":
                        record_count = Application.objects.filter(pk=request.session['payment_pk']).count()
                    elif request.session['payment_model'] == "sanction_outcome":
                        record_count = SanctionOutcome.objects.filter(pk=request.session['payment_pk']).count() 

                    if checkouthash_cookie != checkouthash or checkouthash_cookie != validation_cookie or record_count == 0:                       
                        url_redirect = reverse("/")
                        response = HttpResponse("<script> window.location='"+url_redirect+"';</script> <center><div class='container'><div class='alert alert-primary' role='alert'><a href='"+url_redirect+"'> Redirecting please wait: "+url_redirect+"</a><div></div></center>")
                        return response  
            else:
                if request.path.startswith("/ledger-api/process-payment"):
                    url_redirect = reverse("/")
                    response = HttpResponse("<script> window.location='"+url_redirect+"';</script> <center><div class='container'><div class='alert alert-primary' role='alert'><a href='"+url_redirect+"'> Redirecting please wait: "+url_redirect+"</a><div></div></center>")
                    return response
                
            # force a redirect if in the checkout
            if ('payment_pk' not in request.session or 'payment_model' not in request.session) and CHECKOUT_PATH.match(request.path):
                url_redirect = reverse("/")
                response = HttpResponse("<script> window.location='"+url_redirect+"';</script> <center><div class='container'><div class='alert alert-primary' role='alert'><a href='"+url_redirect+"'> Redirecting please wait: "+url_redirect+"</a><div></div></center>")
                return response
                 
        return response