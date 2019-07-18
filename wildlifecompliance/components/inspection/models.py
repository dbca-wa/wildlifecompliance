from __future__ import unicode_literals
import logging
from django.db import models
from django.contrib.gis.db import models
from django.contrib.postgres.fields.jsonb import JSONField
from django.db.models import Max
from django.utils.encoding import python_2_unicode_compatible
from ledger.accounts.models import EmailUser, RevisionedMixin
from ledger.licence.models import LicenceType
from wildlifecompliance.components.main.models import CommunicationsLogEntry, UserAction, Document
from wildlifecompliance.components.organisations.models import Organisation
from wildlifecompliance.components.main.models import CommunicationsLogEntry,\
    UserAction, Document, get_related_items
from wildlifecompliance.components.users.models import RegionDistrict, CompliancePermissionGroup

logger = logging.getLogger(__name__)

def update_inspection_comms_log_filename(instance, filename):
    return 'wildlifecompliance/compliance/{}/communications/{}/{}'.format(
        instance.log_entry.inspection.id, instance.id, filename)


class InspectionType(models.Model):
   description = models.CharField(max_length=255, null=True, blank=True)

   class Meta:
       app_label = 'wildlifecompliance'
       verbose_name = 'CM_InspectionType'
       verbose_name_plural = 'CM_InspectionTypes'

   def __str__(self):
       return self.description


class Inspection(RevisionedMixin):
    PARTY_CHOICES = (
            ('individual', 'individual'),
            ('organisation', 'organisation')
            )
    STATUS_CHOICES = (
            ('open', 'Open'),
            ('endorsement', 'Awaiting Endorsement'),
            ('sanction_outcome', 'Awaiting Sanction Outcomes'),
            ('closed', 'Closed')
            )

    title = models.CharField(max_length=200, blank=True, null=True)
    status = models.CharField(
            max_length=100,
            choices=STATUS_CHOICES,
            default='open'
            )

    details = models.TextField(blank=True, null=True)
    number = models.CharField(max_length=50, blank=True, null=True)
    planned_for_date = models.DateField(null=True)
    planned_for_time = models.TimeField(blank=True, null=True)
    party_inspected = models.CharField(
            max_length=30,
            choices=PARTY_CHOICES,
            default='individual'
            )
    assigned_to = models.ForeignKey(
        EmailUser, 
        related_name='inspection_assigned_to',
        null=True
        )
    allocated_group = models.ForeignKey(
        CompliancePermissionGroup,
        related_name='inspection_allocated_group', 
        null=True
        )
    inspection_team = models.ManyToManyField(
        EmailUser,
        related_name='inspection_team',
        blank=True
        )
    inspection_type = models.ForeignKey(
            InspectionType,
            related_name='inspection_type',
            null=True
            )

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_Inspection'
        verbose_name_plural = 'CM_Inspections'

    def __str__(self):
        return 'ID: {0}, Type: {1}, Title: {2}' \
            .format(self.id, self.title, self.title)
    
    # Prefix "IN" char to Inspection number.
    def save(self, *args, **kwargs):
        
        super(Inspection, self).save(*args,**kwargs)
        if self.number is None:
            new_number_id = 'IN{0:06d}'.format(self.pk)
            self.number = new_number_id
            self.save()
        
    def log_user_action(self, action, request):
        return InspectionUserAction.log_action(self, action, request.user)
    

class InspectionCommsLogDocument(Document):
    log_entry = models.ForeignKey(
        'InspectionCommsLogEntry',
        related_name='documents')
    _file = models.FileField(max_length=255, upload_to=update_inspection_comms_log_filename)

    class Meta:
        app_label = 'wildlifecompliance'


class InspectionCommsLogEntry(CommunicationsLogEntry):
    inspection = models.ForeignKey(Inspection, related_name='comms_logs')

    class Meta:
        app_label = 'wildlifecompliance'


class InspectionUserAction(UserAction):
    ACTION_SAVE_INSPECTION_ = "Save Inspection {}"

    class Meta:
        app_label = 'wildlifecompliance'
        ordering = ('-when',)

    @classmethod
    def log_action(cls, inspection, action, user):
        return cls.objects.create(
            inspection=inspection,
            who=user,
            what=str(action)
        )

    inspection = models.ForeignKey(Inspection, related_name='action_logs')
