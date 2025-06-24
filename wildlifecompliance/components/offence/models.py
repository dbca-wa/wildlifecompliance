import datetime

from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import post_save
from django.db.models import Q
from ledger_api_client.ledger_models import EmailUserRO as EmailUser
from wildlifecompliance.components.main.models import RevisionedMixin, SanitiseMixin
from wildlifecompliance.components.call_email.models import Location, CallEmail
from wildlifecompliance.components.legal_case.models import LegalCase
from wildlifecompliance.components.inspection.models import Inspection
from wildlifecompliance.components.main.models import Document, CommunicationsLogEntry, Region, District
from wildlifecompliance.components.main.related_item import can_close_record
from wildlifecompliance.components.section_regulation.models import SectionRegulation
from wildlifecompliance.components.main.models import ComplianceManagementSystemGroup
from wildlifecompliance.components.organisations.models import Organisation
from django_countries.fields import CountryField

from wildlifecompliance.components.main.utils import (
    get_first_name,
    get_last_name,
)

from django.conf import settings
from django.core.files.storage import FileSystemStorage
private_storage = FileSystemStorage(location=settings.BASE_DIR+"/private-media/", base_url='/private-media/')

class Offence(RevisionedMixin):
    WORKFLOW_CREATE = 'create'
    WORKFLOW_CLOSE = 'close'

    STATUS_DRAFT = 'draft'
    STATUS_OPEN = 'open'
    STATUS_CLOSED = 'closed'
    STATUS_PENDING_CLOSURE = 'pending_closure'
    STATUS_DISCARDED = 'discarded'

    EDITABLE_STATUSES = (STATUS_DRAFT, STATUS_OPEN,)
    FINAL_STATUSES = (STATUS_CLOSED, STATUS_DISCARDED,)

    STATUS_CHOICES = (
        (STATUS_DRAFT, 'Draft'),
        (STATUS_OPEN, 'Open'),
        (STATUS_PENDING_CLOSURE, 'Pending Closure'),
        (STATUS_CLOSED, 'Closed'),
        (STATUS_DISCARDED, 'Discarded'),
    )

    identifier = models.CharField(
        max_length=50,
        blank=True,
    )
    status = models.CharField(
        max_length=40,
        choices=STATUS_CHOICES,
        default='open',
    )
    location = models.ForeignKey(
        Location,
        null=True,
        blank=True,
        related_name="offence_location", on_delete=models.CASCADE
    )
    call_email = models.ForeignKey(
        CallEmail,
        null=True,
        blank=True,
        related_name='offence_call_eamil', on_delete=models.CASCADE
    )
    legal_case = models.ForeignKey(
        LegalCase,
        null=True,
        blank=True,
        related_name='offence_legal_case', on_delete=models.CASCADE
    )
    inspection = models.ForeignKey(
        Inspection,
        null=True,
        blank=True,
        related_name='offence_inspection', on_delete=models.CASCADE
    )
    lodgement_number = models.CharField(max_length=50, blank=True,)
    occurrence_from_to = models.BooleanField(default=False)
    occurrence_datetime_from = models.DateTimeField(null=True, blank=True)
    occurrence_datetime_to = models.DateTimeField(null=True, blank=True)
    alleged_offences = models.ManyToManyField(
        SectionRegulation,
        blank=True,
        through='AllegedOffence',
    )
    details = models.TextField(blank=True)
    assigned_to = models.ForeignKey(
        EmailUser,
        related_name='offence_assigned_to',
        null=True, on_delete=models.CASCADE
    )
    allocated_group = models.ForeignKey(
       ComplianceManagementSystemGroup,
       related_name='offence_allocated_group',
       null=True, on_delete=models.CASCADE
    )
    region = models.ForeignKey(Region, related_name='offence_region', null=True, on_delete=models.CASCADE)
    district = models.ForeignKey(District, related_name='offence_district', null=True, on_delete=models.CASCADE)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_Offence'
        verbose_name_plural = 'CM_Offences'

    def __str__(self):
        try:
            return 'ID: {}, Status: {}, Identifier: {}'.format(self.id, self.status, self.identifier.encode('utf-8'))
        except Exception as e:
            return 'ID: {}'.format(self.id)

    def save(self, *args, **kwargs):
        super(Offence, self).save(*args, **kwargs)
        if not self.lodgement_number:
            self.lodgement_number = 'OF{0:06d}'.format(self.pk)
            self.save()

    def log_user_action(self, action, request=None):
        if request:
            return OffenceUserAction.log_action(self, action, request.user)
        else:
            return OffenceUserAction.log_action(self, action)

    @property
    def get_related_items_identifier(self):
        #return '{}'.format(self.identifier)
        return self.lodgement_number

    @property
    def allowed_groups(self):
        if not self.allocated_group:
            return []
        groups = [self.allocated_group.id]
        if not settings.AUTH_GROUP_REGION_DISTRICT_LOCK_ENABLED:
            groups = groups + list(ComplianceManagementSystemGroup.objects.filter(name=self.allocated_group.name).values_list('id',flat=True))
        elif settings.SUPER_AUTH_GROUPS_ENABLED:
            queryset = ComplianceManagementSystemGroup.objects
            groups = groups + list(ComplianceManagementSystemGroup.objects.filter(
                (Q(name=self.allocated_group.name) & Q(region=None)) | 
                (Q(name=self.allocated_group.name) & Q(region=self.allocated_group.region) & Q(district=None))).values_list('id',flat=True))
        return list(set(groups))

    @staticmethod
    # Rewrite for Region District models
    def get_allocated_group(region_id, district_id):
        #region_district = RegionDistrict.objects.filter(id=regionDistrictId)

        # 2. Determine which permission(s) is going to be applied
        # compliance_content_type = ContentType.objects.get(model="compliancepermissiongroup")
        # codename = 'officer'
        # per_district = True

        # permissions = Permission.objects.filter(codename=codename, content_type_id=compliance_content_type.id)

        # 3. Find groups which has the permission(s) determined above in the regionDistrict.
        try:
            return ComplianceManagementSystemGroup.objects.get(name=settings.GROUP_OFFICER, region_id=region_id, district_id=district_id)
        except:
            return None

    @property
    # Rewrite for Region District models
    def regionDistrictId(self):
        return self.district.id if self.district else self.region.id

    @property
    def get_related_items_descriptor(self):
        #return '{}, {}'.format(self.identifier, self.details)
        return self.identifier

    def close(self, request=None):
        close_record, parents = can_close_record(self)
        if close_record:
            self.status = self.STATUS_CLOSED
            self.log_user_action(OffenceUserAction.ACTION_CLOSE.format(self.lodgement_number), request)
        else:
            self.status = self.STATUS_PENDING_CLOSURE
            self.log_user_action(OffenceUserAction.ACTION_PENDING_CLOSURE.format(self.lodgement_number), request)
        self.save()

    @property
    def offence_occurrence_datetime(self):
        if self.occurrence_from_to:
            return self.occurrence_datetime_to
        else:
            return self.occurrence_datetime_from


def perform_can_close_record(sender, instance, **kwargs):
    # Trigger the close() function of each parent entity of this offence
    if instance.status in (Offence.FINAL_STATUSES):
        close_record, parents = can_close_record(instance)
        for parent in parents:
            if parent.status == 'pending_closure':
                parent.close()

post_save.connect(perform_can_close_record, sender=Offence)


def update_offence_doc_filename(instance, filename):
    return 'wildlifecompliance/offence/{}/documents/{}'.format(
        instance.sanction_outcome.id, filename
    )


class OffenceDocument(Document):
    offence = models.ForeignKey(Offence, related_name='documents', on_delete=models.CASCADE)
    _file = models.FileField(max_length=255, upload_to=update_offence_doc_filename, storage=private_storage)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_OffenceDocument'
        verbose_name_plural = 'CM_OffenceDocuments'


class AllegedOffence(RevisionedMixin):
    offence = models.ForeignKey(Offence, null=False, on_delete=models.CASCADE)
    section_regulation = models.ForeignKey(SectionRegulation, null=False, on_delete=models.CASCADE)
    reason_for_removal = models.TextField(blank=True)
    removed = models.BooleanField(default=False)
    removed_by = models.ForeignKey(
        EmailUser,
        null=True,
        related_name='alleged_offence_removed_by', on_delete=models.CASCADE
    )

    def __str__(self):
        return self.section_regulation.__str__()

    def retrieve_penalty_amounts_by_date(self, date_of_issue):
        return self.section_regulation.retrieve_penalty_amounts_by_date(date_of_issue)

    @property
    def act(self):
        return self.section_regulation.act

    @property
    def dotag_offence_code(self):
        return self.section_regulation.dotag_offence_code

    @property
    def issue_due_date_window(self):
        return self.section_regulation.issue_due_date_window

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_AllegedOffence'
        verbose_name_plural = 'CM_AllegedOffences'


class ActiveOffenderManager(models.Manager):
    def get_queryset(self):
        return super(ActiveOffenderManager, self).get_queryset().filter(removed=False)


class Offender(SanitiseMixin):
    reason_for_removal = models.TextField(blank=True)
    removed = models.BooleanField(default=False)
    removed_by = models.ForeignKey(
        EmailUser,
        null=True,
        related_name='offender_removed_by', on_delete=models.CASCADE
    )

    email = models.EmailField(blank=True, null=True)
    first_name = models.CharField(max_length=128, blank=False, verbose_name='Given name(s)', null=True)
    last_name = models.CharField(max_length=128, blank=False, null=True)
    dob = models.DateField(auto_now=False, auto_now_add=False, null=True, blank=False, verbose_name="date of birth", help_text='')
    phone_number = models.CharField(max_length=50, null=True, blank=True, verbose_name="phone number", help_text='')
    mobile_number = models.CharField(max_length=50, null=True, blank=True, verbose_name="mobile number", help_text='')

    address_street = models.CharField('Street', max_length=255, null=True, blank=True)
    address_locality = models.CharField('Suburb / Town', max_length=255, null=True, blank=True)
    address_state = models.CharField(max_length=255, default='WA', null=True, blank=True)
    address_country = CountryField(default='AU', null=True, blank=True)
    address_postcode = models.CharField(max_length=10, null=True, blank=True)

    organisation_id = models.IntegerField(
        unique=True, verbose_name="Ledger Organisation ID", null=True
    )
    offence = models.ForeignKey(
        Offence,
        null=True,
        on_delete=models.SET_NULL
    )
    active_offenders = ActiveOffenderManager()
    objects = models.Manager()

    @property
    def get_related_items_identifier(self):
        return self.first_name + " " + self.last_name
    
    @property
    def get_related_items_descriptor(self):
        return self.first_name + " " + self.last_name

    @property
    def full_name(self):
        return "{} {}".format(self.first_name, self.last_name)

    @property
    def address(self):
        return "{} {} {} {} {}".format(self.address_street, self.address_locality, self.address_state, self.address_postcode, self.address_country)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_Offender'
        verbose_name_plural = 'CM_Offenders'

    def __str__(self):
        return 'First name: {}, Last name: {}'.format(self.first_name, self.last_name)
        

class OffenceUserAction(SanitiseMixin):
    ACTION_CLOSE = "Close offence: {}"
    ACTION_PENDING_CLOSURE = "Mark offence {} as pending closure"
    ACTION_CREATE = "Create Offence: {}"
    ACTION_UPDATE = "Update Offence {}"
    ACTION_REMOVE_ALLEGED_OFFENCE = "Remove alleged offence: {}, Reason: {}"
    ACTION_REMOVE_OFFENDER = "Remove offender: {}, Reason: {}"
    ACTION_RESTORE_ALLEGED_OFFENCE = "Restore alleged offence: {}"
    ACTION_RESTORE_OFFENDER = "Restore offender: {}"
    ACTION_ADD_WEAK_LINK = "Create manual link between {}: {} and {}: {}"
    ACTION_REMOVE_WEAK_LINK = "Remove manual link between {}: {} and {}: {}"

    who = models.ForeignKey(EmailUser, null=True, blank=True, on_delete=models.CASCADE)
    when = models.DateTimeField(null=False, blank=False, auto_now_add=True)
    what = models.TextField(blank=False)
    offence = models.ForeignKey(Offence, related_name='action_logs', on_delete=models.CASCADE)

    class Meta:
        app_label = 'wildlifecompliance'
        ordering = ('-when',)

    @classmethod
    def log_action(cls, obj, action, user=None):
        return cls.objects.create(
            offence=obj,
            who=user,
            what=str(action)
        )

#TODO does not appear to work/be in use (it should be)
class OffenceCommsLogDocument(Document):
    log_entry = models.ForeignKey('OffenceCommsLogEntry', related_name='documents', on_delete=models.CASCADE)
    _file = models.FileField(max_length=255, storage=private_storage)

    class Meta:
        app_label = 'wildlifecompliance'


class OffenceCommsLogEntry(CommunicationsLogEntry):
    offence = models.ForeignKey(Offence, related_name='comms_logs', on_delete=models.CASCADE)

    class Meta:
        app_label = 'wildlifecompliance'


import reversion
reversion.register(Offence, follow=['documents', 'allegedoffence_set', 'offender_set', 'action_logs', 'comms_logs', 'offence_sanction_outcomes', 'document_artifact_offence', 'offence_boe_roi', 'offence_pb_roi'])
reversion.register(OffenceDocument, follow=[])
reversion.register(AllegedOffence, follow=['sanction_outcome_alleged_committed_offences', 'allegedcommittedoffence_set'])
reversion.register(Offender, follow=['sanction_outcome_offender', 'document_artifact_offender', 'offender_boe_roi', 'offender_pb_roi'])
reversion.register(OffenceUserAction, follow=[])
reversion.register(OffenceCommsLogDocument, follow=[])
reversion.register(OffenceCommsLogEntry, follow=['documents'])

