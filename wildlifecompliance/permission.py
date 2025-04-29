from wildlifecompliance.components.organisations.models import Organisation
from wildlifecompliance.helpers import is_wildlife_compliance_officer

def organisation_permissions(request, org_id):
    user = request.user
    if is_wildlife_compliance_officer(request):
        organisation_qs = Organisation.objects.filter(organisation_id=org_id)
        return organisation_qs.exists()
    elif user.is_authenticated:
        organisation_qs = user.wildlifecompliance_organisations.filter(organisation_id=org_id)
        if organisation_qs.exists():
            organisation = organisation_qs.last()
            return organisation.can_user_edit(user.email)

    return True