from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.contrib.postgres.fields.jsonb import JSONField
from django.db.models import Max
from django.db.models import Q
from django.forms.models import model_to_dict
import json
import reversion
from ckeditor.fields import RichTextField

from ledger.licence.models import LicenceType

from wildlifecompliance.components.inspection.models import Inspection

from wildlifecompliance.components.main.models import (
    CommunicationsLogEntry,
    UserAction,
    Document
)


def update_licence_doc_filename(instance, filename):
    return 'wildlifecompliance/licences/{}/documents/{}'.format(
        instance.id, filename)


class LicenceDocument(Document):
    _file = models.FileField(upload_to=update_licence_doc_filename)

    class Meta:
        app_label = 'wildlifecompliance'


class LicencePurpose(models.Model):
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=30, default='')
    code = models.CharField(max_length=4, default='')
    schema = JSONField(default=list)
    base_application_fee = models.DecimalField(
        max_digits=8, decimal_places=2, default='0')
    base_licence_fee = models.DecimalField(
        max_digits=8, decimal_places=2, default='0')
    renewal_application_fee = models.DecimalField(
        max_digits=8, decimal_places=2, default='0')
    amendment_application_fee = models.DecimalField(
        max_digits=8, decimal_places=2, default='0')
    minimum_age = models.SmallIntegerField(default=18, blank=False, null=False)
    regulation = models.CharField(max_length=100)
    fields = JSONField(default=list)
    licence_category = models.ForeignKey(
        'LicenceCategory',
        blank=True,
        null=True
    )
    licence_activity = models.ForeignKey(
        'LicenceActivity',
        blank=True,
        null=True
    )
    apply_multiple = models.BooleanField(
        default=False,
        help_text='If ticked, the licenced Purpose can have multiple periods.')
    oracle_account_code = models.CharField(max_length=100, default='')
    not_renewable = models.BooleanField(
        default=False,
        help_text='If ticked, the licenced Purpose can not be renewed.')

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'Licence purpose'
        verbose_name_plural = 'Licence purposes'

    def __str__(self):
        return self.name

    @staticmethod
    def get_first_record(activity_name):
        # Use filter -> first() in case of records with duplicate names
        # (e.g. "Bioprospecting licence")
        return LicencePurpose.objects.filter(name=activity_name).first()

    @property
    def get_group_species_list(self):
        """
        List of species identifiers for questions associated with this licence
        purpose at a group level.
        """
        # SPECIES = ApplicationFormDataRecord.COMPONENT_TYPE_SELECT_SPECIES
        SPECIES = 'species'
        species_list = []

        try:
            for section in self.schema:
                for group in section['children']:
                    for field in group['children']:
                        if field['type'] == SPECIES:
                            field['component_attribute'] = \
                                self.get_species_options(field[SPECIES])
                            species_list += field[SPECIES]

        except KeyError:
            pass
        except Exception:
            pass
        return species_list

    @property
    def get_section_species_list(self):
        """
        List of species identifiers for questions associated with this licence
        purpose at a section level.
        """
        # SPECIES = ApplicationFormDataRecord.COMPONENT_TYPE_SELECT_SPECIES
        SPECIES = 'species'
        species_list = []

        try:
            for section in self.schema:
                for field in section['children']:
                    if field['type'] == SPECIES:
                        field['component_attribute'] = \
                            self.get_species_options(field[SPECIES])
                        species_list += field[SPECIES]

        except KeyError:
            pass
        except Exception:
            pass
        return species_list

    @property
    def get_species_list(self):
        SPECIES = 'species'
        children_keys = [
            'children',
            'header',
            'expander',
            'conditions',
        ]
        species_list = []

        def species_check(collection):
            _species_list = []
            try:
                for field in collection:
                    if field['type'] == SPECIES:
                        field['component_attribute'] = \
                            self.get_species_options(field[SPECIES])
                        _species_list += field[SPECIES]
                    for children_key in children_keys:
                        if children_key in field:
                            _species_list += species_check(
                                field[children_key])

            except KeyError:
                pass
            except Exception:
                pass

            return _species_list

        try:
            for section in self.schema:
                if section['type'] == SPECIES:
                    section['component_attribute'] = \
                        self.get_species_options(section[SPECIES])
                    species_list += section[SPECIES]
                for children_key in children_keys:
                    if children_key in section:
                        species_list += species_check(section[children_key])

        except KeyError:
            pass
        except Exception:
            pass
        return species_list

    def get_species_options(self, species_list):
        """
        Builds a list of drop-down options for Licence Species.
        """
        options = []
        for specie in species_list:
            details = LicenceSpecies.objects.values('data').get(
                specie_id=specie)
            option = {
                'value': details['data'][0][LicenceSpecies.SPECIE_NAME_ID],
                'label': details['data'][0][LicenceSpecies.SPECIE_NAME]}

            options.append(option)

        if not species_list:
            for details in LicenceSpecies.objects.values('data').all():
                option = {
                    'value': details['data'][0][LicenceSpecies.SPECIE_NAME_ID],
                    'label': details['data'][0][LicenceSpecies.SPECIE_NAME]}

                options.append(option)
                species_list.append(option['value'])

        return options

    def to_json(self):
        _list = []
        for i in self.purpose_species.all():
            _list.append(dict(model_to_dict(i)))
        return json.dumps(_list)


class PurposeSpecies(models.Model):
    licence_purpose = models.ForeignKey(LicencePurpose, related_name='purpose_species')
    order = models.IntegerField(default=1)
    header = models.CharField(max_length=255)
    #details = models.TextField()
    details = RichTextField(config_name='pdf_config')
    species = models.NullBooleanField()
    is_additional_info = models.BooleanField(default=False)

    class Meta:
        ordering = ['order', 'header']
        app_label = 'wildlifecompliance'
        verbose_name = 'Purpose Species'
        verbose_name_plural = 'Purpose Species'

    def __str__(self):
        return '{} - {}'.format(self.licence_purpose, self.header)

    def to_json(self):
        dict_obj=model_to_dict(self)
        return json.dumps(dict_obj)


class LicenceActivity(models.Model):
    name = models.CharField(max_length=100)
    licence_category = models.ForeignKey(
        'LicenceCategory',
        blank=True,
        null=True
    )
    purpose = models.ManyToManyField(
        LicencePurpose,
        blank=True,
        through='DefaultPurpose',
        related_name='wildlifecompliance_activity')
    short_name = models.CharField(max_length=30, default='')
    not_for_organisation = models.BooleanField(
        default=False,
        help_text='If ticked, this licenced activity will not be available for applications on behalf of an organisation.')
    schema = JSONField(default=list)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'Licenced activity'
        verbose_name_plural = 'Licenced activities'

    def __str__(self):
        return self.name


# #LicenceType
class LicenceCategory(LicenceType):
    activity = models.ManyToManyField(
        LicenceActivity,
        blank=True,
        through='DefaultActivity',
        related_name='wildlifecompliance_activities')

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'Licence category'
        verbose_name_plural = 'Licence categories'

    @property
    # override LicenceType display_name to display name first instead of
    # short_name
    def display_name(self):
        result = self.name or self.short_name
        if self.replaced_by is None:
            return result
        else:
            return '{} (V{})'.format(result, self.version)

    def get_activities(self):
        '''
        Getter for activities associated with category.

        NOTE: activity attribute not working correctly.
        '''
        _activities = LicenceActivity.objects.filter(
            licence_category_id=self.id
        )
        return _activities


class LicenceSpecies(models.Model):
    """
    Model representation of a verified specie information that can be applied
    to a licence.
    """
    SPECIE_NAME = 'vernacular_names'    # common name applied from data.
    SPECIE_NAME_ID = 'name_id'          # identifer applied from data.

    specie_id = models.IntegerField(unique=True)
    verify_date = models.DateTimeField(auto_now=True)
    verify_id = models.CharField(max_length=256, null=True, blank=True)
    verify_token = models.CharField(max_length=256, null=True, blank=True)
    data = JSONField(default=list)

    class Meta:
        ordering = ['specie_id']
        app_label = 'wildlifecompliance'
        verbose_name = 'Licence species'
        verbose_name_plural = 'Licence species'

    def __str__(self):
        return '{0} SPECIE_ID: {1}'.format(self.verify_date, self.specie_id)


class DefaultActivity(models.Model):
    activity = models.ForeignKey(LicenceActivity)
    licence_category = models.ForeignKey(LicenceCategory)

    class Meta:
        unique_together = (('licence_category', 'activity'))
        app_label = 'wildlifecompliance'
        verbose_name = 'Licenced category - licenced activity mapping'
        verbose_name_plural = 'Licenced category - licenced activity mappings'

    def __str__(self):
        return '{} - {}'.format(self.licence_category, self.activity)


class DefaultPurpose(models.Model):
    purpose = models.ForeignKey(LicencePurpose)
    activity = models.ForeignKey(LicenceActivity)

    class Meta:
        unique_together = (('activity', 'purpose'))
        app_label = 'wildlifecompliance'
        verbose_name = 'Licenced activity - purpose mapping'
        verbose_name_plural = 'Licenced activity - purpose mappings'

    def __str__(self):
        return '{} - {}'.format(self.activity, self.purpose)


class WildlifeLicence(models.Model):

    ACTIVITY_PURPOSE_ACTION_REACTIVATE_RENEW = 'reactivate_renew'
    ACTIVITY_PURPOSE_ACTION_SURRENDER = 'surrender'
    ACTIVITY_PURPOSE_ACTION_CANCEL = 'cancel'
    ACTIVITY_PURPOSE_ACTION_SUSPEND = 'suspend'
    ACTIVITY_PURPOSE_ACTION_REINSTATE = 'reinstate'
    ACTIVITY_PURPOSE_ACTION_REISSUE = 'reissue'

    licence_document = models.ForeignKey(
        LicenceDocument,
        blank=True,
        null=True,
        related_name='licence_document')
    replaced_by = models.ForeignKey('self', blank=True, null=True)
    extracted_fields = JSONField(blank=True, null=True)
    licence_number = models.CharField(max_length=64, blank=True, null=True)
    licence_sequence = models.IntegerField(blank=True, default=1)
    licence_category = models.ForeignKey(LicenceCategory)
    current_application = models.ForeignKey('wildlifecompliance.Application')
    property_cache = JSONField(null=True, blank=True, default={})

    class Meta:
        unique_together = (
            ('licence_number',
             'licence_sequence',
             'licence_category'))
        app_label = 'wildlifecompliance'

    def __str__(self):
        return '{} {}-{}'.format(self.licence_category, self.licence_number, self.licence_sequence)

    def save(self, *args, **kwargs):
        self.update_property_cache(False)
        super(WildlifeLicence, self).save(*args, **kwargs)
        if not self.licence_number:
            self.licence_number = 'L{0:06d}'.format(
                self.next_licence_number_id)
            self.save()

    def get_property_cache(self):
        '''
        Get properties which were previously resolved.
        '''
        if len(self.property_cache) == 0:
            self.update_property_cache()

        return self.property_cache

    def update_property_cache(self, save=True):
        '''
        Refresh cached properties with updated properties.
        '''
        # self.property_cache['payment_status'] = self.payment_status

        if save is True:
            self.save()

        return self.property_cache

    def get_property_cache_key(self, key):
        '''
        Get properties which were previously resolved with key.
        '''
        try:

            self.property_cache[key]

        except KeyError:
            self.update_property_cache()

        return self.property_cache

    def get_activities_by_activity_status_ordered(self, status):
        '''
        Get all activities available on this licence by status using the last
        issued application to chain all previous application activities. The
        list is ordered by issue date.

        NOTE: Issue Date is by Activity Purpose not Licence Activity therefore
        getter may not perform correctly.
        '''
        return self.current_application.get_activity_chain(
            activity_status=status).order_by(
            'licence_activity_id', '-issue_date'
        )

    def get_activities_by_activity_status(self, status):
        '''
        Get all current activities available on this licence by status using
        the last issued application to chain all previous application
        activities.
        '''
        return self.current_application.get_current_activity_chain(
            activity_status=status)

    def get_activities_by_processing_status_ordered(self, status):
        '''
        Get all activities available on this licence by processing status using
        the last issued application to chain all previous application
        activities. The list is ordered by issue date.

        NOTE: Issue Date is by Activity Purpose not Licence Activity therefore
        getter may not perform correctly.
        '''
        return self.current_application.get_activity_chain(
            processing_status=status).order_by(
            'licence_activity_id', '-issue_date'
        )

    def get_activities_by_processing_status(self, status):
        '''
        Get all current activities available on this licence by the processing
        status using the last issued application to chain all previous
        application activities.
        '''
        return self.current_application.get_current_activity_chain(
            processing_status=status).order_by(
            'licence_activity_id',
        )

    def get_application_activities_by(
            self, activity_id=None, action=None, purpose_ids=None):
        '''
        Returns the latest list of ApplicationSelectedActivity records for a
        single application.

        Supports actioning by allowing single applications with multiple
        activities and purposes to be actioned by an officer in one process.

        NOTE: Supporting only Reissue.
        '''
        acts = self.get_latest_activities_for_licence_activity_and_action(
            activity_id,
            action
        )
        if action == WildlifeLicence.ACTIVITY_PURPOSE_ACTION_REISSUE:
            activities = self.latest_activities
            acts = activities.filter(
                proposed_purposes__purpose_id__in=purpose_ids)
            first = acts[0]
            acts = acts.filter(application_id=first.application_id)

        return acts

    def get_latest_activities_for_licence_activity_and_action(
            self, licence_activity_id=None, action=None):
        '''
        Return a list of ApplicationSelectedActivity records for the licence
        Filter by licence_activity_id (optional) and/or specified action
        (optional).

        '''
        # for a given licence_activity_id and action, return relevant
        # applications only check if licence is the latest in its category for
        # the applicant.
        CANCEL = WildlifeLicence.ACTIVITY_PURPOSE_ACTION_CANCEL
        SUSPEND = WildlifeLicence.ACTIVITY_PURPOSE_ACTION_SUSPEND
        SURRENDER = WildlifeLicence.ACTIVITY_PURPOSE_ACTION_SURRENDER
        RENEW = WildlifeLicence.ACTIVITY_PURPOSE_ACTION_REACTIVATE_RENEW
        REINSTATE = WildlifeLicence.ACTIVITY_PURPOSE_ACTION_REINSTATE
        REISSUE = WildlifeLicence.ACTIVITY_PURPOSE_ACTION_REISSUE

        if self.is_latest_in_category:
            latest_activities = self.latest_activities
            if licence_activity_id:
                latest_activities = latest_activities.filter(
                    licence_activity_id=licence_activity_id)

            # get the list of can_<action> ApplicationSelectedActivity records
            if action:
                can_action_activity_ids = []
                purposes_in_open_applications = \
                    self.get_purposes_in_open_applications()

                for activity in latest_activities:
                    activity_can_action = activity.can_action(
                        purposes_in_open_applications)
                    if action == CANCEL:
                        if activity_can_action['can_cancel']:
                            can_action_activity_ids.append(activity.id)
                    elif action == SUSPEND:
                        if activity_can_action['can_suspend']:
                            can_action_activity_ids.append(activity.id)
                    elif action == SURRENDER:
                        if activity_can_action['can_surrender']:
                            can_action_activity_ids.append(activity.id)
                    elif action == RENEW:
                        if activity_can_action['can_reactivate_renew']:
                            can_action_activity_ids.append(activity.id)
                    elif action == REINSTATE:
                        if activity_can_action['can_reinstate']:
                            can_action_activity_ids.append(activity.id)
                    elif action == REISSUE:
                        if activity_can_action['can_reissue']:
                            can_action_activity_ids.append(activity.id)

                latest_activities = latest_activities.filter(
                    id__in=can_action_activity_ids)
        else:
            latest_activities = []

        return latest_activities

    def get_latest_purposes_for_licence_activity_and_action(
            self, licence_activity_id=None, action=None):
        '''
        Return a list of LicencePurpose records for the licence Filter by
        licence_activity_id (optional) and/or specified action (optional)
        Exclude purposes that are currently in an application being processed.

        TODO:AYN REDUNDANT replace with LicenceActioner.
        '''
        can_action_purpose_list = []
        active_licence_purposes = self.get_purposes_in_open_applications()
        latest_activities = \
            self.get_latest_activities_for_licence_activity_and_action(
                licence_activity_id, action
            )

        for activity in latest_activities:
            for purpose in activity.purposes:
                if purpose.id not in active_licence_purposes:
                    can_action_purpose_list.append(purpose.id)
        records = LicencePurpose.objects.filter(
            id__in=can_action_purpose_list
        ).distinct()

        return records

    def get_latest_purposes_for_licence(self, licence_activity_id):
        '''
        Return a list of LicencePurpose records for the licence. Exclude
        purposes that are currently in an application being processed.

        TODO:AYN REDUNDANT replace with LicenceActioner.
        '''
        from wildlifecompliance.components.applications.models import (
            ApplicationSelectedActivity,
            ApplicationSelectedActivityPurpose,
        )
        can_action_purpose_list = []
        status = {
            ApplicationSelectedActivity.ACTIVITY_STATUS_CURRENT,
            ApplicationSelectedActivity.ACTIVITY_STATUS_REPLACED,
            ApplicationSelectedActivity.ACTIVITY_STATUS_SUSPENDED,
        }

        active_licence_purposes = self.get_purposes_in_open_applications()
        latest = self.current_application.get_current_activity_chain(
            activity_status__in=status
        ).filter(licence_activity_id=licence_activity_id)

        for activity in latest:
            for proposed in activity.proposed_purposes.all():
                if proposed.purpose.id not in active_licence_purposes\
                        and proposed.is_issued:
                    can_action_purpose_list.append(proposed.id)

        ISSUED = ApplicationSelectedActivityPurpose.PROCESSING_STATUS_ISSUED
        records = ApplicationSelectedActivityPurpose.objects.filter(
            id__in=can_action_purpose_list,
            processing_status=ISSUED,
        ).distinct()

        return records

    def get_purposes_in_open_applications(self):
        """
        Return a list of LicencePurpose records for the licence that are
        currently in an application being processed
        """
        from wildlifecompliance.components.applications.models import (
            Application, ApplicationSelectedActivity)

        open_applications = Application.objects.filter(
            Q(org_applicant=self.current_application.org_applicant)
            if self.current_application.org_applicant
            else Q(proxy_applicant=self.current_application.proxy_applicant)
            if self.current_application.proxy_applicant
            else Q(
                submitter=self.current_application.submitter,
                proxy_applicant=None,
                org_applicant=None)
        ).computed_filter(
            licence_category_id=self.licence_category.id
        ).exclude(
            selected_activities__processing_status__in=[
                ApplicationSelectedActivity.PROCESSING_STATUS_ACCEPTED,
                ApplicationSelectedActivity.PROCESSING_STATUS_DECLINED,
                ApplicationSelectedActivity.PROCESSING_STATUS_DISCARDED
            ]
        )
        open_purposes = open_applications.values_list(
            'licence_purposes',
            flat=True)

        return open_purposes

    def get_proposed_purposes_in_applications(self):
        '''
        Return a list of ApplicationSelectedActivityPurpose records issued
        through all applications for the licence.
        '''
        from wildlifecompliance.components.applications.models import (
            ApplicationSelectedActivityPurpose,
            ApplicationSelectedActivity,
        )

        # activities for this licence in current or suspended.
        activity_status = [
                ApplicationSelectedActivity.ACTIVITY_STATUS_CURRENT,
                ApplicationSelectedActivity.ACTIVITY_STATUS_REPLACED,
                ApplicationSelectedActivity.ACTIVITY_STATUS_SUSPENDED,
        ]
        # latest purposes on the activities which are issued or reissued.
        purpose_process_status = [
            ApplicationSelectedActivityPurpose.PROCESSING_STATUS_ISSUED,
            ApplicationSelectedActivityPurpose.PROCESSING_STATUS_REISSUE,
        ]

        activity_ids = [
            a.id for a in self.current_application.get_current_activity_chain(
                activity_status__in=activity_status
            )
        ]

        purposes = ApplicationSelectedActivityPurpose.objects.filter(
            selected_activity__in=activity_ids,
            processing_status__in=purpose_process_status
        ).order_by('purpose_sequence')

        return purposes

    @property
    def latest_activities_merged(self):
        """
        Return a list of activities for the licence, merged by
        licence_activity_id (1 per LicenceActivity)

        NOTE:AYN redundant replaced with LicenceActioner.
        """
        latest_activities = self.latest_activities
        merged_activities = {}

        if self.is_latest_in_category:
            purposes_in_open_applications = list(
                self.get_purposes_in_open_applications())
        else:
            purposes_in_open_applications = None

        for activity in latest_activities:
            if purposes_in_open_applications or\
                    purposes_in_open_applications == []:
                activity_can_action = activity.can_action(
                    purposes_in_open_applications)
            else:
                activity_can_action = {
                    'licence_activity_id': activity.licence_activity_id,
                    'can_renew': False,
                    'can_amend': False,
                    'can_surrender': False,
                    'can_cancel': False,
                    'can_suspend': False,
                    'can_reissue': False,
                    'can_reinstate': False,
                }

            # Check if a record for the licence_activity_id already exists, if
            # not, add.
            if not merged_activities.get(activity.licence_activity_id):

                issued_list = [
                    p for p in activity.proposed_purposes.all() if p.is_issued]

                if not len(issued_list):
                    continue

                merged_activities[activity.licence_activity_id] = {
                    'licence_activity_id': activity.licence_activity_id,
                    'activity_name_str': activity.licence_activity.name,
                    'issue_date': activity.get_issue_date(),
                    'start_date': activity.get_start_date(),
                    'expiry_date': '\n'.join(['{}'.format(
                        p.expiry_date.strftime('%d/%m/%Y') if p.expiry_date else '')
                        for p in activity.proposed_purposes.all() if p.is_issued]),
                    'activity_purpose_names_and_status': '\n'.join(['{} ({})'.format(
                        p.purpose.name, activity.get_activity_status_display())
                        for p in activity.proposed_purposes.all() if p.is_issued]),
                    'can_action':
                        {
                            'licence_activity_id': activity.licence_activity_id,
                            'can_renew': activity_can_action['can_renew'],
                            'can_amend': activity_can_action['can_amend'],
                            'can_surrender': activity_can_action['can_surrender'],
                            'can_cancel': activity_can_action['can_cancel'],
                            'can_suspend': activity_can_action['can_suspend'],
                            'can_reissue': activity_can_action['can_reissue'],
                            'can_reinstate': activity_can_action['can_reinstate'],
                        }
                }
            else:
                activity_key = merged_activities[activity.licence_activity_id]
                activity_key['activity_purpose_names_and_status'] += \
                    '\n' + '\n'.join(['{} ({})'.format(
                        p.purpose.name, activity.get_activity_status_display())
                        for p in activity.proposed_purposes.all() if p.is_issued and p.purpose in activity.purposes])
                activity_key['expiry_date'] += \
                    '\n' + '\n'.join(['{}'.format(
                        p.expiry_date.strftime('%d/%m/%Y') if p.expiry_date else None)
                        for p in activity.proposed_purposes.all() if p.is_issued and p.purpose in activity.purposes])
                activity_key['can_action']['can_renew'] =\
                    activity_key['can_action']['can_renew'] or activity_can_action['can_renew']
                activity_key['can_action']['can_amend'] =\
                    activity_key['can_action']['can_amend'] or activity_can_action['can_amend']
                activity_key['can_action']['can_surrender'] =\
                    activity_key['can_action']['can_surrender'] or activity_can_action['can_surrender']
                activity_key['can_action']['can_cancel'] =\
                    activity_key['can_action']['can_cancel'] or activity_can_action['can_cancel']
                activity_key['can_action']['can_suspend'] =\
                    activity_key['can_action']['can_suspend'] or activity_can_action['can_suspend']
                activity_key['can_action']['can_reissue'] =\
                    activity_key['can_action']['can_reissue'] or activity_can_action['can_reissue']
                activity_key['can_action']['can_reinstate'] =\
                    activity_key['can_action']['can_reinstate'] or activity_can_action['can_reinstate']

        merged_activities_list = merged_activities.values()

        return merged_activities_list

    @property
    def latest_activities(self):
        '''
        Returns the most recently issued activities.

        '''
        from wildlifecompliance.components.applications.models import (
            ApplicationSelectedActivity)

        REPLACE = ApplicationSelectedActivity.ACTIVITY_STATUS_REPLACED

        return self.get_activities_by_processing_status(
            ApplicationSelectedActivity.PROCESSING_STATUS_ACCEPTED
        ).exclude(activity_status=REPLACE)

    @property
    def current_activities(self):
        from wildlifecompliance.components.applications.models import ApplicationSelectedActivity
        return self.get_activities_by_activity_status(ApplicationSelectedActivity.ACTIVITY_STATUS_CURRENT)

    @property
    def next_licence_number_id(self):
        licence_number_max = WildlifeLicence.objects.all().aggregate(
            Max('licence_number'))['licence_number__max']
        if licence_number_max is None:
            return self.pk
        else:
            return int(licence_number_max.split('L')[1]) + 1

    @property
    def reference(self):
        return '{}-{}'.format(self.licence_number, self.licence_sequence)

    @property
    def is_issued(self):
        return self.licence_number is not None and len(self.licence_number) > 0

    @property
    def is_latest_in_category(self):
        # Returns True if the licence is the most recent one of it's category, filtered by
        # matching org_applicant, proxy_applicant and submitter
        organisation_id = self.current_application.org_applicant
        proxy_id = self.current_application.proxy_applicant
        submitter = self.current_application.submitter
        return WildlifeLicence.objects.filter(
            Q(current_application__org_applicant_id=organisation_id) if organisation_id else
            (Q(current_application__submitter=proxy_id) |
                Q(current_application__proxy_applicant=proxy_id)) if proxy_id else
            Q(current_application__submitter=submitter,
              current_application__proxy_applicant=None,
              current_application__org_applicant=None
            )
        ).filter(licence_category_id=self.licence_category.id).latest('id') == self

    # @property
    # def can_action(self):
    #     # Returns DICT of can_<action> if any of the licence's
    #     # latest_activities can be actioned
    #     can_action = {
    #         'can_amend': False,
    #         'can_renew': False,
    #         'can_reactivate_renew': False,
    #         'can_surrender': False,
    #         'can_cancel': False,
    #         'can_suspend': False,
    #         'can_reissue': False,
    #         'can_reinstate': False,
    #     }

    #     # only check if licence is the latest in its category for the applicant
    #     if self.is_latest_in_category:
    #         # set True if any activities can be actioned
    #         purposes_in_open_applications = self.get_purposes_in_open_applications()
    #         for activity in self.latest_activities:
    #             activity_can_action = activity.can_action(purposes_in_open_applications)
    #             if activity_can_action.get('can_amend'):
    #                 can_action['can_amend'] = True
    #             if activity_can_action.get('can_renew'):
    #                 can_action['can_renew'] = True
    #             if activity_can_action.get('can_reactivate_renew'):
    #                 can_action['can_reactivate_renew'] = True
    #             if activity_can_action.get('can_surrender'):
    #                 can_action['can_surrender'] = True
    #             if activity_can_action.get('can_cancel'):
    #                 can_action['can_cancel'] = True
    #             if activity_can_action.get('can_suspend'):
    #                 can_action['can_suspend'] = True
    #             if activity_can_action.get('can_reissue'):
    #                 can_action['can_reissue'] = True
    #             if activity_can_action.get('can_reinstate'):
    #                 can_action['can_reinstate'] = True

    #     return can_action

    @property
    def has_inspection_open(self):
        """
        An attribute indicating a licence inspection is created and opened for
        this License.
        """
        inspection_exists = False

        inspections = LicenceInspection.objects.filter(
            licence=self
        )
        is_active = [i.is_active for i in inspections if i.is_active]
        inspection_exists = is_active[0] if is_active else False

        return inspection_exists

    def create_inspection(self, request):
        '''
        Creates an inspection for this licence.
        '''
        with transaction.atomic():
            try:
                inspection = Inspection.objects.get(
                    id=request.data.get('inspection_id'))

                licence_inspection, created = \
                    LicenceInspection.objects.get_or_create(
                        licence=self,
                        inspection=inspection
                    )
                licence_inspection.save()

                # Create a log entry for the inspection
                action = LicenceUserAction.ACTION_CREATE_LICENCE_INSPECTION
                self.log_user_action(
                    action.format(
                        inspection.number, self.licence_number), request)

            except Inspection.DoesNotExist:
                raise Exception('Inspection was not created')

            except BaseException:
                raise

    def apply_action_to_licence(self, request, action):
        """
        Applies a specified action to a all of a licence's activities and purposes for a licence
        """
        if action not in [
            WildlifeLicence.ACTIVITY_PURPOSE_ACTION_REACTIVATE_RENEW,
            WildlifeLicence.ACTIVITY_PURPOSE_ACTION_SURRENDER,
            WildlifeLicence.ACTIVITY_PURPOSE_ACTION_CANCEL,
            WildlifeLicence.ACTIVITY_PURPOSE_ACTION_SUSPEND,
            WildlifeLicence.ACTIVITY_PURPOSE_ACTION_REINSTATE
        ]:
            raise ValidationError('Selected action is not valid')
        with transaction.atomic():
            for activity_id in self.latest_activities.values_list('licence_activity_id', flat=True):
                for activity in self.get_latest_activities_for_licence_activity_and_action(
                        activity_id, action):
                    if action == WildlifeLicence.ACTIVITY_PURPOSE_ACTION_REACTIVATE_RENEW:
                        activity.reactivate_renew(request)
                    elif action == WildlifeLicence.ACTIVITY_PURPOSE_ACTION_SURRENDER:
                        activity.surrender(request)
                    elif action == WildlifeLicence.ACTIVITY_PURPOSE_ACTION_CANCEL:
                        activity.cancel(request)
                    elif action == WildlifeLicence.ACTIVITY_PURPOSE_ACTION_SUSPEND:
                        activity.suspend(request)
                    elif action == WildlifeLicence.ACTIVITY_PURPOSE_ACTION_REINSTATE:
                        activity.reinstate(request)

    def apply_action_to_purposes(self, request, action):
        """
        Applies a specified action to a licence's purposes for a single licence
        activity_id and selected purposes list If not all purposes for an
        activity are to be actioned, create new SYSTEM_GENERATED Applications
        and associated activities to apply the relevant statuses for each.

        TODO: replaced with LicenceActioner - this is only used to renew.
        """
        from wildlifecompliance.components.applications.models import (
            Application, ApplicationSelectedActivity
        )
        CANCEL = WildlifeLicence.ACTIVITY_PURPOSE_ACTION_CANCEL
        SUSPEND = WildlifeLicence.ACTIVITY_PURPOSE_ACTION_SUSPEND
        SURRENDER = WildlifeLicence.ACTIVITY_PURPOSE_ACTION_SURRENDER
        RENEW = WildlifeLicence.ACTIVITY_PURPOSE_ACTION_REACTIVATE_RENEW
        REINSTATE = WildlifeLicence.ACTIVITY_PURPOSE_ACTION_REINSTATE
        REISSUE = WildlifeLicence.ACTIVITY_PURPOSE_ACTION_REISSUE

        if action not in [
         RENEW, SURRENDER, CANCEL, SUSPEND, REINSTATE, REISSUE]:
            raise ValidationError('Selected action is not valid')

        with transaction.atomic():

            purpose_ids_list = request.data.get('purpose_ids_list', None)
            purpose_ids_list = list(set(purpose_ids_list))
            purpose_ids_list.sort()

            if LicencePurpose.objects.filter(id__in=purpose_ids_list).\
                    values_list('licence_activity_id', flat=True).\
                    distinct().count() != 1:
                raise ValidationError(
                  'Selected purposes must all be of the same licence activity')

            licence_activity_id = LicencePurpose.objects.filter(
                id__in=purpose_ids_list).first().licence_activity_id

            can_action_purposes = \
                self.get_latest_purposes_for_licence_activity_and_action(
                    licence_activity_id, action)
            can_action_purposes_ids_list = [
                purpose.id for purpose in can_action_purposes.order_by('id')]

            # A Reissue on Activity Purpose occurs on the selected Activity
            # only and does apply to all activities.
            # TODO:AYN requirement that reissue of active licence purposes only
            # from the same licence application.
            if action == WildlifeLicence.ACTIVITY_PURPOSE_ACTION_REISSUE:
                can_action_purposes_ids_list = purpose_ids_list
                # licence_activity_id = purpose_ids_list[0]

            # if all purposes were selected by the user for action,
            # action all previous status ApplicationSelectedActivity records
            if purpose_ids_list == can_action_purposes_ids_list:
                # TODO:AYN only want latest activity for purposes from the one
                # app.
                activities_to_action = self.get_application_activities_by(
                    licence_activity_id,
                    action,
                    can_action_purposes_ids_list,
                )
                # action target activities
                for activity in activities_to_action:
                    if action == RENEW:
                        activity.reactivate_renew(request)
                    elif action == SURRENDER:
                        activity.surrender(request)
                    elif action == CANCEL:
                        activity.cancel(request)
                    elif action == SUSPEND:
                        activity.suspend(request)
                    elif action == REINSTATE:
                        activity.reinstate(request)
                    elif action == REISSUE:
                        activity.reissue(request)

            else:
                # else, if not all purposes were selected by the user for
                # action:
                #  - if any ApplicationSelectedActivity records can be actioned
                #    completely (i.e. all purposes in the Application record
                #    are selected for action), action them.
                #  - create new Application for the purposes to remain in
                #    previous status, using the first application found to have
                #    a purpose_id to remain in previous status.
                #  - create new Application for the purposes to be actioned,
                #    using the first application found to have a purpose_id to
                #    action.
                #  - add purposes from other relevant applications to either
                #    the new previous status or new actioned application
                #    copying data from their respective Applications.
                #  - mark all previous status and not actioned
                #    ApplicationSelectedActivity records as REPLACED.

                # Use dict for new_previous_status_applications, new
                # application per previous possible status.
                # e.g. REINSTATE can come from both CANCELLED and SURRENDERED
                # activities/purposes.
                new_previous_status_applications = {}
                new_actioned_application = None
                # TODO:AYN get latest activities by application for reissue.
                licence_latest_activities = self.get_application_activities_by(
                    licence_activity_id, action, can_action_purposes_ids_list
                )
                previous_statuses = list(
                    set(licence_latest_activities.values_list(
                        'activity_status', flat=True))
                )
                for previous_status in previous_statuses:
                    new_previous_status_applications[previous_status] = None
                original_application_ids = licence_latest_activities.filter(
                    application__licence_purposes__in=purpose_ids_list
                    ).values_list('application_id', flat=True)
                original_applications = Application.objects.filter(
                    id__in=original_application_ids)

                for application in original_applications:
                    # get purpose_ids linked with application
                    application_licence_purpose_ids_list = \
                        application.licence_purposes.filter(
                            licence_activity_id=licence_activity_id
                        ).values_list('id', flat=True)

                    activity = application.selected_activities.get(
                        licence_activity_id=licence_activity_id
                    )
                    # Get previous_status and target post_actioned_status
                    previous_status = activity.activity_status
                    if action == RENEW:
                        post_actioned_status = \
                            ApplicationSelectedActivity.ACTIVITY_STATUS_EXPIRED
                    elif action == SURRENDER:
                        post_actioned_status = \
                            ApplicationSelectedActivity.ACTIVITY_STATUS_SURRENDERED
                    elif action == CANCEL:
                        post_actioned_status = \
                            ApplicationSelectedActivity.ACTIVITY_STATUS_CANCELLED
                    elif action == SUSPEND:
                        post_actioned_status = \
                            ApplicationSelectedActivity.ACTIVITY_STATUS_SUSPENDED
                    elif action == REINSTATE:
                        post_actioned_status = \
                            ApplicationSelectedActivity.ACTIVITY_STATUS_CURRENT
                    elif action == REISSUE:
                        post_actioned_status = \
                            ApplicationSelectedActivity.ACTIVITY_STATUS_CURRENT

                    # if an application's purpose_ids are all in the
                    # purpose_ids_list, completely action the
                    # ApplicationSelectedActivity.
                    if not set(application_licence_purpose_ids_list) \
                            - set(purpose_ids_list):
                        if action == RENEW:
                            activity.reactivate_renew(request)
                        elif action == SURRENDER:
                            activity.surrender(request)
                        elif action == CANCEL:
                            activity.cancel(request)
                        elif action == SUSPEND:
                            activity.suspend(request)
                        elif action == REINSTATE:
                            activity.reinstate(request)
                        elif action == REISSUE:
                            activity.reissue(request)

                    # if application still has previous_status purposes after
                    # actioning selected purposes.
                    elif set(application_licence_purpose_ids_list) \
                            - set(purpose_ids_list):

                        common_actioned_purpose_ids = set(application_licence_purpose_ids_list) & set(purpose_ids_list)
                        remaining_previous_status_purpose_ids = set(application_licence_purpose_ids_list) - set(purpose_ids_list)

                        # create new previous_status application from this
                        # application if not yet exists.
                        if not new_previous_status_applications[previous_status]:
                            new_previous_status_applications[previous_status] = application.copy_application_purposes_for_status(
                                remaining_previous_status_purpose_ids, previous_status)

                        # else, if new previous_status application exists, link
                        # the target LicencePurpose IDs to it.
                        else:
                            # Link the target LicencePurpose IDs to the
                            # application.
                            for licence_purpose_id in remaining_previous_status_purpose_ids:
                                application.copy_application_purpose_to_target_application(
                                    new_previous_status_applications[previous_status],
                                    licence_purpose_id)

                                # Copy conditions to the new_actioned_application.
                                application.copy_conditions_to_target(
                                    new_previous_status_applications[
                                        previous_status
                                    ],
                                    licence_purpose_id
                                )

                        # create new actioned application from this application
                        # if not yet exists.
                        if not new_actioned_application:
                            new_actioned_application = application.copy_application_purposes_for_status(
                                common_actioned_purpose_ids,
                                post_actioned_status
                            )
                        # else, if new actioned application exists, link the
                        # target LicencePurpose IDs to it.
                        else:
                            # Link the target LicencePurpose IDs to the
                            # application.
                            for licence_purpose_id in common_actioned_purpose_ids:
                                application.copy_application_purpose_to_target_application(
                                    new_actioned_application,
                                    licence_purpose_id)

                                # Copy conditions to the
                                # new_actioned_application.
                                application.copy_conditions_to_target(
                                    new_actioned_application,
                                    licence_purpose_id,
                                )

                # Set original activities to REPLACED except for any that were
                # ACTIONED completely.
                original_activities = ApplicationSelectedActivity.objects.\
                    filter(application__id__in=original_application_ids).\
                    exclude(activity_status=post_actioned_status)
                for activity in original_activities:
                    activity.mark_as_replaced(request)

    @property
    def purposes_available_to_add(self):
        """
        Returns a list of LicencePurpose objects that can be added to a WildlifeLicence
        Same logic as the UserAvailableWildlifeLicencePurposesViewSet list function (used in API call)
        """
        available_purpose_records = LicencePurpose.objects.all()
        licence_category_id = self.licence_category.id
        current_activities = self.current_activities

        # Exclude any purposes that are linked with CURRENT activities
        active_purpose_ids = []
        for current_activity in current_activities:
            active_purpose_ids.extend([purpose.id for purpose in current_activity.purposes])
        available_purpose_records = available_purpose_records.exclude(
            id__in=active_purpose_ids
        )

        # Filter by Licence Category ID
        available_purpose_records = available_purpose_records.filter(
            licence_category_id=licence_category_id
        )

        return available_purpose_records

    # @property
    # def can_add_purpose(self):
    #     return self.is_latest_in_category and\
    #            self.purposes_available_to_add.count() > 0 and\
    #            self.can_action.get('can_amend')

    def has_additional_information_for(self, selected_activity):
        """
        Check for additional information exist for selected activity on this
        licence.
        """
        has_info = False
        activity_conditions = selected_activity.application.conditions.filter(
            licence_activity_id=selected_activity.licence_activity_id,
            licence_purpose_id=selected_activity.issued_purposes[0].id)

        for condition in activity_conditions:
            if condition.standard_condition:
                has_info = condition.standard_condition.additional_information
                return has_info

        return has_info

    def get_next_purpose_sequence(self):
        '''
        Returns the next sequence number for selected licence purposes.
        '''
        from wildlifecompliance.components.applications.models import (
            ApplicationSelectedActivityPurpose,
            ApplicationSelectedActivity,
        )
        next_sequence = 0
        # activities for this licence in current or suspended.
        activity_status = [
                ApplicationSelectedActivity.ACTIVITY_STATUS_CURRENT,
                ApplicationSelectedActivity.ACTIVITY_STATUS_REPLACED,
                ApplicationSelectedActivity.ACTIVITY_STATUS_SUSPENDED,
        ]
        # latest purposes on the activities which are issued or reissued.
        purpose_process_status = [
            ApplicationSelectedActivityPurpose.PROCESSING_STATUS_ISSUED,
            ApplicationSelectedActivityPurpose.PROCESSING_STATUS_REISSUE,
        ]

        activities = self.current_application.get_current_activity_chain(
            activity_status__in=activity_status
        )
        latest_purposes = [
            p for p in [
                a.proposed_purposes.filter(
                    processing_status__in=purpose_process_status
                ) for a in activities
            ]
        ]

        # set the next sequence number from the latest proposed purposes from
        # all the activities.
        if latest_purposes:
            last_sequence = 0
            for a_purposes in latest_purposes:
                for purpose in a_purposes:
                    last_sequence = purpose.purpose_sequence \
                        if purpose.purpose_sequence > last_sequence \
                        else last_sequence
            next_sequence = last_sequence

        next_sequence += 1
        return next_sequence

    def get_purposes_in_sequence(self):
        '''
        Returns selected licence purposes for this licence in sequence order.
        '''
        from wildlifecompliance.components.applications.models import (
            ApplicationSelectedActivityPurpose,
            ApplicationSelectedActivity,
        )
        purposes = []
        # activities for this licence in current or suspended.
        activity_status = [
                ApplicationSelectedActivity.ACTIVITY_STATUS_CURRENT,
                ApplicationSelectedActivity.ACTIVITY_STATUS_REPLACED,
                ApplicationSelectedActivity.ACTIVITY_STATUS_SUSPENDED,
        ]
        # latest purposes on the activities which are issued or reissued.
        purpose_process_status = [
            ApplicationSelectedActivityPurpose.PROCESSING_STATUS_ISSUED,
            ApplicationSelectedActivityPurpose.PROCESSING_STATUS_REISSUE,
        ]

        activity_ids = [
            a.id for a in self.current_application.get_current_activity_chain(
                activity_status__in=activity_status
            )
        ]

        purposes = ApplicationSelectedActivityPurpose.objects.filter(
            selected_activity__in=activity_ids,
            processing_status__in=purpose_process_status
        ).order_by('purpose_sequence')

        purposes = self.get_proposed_purposes_in_applications()

        return purposes

    def get_purposes_to_expire(self):
        '''
        Returns selected licence purposes will have expired today.
        '''
        from wildlifecompliance.components.applications.models import (
            ApplicationSelectedActivityPurpose,
        )
        from datetime import date

        today = date.today()

        current_status = [
            ApplicationSelectedActivityPurpose.PURPOSE_STATUS_DEFAULT,
            ApplicationSelectedActivityPurpose.PURPOSE_STATUS_CURRENT,
        ]

        purposes = self.get_proposed_purposes_in_applications()

        to_expire = [
            p for p in purposes.filter(
                expiry_date__lt=today,
                purpose_status__in=current_status,
            )
        ]

        return to_expire

    def get_purposes_to_renew(self, period_days=0):
        '''
        Returns selected licence purposes which are about to expire in relation
        to period.

        :param: period_days is number of days before expiration.
        '''
        from wildlifecompliance.components.applications.models import (
            ApplicationSelectedActivityPurpose,
        )
        from datetime import date, timedelta

        today = date.today()
        today_plus_days = date.today() + timedelta(days=int(period_days))
        purposes = self.get_proposed_purposes_in_applications()

        to_renew = [
            p for p in purposes.filter(
                expiry_date__range=[today, today_plus_days],
                sent_renewal=False,
                purpose_status__in=ApplicationSelectedActivityPurpose.RENEWABLE
            )
        ]
        to_renew = [p for p in to_renew if not p.purpose.not_renewable]
        return to_renew

    def get_document_history(self):
        '''
        Returns a query set of all licence documents for this licence by
        applications with current or suspended activities.
        '''
        pdf_name = 'licence-{0}.pdf'.format(self.licence_number)

        documents = LicenceDocument.objects.values(
                'uploaded_date',
                'name',
                'licence_document',
                'id',
            ).filter(
                name=pdf_name,
            )

        return documents

    def generate_doc(self):
        from wildlifecompliance.components.licences.pdf import create_licence_doc
        self.licence_document = create_licence_doc(
            self, self.current_application)
        self.save()

    def generate_preview_doc(self):
        from wildlifecompliance.components.licences.pdf import create_licence_pdf_bytes
        return create_licence_pdf_bytes(self, self.current_application)


    def log_user_action(self, action, request):
        return LicenceUserAction.log_action(self, action, request.user)


class LicenceInspection(models.Model):
    '''
    A model represention of an Inspection for Wildlife Licence.
    '''
    licence = models.ForeignKey(
        WildlifeLicence, related_name='licence_inspections')
    inspection = models.ForeignKey(
        Inspection, related_name='wildlifecompliance_licence_inspection')
    request_datetime = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'wildlifecompliance'

    def __str__(self):
        return 'Inspection #{0} for Licence {1}'.format(
            self.inspection.number, self.licence.licence_number)

    @property
    def is_active(self):
        '''
        An attribute to indicate that this licence inspection is currently
        progressing.
        '''
        is_active = False

        if self.inspection.status in [
            Inspection.STATUS_OPEN,
            Inspection.STATUS_AWAIT_ENDORSEMENT,
        ]:
            is_active = True

        return is_active

class LicenceLogEntry(CommunicationsLogEntry):
    licence = models.ForeignKey(WildlifeLicence, related_name='comms_logs')

    class Meta:
        app_label = 'wildlifecompliance'

    def save(self, **kwargs):
        # save the application reference if the reference not provided
        if not self.reference:
            self.reference = self.licence.id
        super(LicenceLogEntry, self).save(**kwargs)


class LicenceUserAction(UserAction):
    ACTION_CREATE_LICENCE = "Create licence {}"
    ACTION_UPDATE_LICENCE = "Create licence {}"
    ACTION_CREATE_LICENCE_INSPECTION = \
        "Inspection {} for licence {} was requested."

    class Meta:
        app_label = 'wildlifecompliance'
        ordering = ('-when',)

    @classmethod
    def log_action(cls, licence, action, user):
        return cls.objects.create(
            licence=licence,
            who=user,
            what=str(action)
        )

    licence = models.ForeignKey(WildlifeLicence, related_name='action_logs')


# @receiver(pre_delete, sender=WildlifeLicence)
# def delete_documents(sender, instance, *args, **kwargs):
#     for document in instance.documents.all():
#         document.delete()

class WildlifeLicenceReceptionEmail(models.Model):
    '''
    An model representation of an Wildlife Licensing Reception email address
    used for general purposes.
    '''
    name = models.CharField(max_length=64)
    email = models.CharField(max_length=128)

    class Meta:
        app_label = 'wildlifecompliance'

    def __str__(self):
        return self.email


'''
NOTE: REGISTER MODELS FOR REVERSION HERE.
'''
reversion.register(
    WildlifeLicence,
    follow=[
        'licence_document',
        'replaced_by',
        'licence_category',
        'current_application',
    ]
)
reversion.register(
    LicencePurpose,
    follow=[
        'licence_category',
        'licence_activity',
    ]
)
reversion.register(
    PurposeSpecies,
    follow=[
        'licence_purpose',
    ]
)
reversion.register(
    LicenceActivity,
    follow=[
        'licence_category',
        'purpose',
    ]
)
reversion.register(
    LicenceCategory,
    follow=[
        'activity',
    ]
)
reversion.register(
    DefaultActivity,
    follow=[
        'activity',
        'licence_category',
    ]
)
reversion.register(
    DefaultPurpose,
    follow=[
        'purpose',
        'activity',
    ]
)
reversion.register(LicenceSpecies)
reversion.register(LicenceDocument)
reversion.register(WildlifeLicenceReceptionEmail)
reversion.register(LicenceInspection)
