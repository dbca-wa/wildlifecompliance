import logging

from django.http import Http404, HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
from django.views.generic.base import View, TemplateView
from django.conf import settings
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin

from datetime import datetime, timedelta

from wildlifecompliance.helpers import is_internal, prefer_compliance_management, in_dbca_domain, \
    is_compliance_internal_user, is_wildlifecompliance_admin, is_compliance_management_callemail_readonly_user, belongs_to, \
    is_compliance_management_approved_external_user, is_customer, is_wildlife_compliance_officer
from wildlifecompliance.forms import *
from wildlifecompliance.components.applications.models import Application,ApplicationSelectedActivity
from wildlifecompliance.components.call_email.models import CallEmail
from wildlifecompliance.components.returns.models import Return
from wildlifecompliance.components.licences.models import WildlifeLicence
from wildlifecompliance.components.organisations.models import Organisation, OrganisationContact
from wildlifecompliance.components.main import utils
from wildlifecompliance.exceptions import BindApplicationException
from django.core.management import call_command
from ledger_api_client.ledger_models import EmailUserRO as EmailUser
import os
import mimetypes
from django.contrib import messages
from django.db.models import Q
#from wildlifecompliance.components.users.models import CompliancePermissionGroup


logger = logging.getLogger(__name__)
# logger = logging

class ApplicationView(DetailView):
    model = Application
    template_name = 'wildlifecompliance/dash/index.html'


class CallEmailView(DetailView):
    model = CallEmail
    template_name = 'wildlifecompliance/dash/index.html'


class ExternalApplicationView(DetailView):
    model = Application
    template_name = 'wildlifecompliance/dash/index.html'


class ExternalReturnView(DetailView):
    model = Return
    template_name = 'wildlifecompliance/dash/index.html'


class InternalView(UserPassesTestMixin, TemplateView):
#class InternalView(TemplateView):
    template_name = 'wildlifecompliance/dash/index.html'

    def test_func(self):
        return is_internal(self.request) or is_compliance_management_approved_external_user(self.request)

    def get_context_data(self, **kwargs):
        context = super(InternalView, self).get_context_data(**kwargs)
        # context['dev'] = settings.DEV_STATIC
        # context['dev_url'] = settings.DEV_STATIC_URL
        # context['app_build_url'] = settings.DEV_APP_BUILD_URL
        #context['build_tag'] = settings.BUILD_TAG
        return context


class ExternalView(LoginRequiredMixin, TemplateView):
    template_name = 'wildlifecompliance/dash/index.html'

    def get_context_data(self, **kwargs):
        context = super(ExternalView, self).get_context_data(**kwargs)
        # context['dev'] = settings.DEV_STATIC
        # context['dev_url'] = settings.DEV_STATIC_URL
        # context['app_build_url'] = settings.DEV_APP_BUILD_URL
        #context['build_tag'] = settings.BUILD_TAG
        return context

class InfringementView(TemplateView):
    template_name = 'wildlifecompliance/infringement.html'

    def get_context_data(self, **kwargs):
        context = super(InfringementView, self).get_context_data(**kwargs)
        context['wc_pay_infr_url'] = settings.WC_PAY_INFR_URL
        return context


class WildlifeComplianceRoutingView(TemplateView):
    template_name = 'wildlifecompliance/index.html'

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            print('email: {}'.format(self.request.user.email))
            print("is_authenticated: True")
            print('is_superuser: {}'.format(self.request.user.is_superuser))
            print('is_dbca_domain: {}'.format(in_dbca_domain(self.request)))
            print('is_compliance_internal_user: {}'.format(is_compliance_internal_user(self.request)))
            print('is_wildlifecompliance_admin: {}'.format(is_wildlifecompliance_admin(self.request)))
            print('prefer compliance management: {}'.format(prefer_compliance_management(self.request)))
            #if (
            #        (is_internal(self.request) and prefer_compliance_management(self.request)) or
            #        is_compliance_management_approved_external_user(self.request)
            #        ):
            #    #return redirect('internal')
            #elif is_internal(self.request):
            #    #return redirect('internal')
            return redirect('external')
        kwargs['form'] = LoginForm
        return super(WildlifeComplianceRoutingView, self).get(*args, **kwargs)


@login_required(login_url='home')
def first_time(request):
    context = {}
    if request.method == 'POST':
        form = FirstTimeForm(request.POST)
        redirect_url = form.data['redirect_url']
        if not redirect_url:
            redirect_url = '/'
        if form.is_valid():
            # set user attributes
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.dob = form.cleaned_data['dob']
            request.user.save()
            return redirect(redirect_url)
        context['form'] = form
        context['redirect_url'] = redirect_url
        return render(request, 'wildlifecompliance/user_profile.html', context)
    # GET default
    if 'next' in request.GET:
        context['redirect_url'] = request.GET['next']
    else:
        context['redirect_url'] = '/'
    # context['dev'] = settings.DEV_STATIC
    # context['dev_url'] = settings.DEV_STATIC_URL
    # context['app_build_url'] = settings.DEV_APP_BUILD_URL
    #context['build_tag'] = settings.BUILD_TAG
    return render(request, 'wildlifecompliance/dash/index.html', context)


class HealthCheckView(TemplateView):
    """A basic template view not requiring auth, used for service monitoring.
    """
    template_name = 'wildlifecompliance/healthcheck.html'

    def get_context_data(self, **kwargs):
        context = super(HealthCheckView, self).get_context_data(**kwargs)
        context['page_title'] = 'Wildlife Licensing application status'
        context['status'] = 'HEALTHY'
        return context


class ManagementCommandsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'wildlifecompliance/mgt-commands.html'

    def test_func(self):
        return is_internal(self.request)

    def post(self, request):
        from wildlifecompliance.components.returns.services import (
            ReturnService)
        from wildlifecompliance.components.licences.services import (
            LicenceService)
        from wildlifecompliance.components.applications.services import (
            ApplicationService)

        data = {
            "prefer_compliance_management": prefer_compliance_management(request),
            "is_internal_login": is_internal(request),
            "is_compliance_internal_login": is_compliance_internal_user(request),
        }
        command_script = request.POST.get('script', None)
        if command_script:
            logger.info(
                'ManagementCommandsView(): running - {0}'.format(
                    command_script
                ))

            call_command(command_script)
            data[command_script] = 'true'

        return render(request, self.template_name, data)
    
    def get(self,request):
        data = {
            "prefer_compliance_management": prefer_compliance_management(request),
            "is_internal_login": is_internal(request),
            "is_compliance_internal_login": is_compliance_internal_user(request),
        }
        return render(request, self.template_name, data)

class SecureBaseView(View):
    '''
    A generic view that applies the securebase policy to a post request. 
    '''
    def post(self, request, *args, **kwargs):
        from wildlifecompliance.management.securebase_manager import SecurePipe
        
        securebase_view = SecurePipe(request)

        return securebase_view.get_http_response()
    

def is_authorised_to_access_application_document(request,document_id):
    if is_internal(request):
        return True
    elif is_customer(request):
        user = request.user
        user_orgs = [org.id for org in user.wildlifecompliance_organisations.all()]
        return Application.objects.filter(id=document_id).filter(
            Q(org_applicant_id__in=user_orgs) | 
            Q(proxy_applicant=user) | Q(submitter=user)).exists()
    
def is_authorised_to_access_licence_document(request,document_id):
    if is_internal(request):
        return True
    elif is_customer(request):
        asa_accepted = ApplicationSelectedActivity.objects.filter(
            processing_status=ApplicationSelectedActivity.PROCESSING_STATUS_ACCEPTED)
        user = request.user
        user_orgs = [org.id for org in user.wildlifecompliance_organisations.all()]
        return WildlifeLicence.objects.filter(id=document_id).filter(
                Q(current_application__org_applicant_id__in=user_orgs) |
                Q(current_application__proxy_applicant=user) |
                Q(current_application__submitter=user)
            ).filter(current_application__in=asa_accepted.values_list('application_id', flat=True)).exists()
    
def is_authorised_to_access_return_document(request,document_id):
    if is_internal(request):
        return True
    elif is_customer(request):
        user = request.user
        user_orgs = [
            org.id for org in user.wildlifecompliance_organisations.all()]
        user_licences = [wildlifelicence.id for wildlifelicence in WildlifeLicence.objects.filter(
            Q(current_application__org_applicant_id__in=user_orgs) |
            Q(current_application__proxy_applicant=user) |
            Q(current_application__submitter=user))]
        return Return.objects.filter(id=document_id).filter(Q(licence_id__in=user_licences)).exists()

def is_authorised_to_access_organisation_document(request,document_id):
    if is_internal(request):
        return True
    elif is_customer(request):
        user = request.user
        org_contacts = OrganisationContact.objects.filter(is_admin=True).filter(email=user.email)
        user_admin_orgs = [org.organisation.id for org in org_contacts]
        return Organisation.objects.filter(id=document_id).filter(id__in=user_admin_orgs).exists()

def get_file_path_id(check_str,file_path):
    file_name_path_split = file_path.split("/")
    #if the check_str is in the file path, the next value should be the id
    if check_str in file_name_path_split:
        id_index = file_name_path_split.index(check_str)+1
        if len(file_name_path_split) > id_index and file_name_path_split[id_index].isnumeric():
            return int(file_name_path_split[id_index])
        else:
            return False
    else:
        return False

def is_authorised_to_access_document(request):

    if is_wildlife_compliance_officer(request) or is_compliance_internal_user(request):
        return True
    elif request.user.is_authenticated:
        a_document_id = get_file_path_id("applications",request.path)
        if a_document_id:
            return is_authorised_to_access_application_document(request,a_document_id)
        
        l_document_id = get_file_path_id("licences",request.path)
        if l_document_id:
            return is_authorised_to_access_licence_document(request,l_document_id)
        
        r_document_id = get_file_path_id("returns",request.path)
        if r_document_id:
            return is_authorised_to_access_return_document(request,r_document_id)
        
        #for organisation requests, this will fail and they are stored in a request subdir and by date (which is fine for current use cases)
        o_document_id = get_file_path_id("organisations",request.path)
        if o_document_id:
            return is_authorised_to_access_organisation_document(request,a_document_id)
    else:
        return False

def getPrivateFile(request):

    if is_authorised_to_access_document(request):
        file_name_path =  request.path
        #norm path will convert any traversal or repeat / in to its normalised form
        full_file_path= os.path.normpath(settings.BASE_DIR+file_name_path) 
        #we then ensure the normalised path is within the BASE_DIR (and the file exists)
        if full_file_path.startswith(settings.BASE_DIR) and os.path.isfile(full_file_path):
            extension = file_name_path.split(".")[-1].lower()
            the_file = open(full_file_path, 'rb')
            the_data = the_file.read()
            the_file.close()
            if extension == 'msg':
                return HttpResponse(the_data, content_type="application/vnd.ms-outlook")
            if extension == 'eml':
                return HttpResponse(the_data, content_type="application/vnd.ms-outlook")
            if extension == 'heic':
                return HttpResponse(the_data, content_type="image/heic")
            return HttpResponse(the_data, content_type=mimetypes.types_map['.'+str(extension)])

    return HttpResponse()
