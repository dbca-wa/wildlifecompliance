import datetime

from dateutil.relativedelta import relativedelta
from django.db import transaction
from django.core.management.base import BaseCommand
from django.db.models import Q, Max

from django.utils import timezone
import logging

from wildlifecompliance import settings
#from wildlifecompliance.components.sanction_outcome.email import send_unpaid_infringements_file
#from wildlifecompliance.components.sanction_outcome.models import SanctionOutcome, SanctionOutcomeUserAction, \
#    UnpaidInfringementFile
#from wildlifecompliance.components.sanction_outcome.serializers import SanctionOutcomeCommsLogEntrySerializer
#from wildlifecompliance.components.sanction_outcome_due.models import SanctionOutcomeDueDate
#from wildlifecompliance.components.users.modelsk import CompliancePermissionGroup
from wildlifecompliance.helpers import DEBUG
#from wildlifecompliance.management.classes.unpaid_infringement_file import UnpaidInfringementFileHeader, \
 #   UnpaidInfringementFileTrailer
from wildlifecompliance.components.main.models import GlobalSettings
from wildlifecompliance.components.artifact.models import Artifact, DocumentArtifact, PhysicalArtifact

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send unpaid infringements file emails for infringements which have past payment due dates'

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                logger.info('Running command {}'.format(__name__))
                #today = timezone.localtime(timezone.now()).date()
                today = timezone.localtime(timezone.now())
                #today = datetime.date.today()
                #today = timezone.now()
                #print(today)

                # retrieve artifact disposal dates
                document_artifact_disposal_period_str = None
                physical_artifact_disposal_period_str = None
                document_artifact_disposal_period_list = GlobalSettings.objects.filter(key='document_object_disposal_period')
                if document_artifact_disposal_period_list:
                    document_artifact_disposal_period_str = document_artifact_disposal_period_list[0].value
                physical_artifact_disposal_period_list = GlobalSettings.objects.filter(key='physical_object_disposal_period')
                if physical_artifact_disposal_period_list:
                    physical_artifact_disposal_period_str = physical_artifact_disposal_period_list[0].value
                document_artifact_disposal_period_int = int(document_artifact_disposal_period_str)
                physical_artifact_disposal_period_int = int(physical_artifact_disposal_period_str)
                # generate datetime timedelta disposal periods
                document_artifact_disposal_period_delta = relativedelta(days=document_artifact_disposal_period_int)
                physical_artifact_disposal_period_delta = relativedelta(days=physical_artifact_disposal_period_int)

                document_artifact_disposal_date_cutoff = today - document_artifact_disposal_period_delta
                physical_artifact_disposal_date_cutoff = today - physical_artifact_disposal_period_delta

                # retrieve active DocumentArtifacts with created dates older than the disposal period
                # TEST: change to created_at__lt for PROD
                document_artifacts = DocumentArtifact.objects.filter(status='active', legal_cases__id=None, created_at__gt=document_artifact_disposal_date_cutoff)
                for document_artifact in document_artifacts:
                    print(document_artifact.created_at)
                    document_artifact.close()

                # retrieve active PhysicalArtifacts with created dates older than the disposal period
                # TEST: change to created_at__lt for PROD
                physical_artifacts = PhysicalArtifact.objects.filter(status='active', legal_cases__id=None, created_at__gt=physical_artifact_disposal_date_cutoff)
                for physical_artifact in physical_artifacts:
                    print(physical_artifact.created_at)
                    physical_artifact.close()

        except Exception as e:
            logger.error('Error command {}'.format(__name__))
            raise e


#def main():
#    print("main method")
#    #c = Command()
#    #c.handle()
#    today = timezone.localtime(timezone.now()).date()
#
#    # retrieve artifact disposal dates
#    document_artifact_disposal_period_str = GlobalSettings.objects.filter(key='document_object_disposal_period')
#    physical_artifact_disposal_period_str = GlobalSettings.objects.filter(key='physical_object_disposal_period')
#    # generate datetime timedelta disposal periods
#    document_artifact_disposal_period_delta = datetime.timedelta(days=int(document_artifact_disposal_period_str))
#    physical_artifact_disposal_period_delta = datetime.timedelta(days=int(physical_artifact_disposal_period_str))
#
#    document_artifact_disposal_date_cutoff = today - document_artifact_disposal_period_delta
#    physical_artifact_disposal_date_cutoff = today - physical_artifact_disposal_period_delta
#    print(document_artifact_disposal_date_cutoff)
#    print(physical_artifact_disposal_date_cutoff)
#
#    # retrieve active DocumentArtifacts with created dates older than the disposal period
#    document_artifacts = DocumentArtifact.objects.filter(status='active', created__gt=document_artifact_disposal_date_cutoff)
#    for doc in document_artifacts:
#        print(doc)
#
#
#if __name__ == "__main__":
#    main()
