from django.conf import settings
from wildlifecompliance.helpers import (is_wildlife_compliance_officer,
is_compliance_management_user,prefer_compliance_management)
from wildlifecompliance.components.users.models import (ComplianceManagementUserPreferences)

def authorised_index(request):

    print(is_wildlife_compliance_officer(request),
        is_compliance_management_user(request))

    if is_wildlife_compliance_officer(request):
        return {"authorised_index":"app"}
    elif is_compliance_management_user(request):
        if not prefer_compliance_management(request):
            #if the user IS a compliance management user but NOT a wildlife compliance officer, change their preference
            preferences = ComplianceManagementUserPreferences.objects.get(email_user_id=request.user.id)
            preferences.prefer_compliance_management = True
            preferences.save()

        return {"authorised_index":"app"}
    else:
        return ""