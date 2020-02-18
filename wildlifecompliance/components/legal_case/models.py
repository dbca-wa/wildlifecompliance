from __future__ import unicode_literals
import logging
from django.db import models
from django.contrib.gis.db import models
from django.contrib.postgres.fields.jsonb import JSONField
from django.db.models import Max
from django.utils.encoding import python_2_unicode_compatible
from ledger.accounts.models import EmailUser, RevisionedMixin
from ledger.licence.models import LicenceType
from wildlifecompliance.components.organisations.models import Organisation
from wildlifecompliance.components.call_email.models import CallEmail, Location
#from wildlifecompliance.components.artifact.utils import build_legal_case_hierarchy
#from wildlifecompliance.components.artifact.utils import BriefOfEvidenceRecordOfInterview
from wildlifecompliance.components.main.models import (
        CommunicationsLogEntry,
        UserAction, 
        Document,
        )
from wildlifecompliance.components.main.related_item import can_close_legal_case
from wildlifecompliance.components.users.models import RegionDistrict, CompliancePermissionGroup
from django.core.exceptions import ValidationError
from treebeard.mp_tree import MP_Node

logger = logging.getLogger(__name__)


class LegalCasePriority(models.Model):
    case_priority = models.CharField(max_length=50)
    schema = JSONField(null=True)
    version = models.SmallIntegerField(default=1, blank=False, null=False)
    description = models.CharField(max_length=255, blank=True, null=True)
    replaced_by = models.ForeignKey(
        'self', on_delete=models.PROTECT, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    #approval_document = models.ForeignKey(
    #    'InspectionTypeApprovalDocument',
    #    related_name='inspection_type',
    #    null=True)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_CasePriority'
        verbose_name_plural = 'CM_CasePriorities'
        unique_together = ('case_priority', 'version')

    def __str__(self):
        return '{0}, v.{1}'.format(self.case_priority, self.version)


class CourtProceedings(models.Model):
    legal_case = models.OneToOneField(
        'LegalCase',
        null=True,
        blank=True,
        related_name="court_proceedings",
    )
    court_outcome_details = models.TextField(blank=True)

    class Meta:
        app_label = 'wildlifecompliance'


class LegalCase(RevisionedMixin):
    STATUS_OPEN = 'open'
    #STATUS_WITH_MANAGER = 'with_manager'
    #STATUS_REQUEST_AMENDMENT = 'request_amendment'
    STATUS_AWAIT_ENDORSEMENT = 'await_endorsement'
    STATUS_BRIEF_OF_EVIDENCE = 'brief_of_evidence'
    #STATUS_SANCTION_OUTCOME = 'sanction_outcome'
    STATUS_DISCARDED = 'discarded'
    STATUS_CLOSED = 'closed'
    STATUS_PENDING_CLOSURE = 'pending_closure'
    STATUS_CHOICES = (
            (STATUS_OPEN, 'Open'),
            #(STATUS_WITH_MANAGER, 'With Manager'),
            #(STATUS_REQUEST_AMENDMENT, 'Request Amendment'),
            (STATUS_AWAIT_ENDORSEMENT, 'Awaiting Endorsement'),
            #(STATUS_SANCTION_OUTCOME, 'Awaiting Sanction Outcomes'),
            (STATUS_DISCARDED, 'Discarded'),
            (STATUS_BRIEF_OF_EVIDENCE, 'Brief of Evidence'),
            (STATUS_CLOSED, 'Closed'),
            (STATUS_PENDING_CLOSURE, 'Pending Closure')
            )

    title = models.CharField(max_length=200, blank=True, null=True)
    status = models.CharField(
            max_length=100,
            choices=STATUS_CHOICES,
            default='open'
            )
    details = models.TextField(blank=True, null=True)
    number = models.CharField(max_length=50, blank=True, null=True)
    case_created_date = models.DateField(null=True)
    case_created_time = models.TimeField(blank=True, null=True)
    call_email = models.ForeignKey(
        CallEmail, 
        related_name='legal_case_call_email',
        null=True
        )
    assigned_to = models.ForeignKey(
        EmailUser, 
        related_name='legal_case_assigned_to',
        null=True
        )
    allocated_group = models.ForeignKey(
        CompliancePermissionGroup,
        related_name='legal_case_allocated_group', 
        null=True
        )
    region = models.ForeignKey(
        RegionDistrict, 
        related_name='legal_case_region', 
        null=True
    )
    district = models.ForeignKey(
        RegionDistrict, 
        related_name='legal_case_district', 
        null=True
    )
    legal_case_priority = models.ForeignKey(
            LegalCasePriority,
            null=True
            )
    associated_persons = models.ManyToManyField(
            EmailUser,
            related_name='legal_case_associated_persons',
            )

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_LegalCase'
        verbose_name_plural = 'CM_LegalCases'

    def __str__(self):
        return 'ID: {}, Title: {}'.format(self.number, self.title)

    # Prefix "CS" char to LegalCase number.
    def save(self, *args, **kwargs):
        super(LegalCase, self).save(*args,**kwargs)

        if self.number is None:
            new_number_id = 'CS{0:06d}'.format(self.pk)
            self.number = new_number_id
            self.save()

        if not hasattr(self, 'court_proceedings'):
            cp = CourtProceedings.objects.create(legal_case=self)
            cp.save()

    def log_user_action(self, action, request):
        return LegalCaseUserAction.log_action(self, action, request.user)
    
    @property
    def get_related_items_identifier(self):
        return self.number

    @property
    def get_related_items_descriptor(self):
        #return '{0}, {1}'.format(self.title, self.details)
        return self.title

    #def send_to_manager(self, request):
    #    self.status = self.STATUS_AWAIT_ENDORSEMENT
    #    self.log_user_action(
    #        InspectionUserAction.ACTION_SEND_TO_MANAGER.format(self.number), 
    #        request)
    #    self.save()

    def close(self, request):
        close_record, parents = can_close_legal_case(self, request)
        if close_record:
            self.status = self.STATUS_CLOSED
            self.log_user_action(
                    LegalCaseUserAction.ACTION_CLOSE.format(self.number),
                    request)
        else:
            self.status = self.STATUS_PENDING_CLOSURE
            self.log_user_action(
                    LegalCaseUserAction.ACTION_PENDING_CLOSURE.format(self.number), 
                    request)
        self.save()
        # Call close() on any parent with pending_closure status
        if parents and self.status == 'closed':
            for parent in parents:
                if parent.status == 'pending_closure':
                    parent.close(request)

    def generate_brief_of_evidence(self, request):
        print("generate brief of evidence")
        self.assigned_to = None
        self.status = self.STATUS_BRIEF_OF_EVIDENCE
        self.log_user_action(
            LegalCaseUserAction.ACTION_GENERATE_BRIEF_OF_EVIDENCE.format(self.number), 
            request)
        # set allocated group to 
        #self.allocated_group
        self.save()


class BriefOfEvidence(models.Model):
    legal_case = models.OneToOneField(
            LegalCase,
            null=True,
            blank=True,
            related_name="brief_of_evidence",
            )
    statement_of_facts = models.TextField(blank=True, null=True)
    victim_impact_statement_taken = models.BooleanField(default=False)
    statements_pending = models.BooleanField(default=False)
    vulnerable_hostile_witnesses = models.BooleanField(default=False)
    witness_refusing_statement = models.BooleanField(default=False)
    problems_needs_prosecution_witnesses = models.BooleanField(default=False)
    accused_bad_character = models.BooleanField(default=False)
    further_persons_interviews_pending = models.BooleanField(default=False)
    other_interviews = models.BooleanField(default=False)
    relevant_persons_pending_charges = models.BooleanField(default=False)
    other_persons_receiving_sanction_outcome = models.BooleanField(default=False)
    local_public_interest = models.BooleanField(default=False)
    applications_orders_requests = models.BooleanField(default=False)
    applications_orders_required = models.BooleanField(default=False)
    other_legal_matters = models.BooleanField(default=False)

    victim_impact_statement_taken_details = models.TextField(blank=True, null=True)
    statements_pending_details = models.TextField(blank=True, null=True)
    vulnerable_hostile_witnesses_details = models.TextField(blank=True, null=True)
    witness_refusing_statement_details = models.TextField(blank=True, null=True)
    problems_needs_prosecution_witnesses_details = models.TextField(blank=True, null=True)
    accused_bad_character_details = models.TextField(blank=True, null=True)
    further_persons_interviews_pending_details = models.TextField(blank=True, null=True)
    other_interviews_details = models.TextField(blank=True, null=True)
    relevant_persons_pending_charges_details = models.TextField(blank=True, null=True)
    other_persons_receiving_sanction_outcome_details = models.TextField(blank=True, null=True)
    local_public_interest_details = models.TextField(blank=True, null=True)
    applications_orders_requests_details = models.TextField(blank=True, null=True)
    applications_orders_required_details = models.TextField(blank=True, null=True)
    other_legal_matters_details = models.TextField(blank=True, null=True)

    class Meta:
        app_label = 'wildlifecompliance'


class ProsecutionBrief(models.Model):
    legal_case = models.OneToOneField(
            LegalCase,
            null=True,
            blank=True,
            related_name="prosecution_brief",
            )
    statement_of_facts = models.TextField(blank=True, null=True)
    victim_impact_statement_taken = models.BooleanField(default=False)
    statements_pending = models.BooleanField(default=False)
    vulnerable_hostile_witnesses = models.BooleanField(default=False)
    witness_refusing_statement = models.BooleanField(default=False)
    problems_needs_prosecution_witnesses = models.BooleanField(default=False)
    accused_bad_character = models.BooleanField(default=False)
    further_persons_interviews_pending = models.BooleanField(default=False)
    other_interviews = models.BooleanField(default=False)
    relevant_persons_pending_charges = models.BooleanField(default=False)
    other_persons_receiving_sanction_outcome = models.BooleanField(default=False)
    local_public_interest = models.BooleanField(default=False)
    applications_orders_requests = models.BooleanField(default=False)
    applications_orders_required = models.BooleanField(default=False)
    other_legal_matters = models.BooleanField(default=False)

    victim_impact_statement_taken_details = models.TextField(blank=True, null=True)
    statements_pending_details = models.TextField(blank=True, null=True)
    vulnerable_hostile_witnesses_details = models.TextField(blank=True, null=True)
    witness_refusing_statement_details = models.TextField(blank=True, null=True)
    problems_needs_prosecution_witnesses_details = models.TextField(blank=True, null=True)
    accused_bad_character_details = models.TextField(blank=True, null=True)
    further_persons_interviews_pending_details = models.TextField(blank=True, null=True)
    other_interviews_details = models.TextField(blank=True, null=True)
    relevant_persons_pending_charges_details = models.TextField(blank=True, null=True)
    other_persons_receiving_sanction_outcome_details = models.TextField(blank=True, null=True)
    local_public_interest_details = models.TextField(blank=True, null=True)
    applications_orders_requests_details = models.TextField(blank=True, null=True)
    applications_orders_required_details = models.TextField(blank=True, null=True)
    other_legal_matters_details = models.TextField(blank=True, null=True)

    class Meta:
        app_label = 'wildlifecompliance'


class CourtProceedingsJournalEntryManager(models.Manager):
    def create_journal_entry(self, court_proceedings_id, user_id):
        max_row_num_dict = CourtProceedingsJournalEntry.objects.filter(court_proceedings_id=court_proceedings_id).aggregate(Max('row_num'))
        # initial value for new LegalCase
        row_num = 1
        # increment initial value if other entries exist for LegalCase
        if max_row_num_dict.get('row_num__max'):
            max_row_num = int(max_row_num_dict.get('row_num__max'))
            row_num = max_row_num + 1
        journal_entry = self.create(row_num=row_num, court_proceedings_id=court_proceedings_id, user_id=user_id)

        return journal_entry


class CourtProceedingsJournalEntry(RevisionedMixin):
    court_proceedings = models.ForeignKey(CourtProceedings, related_name='journal_entries')
    #person = models.ManyToManyField(LegalCasePerson, related_name='journal_entry_person')
    date_modified = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(EmailUser, related_name='journal_entry_user')
    description = models.TextField(blank=True)
    row_num = models.SmallIntegerField(blank=False, null=False)
    deleted = models.BooleanField(default=False)
    objects = CourtProceedingsJournalEntryManager()

    class Meta:
        app_label = 'wildlifecompliance'
        unique_together = ('court_proceedings', 'row_num')

    #def __str__(self):
    #    return "Number:{}, User:{}, Description:{}".format(
    #            self.number(),
    #            self.user,
    #            self.description)

   # def legal_case_persons(self):
   #     persons = self.legal_case.legal_case_person.all()
   #     return persons

    def number(self):
        #return self.court_proceedings.number + '-' + str(self.row_num)
        number = ''
        if self.court_proceedings.legal_case:
            number = self.court_proceedings.legal_case.number + '-' + str(self.row_num)
        return number

    def delete_entry(self):
        is_deleted = False
        if not self.deleted:
            self.deleted = True
            is_deleted = True
        return is_deleted

    def reinstate_entry(self):
        is_reinstated = False
        if self.deleted:
            self.deleted = False
            is_reinstated = True
        return is_reinstated

class LegalCasePerson(EmailUser):
    legal_case = models.ForeignKey(LegalCase, related_name='legal_case_person')

    class Meta:
        app_label = 'wildlifecompliance'

    def __str__(self):
        return "id:{}, legal_case_id:{}".format(
                self.id,
                self.legal_case_id,
                )

class LegalCaseRunningSheetEntryManager(models.Manager):
    def create_running_sheet_entry(self, legal_case_id, user_id):
        max_row_num_dict = LegalCaseRunningSheetEntry.objects.filter(legal_case_id=legal_case_id).aggregate(Max('row_num'))
        # initial value for new LegalCase
        row_num = 1
        # increment initial value if other entries exist for LegalCase
        if max_row_num_dict.get('row_num__max'):
            max_row_num = int(max_row_num_dict.get('row_num__max'))
            row_num = max_row_num + 1
        running_sheet_entry = self.create(row_num=row_num, legal_case_id=legal_case_id, user_id=user_id)

        return running_sheet_entry


class LegalCaseRunningSheetEntry(RevisionedMixin):
    legal_case = models.ForeignKey(LegalCase, related_name='running_sheet_entries')
    # TODO: person fk req?  Url links in description instead
    person = models.ManyToManyField(LegalCasePerson, related_name='running_sheet_entry_person')
    #number = models.CharField(max_length=50, blank=True)
    #date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(EmailUser, related_name='running_sheet_entry_user')
    #description = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    row_num = models.SmallIntegerField(blank=False, null=False)
    deleted = models.BooleanField(default=False)
    objects = LegalCaseRunningSheetEntryManager()

    class Meta:
        app_label = 'wildlifecompliance'
        unique_together = ('legal_case', 'row_num')

    #def save(self, *args, **kwargs):
    #    super(LegalCaseRunningSheetEntry, self).save(*args,**kwargs)
    #    if self.row_num is None:
    #        # TODO: replace with max fn
    #        #new_number_id = self.legal_case.number + str(self.pk)
    #        #max_row_num = LegalCaseRunningSheetEntry.objects.all().aggregate(Max('row_num'))
    #        max_row_num_dict = LegalCaseRunningSheetEntry.objects.filter(legal_case=self.legal_case).aggregate(Max('row_num'))
    #        max_row_num = int(max_row_num_dict['row_num__max'])
    #        
    #        self.row_num = max_row_num + 1
    #        self.save()

    def __str__(self):
        return "Number:{}, User:{}, Description:{}".format(
                self.number(),
                self.user,
                self.description)

    def legal_case_persons(self):
        persons = self.legal_case.legal_case_person.all()
        return persons

    def number(self):
        return self.legal_case.number + '-' + str(self.row_num)

    def delete_entry(self):
        is_deleted = False
        if not self.deleted:
            self.deleted = True
            is_deleted = True
        return is_deleted

    def reinstate_entry(self):
        is_reinstated = False
        if self.deleted:
            self.deleted = False
            is_reinstated = True
        return is_reinstated


class LegalCaseCommsLogEntry(CommunicationsLogEntry):
    legal_case = models.ForeignKey(LegalCase, related_name='comms_logs')

    class Meta:
        app_label = 'wildlifecompliance'


class LegalCaseCommsLogDocument(Document):
    log_entry = models.ForeignKey(
        LegalCaseCommsLogEntry,
        related_name='documents')
    _file = models.FileField(max_length=255)

    class Meta:
        app_label = 'wildlifecompliance'


class LegalCaseUserAction(UserAction):
    ACTION_CREATE_LEGAL_CASE = "Create Case {}"
    ACTION_SAVE_LEGAL_CASE = "Save Case {}"
    ACTION_GENERATE_BRIEF_OF_EVIDENCE = "Generate Brief of Evidence for Case {}"
    #ACTION_OFFENCE = "Create Offence {}"
    #ACTION_SANCTION_OUTCOME = "Create Sanction Outcome {}"
    #ACTION_SEND_TO_MANAGER = "Send Inspection {} to Manager"
    ACTION_CLOSE = "Close Legal Case {}"
    ACTION_PENDING_CLOSURE = "Mark Inspection {} as pending closure"
    #ACTION_REQUEST_AMENDMENT = "Request amendment for {}"
    #ACTION_ENDORSEMENT = "Inspection {} has been endorsed by {}"
    ACTION_ADD_WEAK_LINK = "Create manual link between {}: {} and {}: {}"
    ACTION_REMOVE_WEAK_LINK = "Remove manual link between {}: {} and {}: {}"
    #ACTION_MAKE_TEAM_LEAD = "Make {} team lead"
    #ACTION_ADD_TEAM_MEMBER = "Add {} to team"
    #ACTION_REMOVE_TEAM_MEMBER = "Remove {} from team"
    #ACTION_UPLOAD_INSPECTION_REPORT = "Upload Inspection Report '{}'"
    #ACTION_CHANGE_INDIVIDUAL_INSPECTED = "Change individual inspected from {} to {}"
    #ACTION_CHANGE_ORGANISATION_INSPECTED = "Change organisation inspected from {} to {}"

    class Meta:
        app_label = 'wildlifecompliance'
        ordering = ('-when',)

    @classmethod
    def log_action(cls, legal_case, action, user):
        return cls.objects.create(
            legal_case=legal_case,
            who=user,
            what=str(action)
        )

    legal_case = models.ForeignKey(LegalCase, related_name='action_logs')


class LegalCaseDocument(Document):
    legal_case = models.ForeignKey(LegalCase, related_name='documents')
    _file = models.FileField(max_length=255)
    input_name = models.CharField(max_length=255, blank=True, null=True)
    # after initial submit prevent document from being deleted
    can_delete = models.BooleanField(default=True)
    version_comment = models.CharField(max_length=255, blank=True, null=True)

    def delete(self):
        if self.can_delete:
            return super(LegalCaseDocument, self).delete()
        #logger.info(
         #   'Cannot delete existing document object after application has been submitted (including document submitted before\
          #  application pushback to status Draft): {}'.format(
           #     self.name)
        #)

    class Meta:
        app_label = 'wildlifecompliance'


def update_court_outcome_doc_filename(instance, filename):
    return 'wildlifecompliance/legal_case/{}/court_outcome_documents/{}'.format(instance.legal_case.id, filename)


class CourtOutcomeDocument(Document):
    court_proceedings = models.ForeignKey(CourtProceedings, related_name='court_outcome_documents')
    _file = models.FileField(max_length=255, upload_to=update_court_outcome_doc_filename)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_CourtOutcomeDocument'
        verbose_name_plural = 'CM_CourtOutcomeDocuments'


class CourtDate(models.Model):
    court_proceedings = models.ForeignKey(CourtProceedings, related_name='court_dates')
    court_datetime = models.DateTimeField(blank=True, null=True,)
    comments = models.TextField(blank=True)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_CourtDate'
        verbose_name_plural = 'CM_CourtDates'


import reversion
reversion.register(LegalCaseRunningSheetEntry, follow=['user'])
reversion.register(CourtProceedingsJournalEntry, follow=['user'])
reversion.register(LegalCase)
reversion.register(EmailUser)