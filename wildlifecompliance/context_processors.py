from django.conf import settings
from wildlifecompliance.helpers import (is_wildlife_compliance_officer,
is_compliance_management_user,prefer_compliance_management, is_internal_url)
from wildlifecompliance.components.users.models import (ComplianceManagementUserPreferences)
from ledger_api_client import utils as ledger_api_utils

def authorised_index(request):

    if is_wildlife_compliance_officer(request):
        if not is_compliance_management_user(request) and prefer_compliance_management(request):
            #if the user is NOT a compliance management user but IS a wildlife compliance officer, change their preference
            preferences = ComplianceManagementUserPreferences.objects.get(email_user_id=request.user.id)
            preferences.prefer_compliance_management = False
            preferences.save()
        return {"authorised_index":"app"}
    elif is_compliance_management_user(request):
        if not prefer_compliance_management(request):
            #if the user IS a compliance management user but NOT a wildlife compliance officer, change their preference
            preferences = ComplianceManagementUserPreferences.objects.get(email_user_id=request.user.id)
            preferences.prefer_compliance_management = True
            preferences.save()

        return {"authorised_index":"app"}
    elif not is_internal_url(request):
        return {"authorised_index":"app"}
    else:
        return ""
    
def wildlifecompliance_processor(request):

    web_url = request.META.get('HTTP_HOST', None)
    lt = ledger_api_utils.get_ledger_totals()

    #checkouthash = None
    #if 'payment_model' in request.session and 'payment_pk' in request.session:
    #    checkouthash =  hashlib.sha256(str(str(request.session["payment_model"])+str(request.session["payment_pk"])).encode('utf-8')).hexdigest()

    return {
        'public_url': web_url,
        'template_group': 'parkswildlifev2',
        'LEDGER_UI_URL': f'{settings.LEDGER_UI_URL}',
        'LEDGER_SYSTEM_ID': f'{settings.LEDGER_SYSTEM_ID}',
        'ledger_totals': lt,
        #'checkouthash' : checkouthash,
    }