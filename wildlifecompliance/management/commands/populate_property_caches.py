from django.core.management.base import BaseCommand
import logging
from django.db.models import Q
from wildlifecompliance.components.applications.models import Application

logger = logging.getLogger('cron_tasks')
cron_email = logging.getLogger('cron_email')

class Command(BaseCommand):

    """Obtaining certain ledger values can take too long under circumstances. 
    The property_cache of certain records are populated with these values to compensate for that. 
    This management command script populate records before property_cache change were made, or any that might be missing values for any other reason."""

    def handle(self, *args, **options):

        #applications
        #filter by missing property cache values
        applications = Application.objects.filter(
            Q(
                ~Q(org_applicant=None) & 
                Q(property_cache__organisation_name__isnull=True) #has org applicant set, but no org name property
            ) |
            Q(
                Q(org_applicant=None) & 
                Q(
                    Q(property_cache__proxy_applicant_first_name__isnull=True)|
                    Q(property_cache__proxy_applicant_last_name__isnull=True)
                ) #has no org applicant set, but proxy applicant property
            )
        )
        #populate
        for application in applications:
            application.update_property_cache()

        #licences
        #filter by missing property cache values
        #populate