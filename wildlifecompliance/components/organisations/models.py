from __future__ import unicode_literals

from django.db import models, transaction
from django.contrib.sites.models import Site
from django.dispatch import receiver
from django.db.models.signals import pre_delete, pre_save
from six import python_2_unicode_compatible
from django.core.exceptions import ValidationError
from django.contrib.postgres.fields.jsonb import JSONField

from ledger_api_client.utils import get_organisation, get_search_organisation

from ledger_api_client.ledger_models import EmailUserRO as EmailUser
from django.contrib.auth.models import Group
from wildlifecompliance.components.main.models import UserAction, CommunicationsLogEntry
from wildlifecompliance.components.organisations.utils import random_generator, get_officer_email_list
from wildlifecompliance.components.organisations.emails import (
    send_organisation_request_accept_email_notification,
    send_organisation_request_amendment_requested_email_notification,
    send_organisation_link_email_notification,
    send_organisation_unlink_email_notification,
    send_organisation_contact_adminuser_email_notification,
    send_organisation_contact_user_email_notification,
    send_organisation_contact_suspend_email_notification,
    send_organisation_reinstate_email_notification,
    send_organisation_contact_decline_email_notification,
    send_organisation_request_decline_email_notification,
    send_organisation_request_email_notification,
    send_organisation_request_link_email_notification,
    send_organisation_request_decline_admin_email_notification,
    send_organisation_request_accept_admin_email_notification,
    send_organisation_id_upload_email_notification,
    send_organisation_contact_consultant_email_notification,
)
from wildlifecompliance.components.main.models import Document
from wildlifecompliance.components.main.utils import (
    get_first_name,
    get_last_name,
    get_full_name,
)

from django.conf import settings
from django.core.files.storage import FileSystemStorage
private_storage = FileSystemStorage(location=settings.BASE_DIR+"/private-media/", base_url='/private-media/')

def is_wildlife_compliance_officer(request):
    wildlife_compliance_user = request.user.has_perm('wildlifecompliance.system_administrator') or \
               request.user.is_superuser

    if request.user.is_authenticated() and (
            Group.objects.get(name=settings.GROUP_WILDLIFE_COMPLIANCE_OFFICERS).user_set.filter(id=request.user.id)
        ):
        wildlife_compliance_user = True

    return wildlife_compliance_user

#TODO fix for segregation
@python_2_unicode_compatible
class Organisation(models.Model):
    intelligence_information_text = models.TextField(blank=True)
    organisation_id = models.IntegerField(
        unique=True, verbose_name="Ledger Organisation ID"
    )
    #organisation = models.ForeignKey(ledger_organisation)
    # TODO: business logic related to delegate changes.
    delegates = models.ManyToManyField(
        EmailUser,
        blank=True,
        through='UserDelegation',
        related_name='wildlifecompliance_organisations')
    admin_pin_one = models.CharField(max_length=50, blank=True)
    admin_pin_two = models.CharField(max_length=50, blank=True)
    user_pin_one = models.CharField(max_length=50, blank=True)
    user_pin_two = models.CharField(max_length=50, blank=True)

    class Meta:
        app_label = 'wildlifecompliance'

    @property
    def organisation(self):
        return get_organisation(self.id)

    def __str__(self):
        return str(self.organisation)

    def log_user_action(self, action, request):
        return OrganisationAction.log_action(self, action, request.user)

    def validate_pins(self, pin1, pin2, request):
        val_admin = self.admin_pin_one == pin1 and self.admin_pin_two == pin2
        val_user = self.user_pin_one == pin1 and self.user_pin_two == pin2
        if val_admin:
            val = val_admin
            admin_flag = True
            role = OrganisationContact.ORG_CONTACT_ROLE_ADMIN
        elif val_user:
            val = val_user
            admin_flag = False
            role = OrganisationContact.ORG_CONTACT_ROLE_USER
        else:
            val = False
            return val

        self.add_user_contact(request.user, request, admin_flag, role)
        return val

    def add_user_contact(self, user, request, admin_flag, role):
        '''
        Add user contact for linking to this Organisation. Linking requires
        authorisation as validation pins are supplied by admin.
        '''
        OrganisationContact.objects.create(
            organisation=self,
            first_name=get_first_name(user),
            last_name=get_last_name(user),
            mobile_number=user.mobile_number,
            phone_number=user.phone_number,
            fax_number=user.fax_number,
            email=user.email,
            user_role=role,
            user_status=OrganisationContact.ORG_CONTACT_STATUS_PENDING,
            is_admin=admin_flag

        )

        # log linking
        self.log_user_action(
            OrganisationAction.ACTION_CONTACT_ADDED.format(
                '{} {}({})'.format(
                    get_first_name(user),
                    get_last_name(user),
                    user.email)),
            request)

    def accept_user(self, user, request):
        with transaction.atomic():
            # try:
            #     UserDelegation.objects.get(organisation=self,user=user)
            #     raise ValidationError('This user has already been linked to {}'.format(str(self.organisation)))
            # except UserDelegation.DoesNotExist:
            delegate = UserDelegation.objects.create(
                organisation=self, user=user)

            try:
                org_contact = OrganisationContact.objects.get(
                    organisation=self, email=delegate.user.email)
                org_contact.user_status = OrganisationContact.ORG_CONTACT_STATUS_ACTIVE
                org_contact.save()
            except OrganisationContact.DoesNotExist:
                pass

        # log linking
            self.log_user_action(
                OrganisationAction.ACTION_LINK.format(
                    '{} {}({})'.format(
                        get_first_name(delegate.user),
                        get_last_name(delegate.user),
                        delegate.user.email)),
                request)
            send_organisation_link_email_notification(
                user, request.user, self, request)

    def decline_user(self, user, request):
        try:
            org_contact = OrganisationContact.objects.get(
                organisation=self, email=user.email)
            org_contact.user_status = OrganisationContact.ORG_CONTACT_STATUS_DECLINED
            org_contact.save()
        except OrganisationContact.DoesNotExist:
            pass
        OrganisationContactDeclinedDetails.objects.create(
            officer=request.user,
            request=org_contact
        )

        # log linking
        self.log_user_action(
            OrganisationAction.ACTION_CONTACT_DECLINED.format(
                '{} {}({})'.format(
                    get_first_name(user),
                    get_last_name(user),
                    user.email)),
            request)
        send_organisation_contact_decline_email_notification(
            user, request.user, self, request)

    # def link_user(self, user, request, admin_flag):
    #     with transaction.atomic():
    #         try:
    #             UserDelegation.objects.get(organisation=self, user=user)
    #             raise ValidationError('This user has already been linked to {}'.format(str(self.organisation)))
    #         except UserDelegation.DoesNotExist:
    #             delegate = UserDelegation.objects.create(organisation=self, user=user)
    #         if self.has_no_admins and ajsdhflkajhsdflkjhasdlkjfh:
    #             role = 'organisation_admin'
    #             is_admin = True
    #         elif admin_flag:
    #             role = 'organisation_admin'
    #             is_admin = True
    #         else:
    #             role = 'organisation_user'
    #             is_admin = False
    #
    #         # Create contact person
    #         OrganisationContact.objects.create(
    #             organisation=self,
    #             first_name=user.first_name,
    #             last_name=user.last_name,
    #             mobile_number=user.mobile_number,
    #             phone_number=user.phone_number,
    #             fax_number=user.fax_number,
    #             email=user.email,
    #             user_role=role,
    #             user_status='pending',
    #             is_admin=is_admin
    #
    #         )
    #         # log linking
    #         self.log_user_action(OrganisationAction.ACTION_LINK.format(
    #             '{} {}({})'.format(delegate.user.first_name, delegate.user.last_name, delegate.user.email)), request)
    #         # send email
    #         send_organisation_link_email_notification(user, request.user, self, request)

    def accept_declined_user(self, user, request):
        with transaction.atomic():
            try:
                UserDelegation.objects.get(organisation=self, user=user)
                raise ValidationError(
                    'This user has already been linked to {}'.format(str(self.organisation)))
            except UserDelegation.DoesNotExist:
                delegate = UserDelegation.objects.create(
                    organisation=self, user=user)

            try:
                org_contact = OrganisationContact.objects.get(
                    organisation=self, email=delegate.user.email)
                org_contact.user_status = OrganisationContact.ORG_CONTACT_STATUS_ACTIVE
                org_contact.save()
            except OrganisationContact.DoesNotExist:
                pass

            # log linking
            self.log_user_action(
                OrganisationAction.ACTION_LINK.format(
                    '{} {}({})'.format(
                        get_first_name(delegate.user),
                        get_last_name(delegate.user),
                        delegate.user.email)),
                request)
            # send email
            send_organisation_link_email_notification(
                user, request.user, self, request)

    def relink_user(self, user, request):
        with transaction.atomic():
            try:
                UserDelegation.objects.get(organisation=self, user=user)
                raise ValidationError(
                    'This user has not yet been linked to {}'.format(str(self.organisation)))
            except UserDelegation.DoesNotExist:
                delegate = UserDelegation.objects.create(
                    organisation=self, user=user)
            try:
                org_contact = OrganisationContact.objects.get(
                    organisation=self, email=delegate.user.email)
                org_contact.user_status = OrganisationContact.ORG_CONTACT_STATUS_ACTIVE
                org_contact.save()
            except OrganisationContact.DoesNotExist:
                pass
            # log linking
            self.log_user_action(
                OrganisationAction.ACTION_MAKE_CONTACT_REINSTATE.format(
                    '{} {}({})'.format(
                        get_first_name(delegate.user),
                        get_last_name(delegate.user),
                        delegate.user.email)),
                request)
            # send email
            send_organisation_reinstate_email_notification(
                user, request.user, self, request)

    def unlink_user(self, user, request):
        with transaction.atomic():
            try:
                delegate = UserDelegation.objects.get(
                    organisation=self, user=user)
            except UserDelegation.DoesNotExist:
                raise ValidationError(
                    'This user is not a member of {}'.format(str(self.organisation)))
            # delete contact person
            try:
                org_contact = OrganisationContact.objects.get(
                    organisation=self, email=delegate.user.email)
                if org_contact.user_role == OrganisationContact.ORG_CONTACT_ROLE_ADMIN:
                    org_contact.user_status = OrganisationContact.ORG_CONTACT_STATUS_UNLINKED
                    org_contact.save()
                    # delete delegate
                    delegate.delete()
                else:
                    org_contact.user_status = OrganisationContact.ORG_CONTACT_STATUS_UNLINKED
                    org_contact.save()
                    # delete delegate
                    delegate.delete()
            except OrganisationContact.DoesNotExist:
                pass

            # log linking
            self.log_user_action(
                OrganisationAction.ACTION_UNLINK.format(
                    '{} {}({})'.format(
                        get_first_name(delegate.user),
                        get_last_name(delegate.user),
                        delegate.user.email)),
                request)
            # send email
            send_organisation_unlink_email_notification(
                user, request.user, self, request)

    def make_admin_user(self, user, request):
        with transaction.atomic():
            try:
                delegate = UserDelegation.objects.get(
                    organisation=self, user=user)
            except UserDelegation.DoesNotExist:
                raise ValidationError(
                    'This user is not a member of {}'.format(str(self.organisation)))
            # delete contact person
            try:
                org_contact = OrganisationContact.objects.get(
                    organisation=self, email=delegate.user.email)
                org_contact.user_role = OrganisationContact.ORG_CONTACT_ROLE_ADMIN
                org_contact.is_admin = True
                org_contact.save()
            except OrganisationContact.DoesNotExist:
                pass
            # log linking
            self.log_user_action(
                OrganisationAction.ACTION_MAKE_CONTACT_ADMIN.format(
                    '{} {}({})'.format(
                        get_first_name(delegate.user),
                        get_last_name(delegate.user),
                        delegate.user.email)),
                request)
            # send email
            send_organisation_contact_adminuser_email_notification(
                user, request.user, self, request)

    def make_user(self, user, request):
        with transaction.atomic():
            try:
                delegate = UserDelegation.objects.get(
                    organisation=self, user=user)
            except UserDelegation.DoesNotExist:
                raise ValidationError(
                    'This user is not a member of {}'.format(str(self.organisation)))
            # delete contact person
            try:
                org_contact = OrganisationContact.objects.get(
                    organisation=self, email=delegate.user.email)
                org_contact.user_role = OrganisationContact.ORG_CONTACT_ROLE_USER
                org_contact.is_admin = False
                org_contact.save()
            except OrganisationContact.DoesNotExist:
                pass
            # log linking
            self.log_user_action(
                OrganisationAction.ACTION_MAKE_CONTACT_USER.format(
                    '{} {}({})'.format(
                        get_first_name(delegate.user),
                        get_last_name(delegate.user),
                        delegate.user.email)),
                request)
            # send email
            send_organisation_contact_user_email_notification(
                user, request.user, self, request)

    def make_consultant(self, user, request):
        with transaction.atomic():
            try:
                delegate = UserDelegation.objects.get(
                    organisation=self, user=user)
            except UserDelegation.DoesNotExist:
                raise ValidationError(
                    'This user is not a member of {}'.format(str(self.organisation)))
            # add consultant
            try:
                org_contact = OrganisationContact.objects.get(
                    organisation=self, email=delegate.user.email)
                org_contact.user_role = OrganisationContact.ORG_CONTACT_ROLE_CONSULTANT
                org_contact.is_admin = True
                org_contact.save()
            except OrganisationContact.DoesNotExist:
                pass
            # log linking
            self.log_user_action(
                OrganisationAction.ACTION_MAKE_CONTACT_ADMIN.format(
                    '{} {}({})'.format(
                        get_first_name(delegate.user),
                        get_last_name(delegate.user),
                        delegate.user.email)),
                request)
            # send email
            send_organisation_contact_consultant_email_notification(
                user, request.user, self, request)

    def suspend_user(self, user, request):
        with transaction.atomic():
            try:
                delegate = UserDelegation.objects.get(
                    organisation=self, user=user)
            except UserDelegation.DoesNotExist:
                raise ValidationError(
                    'This user is not a member of {}'.format(str(self.organisation)))
            # delete contact person
            try:
                org_contact = OrganisationContact.objects.get(
                    organisation=self, email=delegate.user.email)
                org_contact.user_status = OrganisationContact.ORG_CONTACT_STATUS_SUSPENDED
                org_contact.save()
            except OrganisationContact.DoesNotExist:
                pass
            # log linking
            self.log_user_action(
                OrganisationAction.ACTION_MAKE_CONTACT_SUSPEND.format(
                    '{} {}({})'.format(
                        get_first_name(delegate.user),
                        get_last_name(delegate.user),
                        delegate.user.email)),
                request)
            # send email
            send_organisation_contact_suspend_email_notification(
                user, request.user, self, request)

    def reinstate_user(self, user, request):
        with transaction.atomic():
            try:
                delegate = UserDelegation.objects.get(
                    organisation=self, user=user)
            except UserDelegation.DoesNotExist:
                raise ValidationError(
                    'This user is not a member of {}'.format(str(self.organisation)))
            # delete contact person
            try:
                org_contact = OrganisationContact.objects.get(
                    organisation=self, email=delegate.user.email)
                org_contact.user_status = OrganisationContact.ORG_CONTACT_STATUS_ACTIVE
                org_contact.save()
            except OrganisationContact.DoesNotExist:
                pass
            # log linking
            self.log_user_action(
                OrganisationAction.ACTION_MAKE_CONTACT_REINSTATE.format(
                    '{} {}({})'.format(
                        get_first_name(delegate.user),
                        get_last_name(delegate.user),
                        delegate.user.email)),
                request)
            # send email
            send_organisation_reinstate_email_notification(
                user, request.user, self, request)

    def generate_pins(self):
        self.admin_pin_one = self._generate_pin()
        self.admin_pin_two = self._generate_pin()
        self.user_pin_one = self._generate_pin()
        self.user_pin_two = self._generate_pin()
        self.save()

    def _generate_pin(self):
        return random_generator()

    def send_organisation_request_link_notification(self, request):
        # Notify each Admin member of request to be linked to org.
        contacts = OrganisationContact.objects.filter(
            organisation_id=self.id,
            user_role=OrganisationContact.ORG_CONTACT_ROLE_ADMIN,
            user_status=OrganisationContact.ORG_CONTACT_STATUS_ACTIVE,
            is_admin=True)
        recipients = [c.email for c in contacts]
        send_organisation_request_link_email_notification(
            self, request, recipients)

    def send_organisation_id_upload_email_notification(self, applications, request):
        # Notify reviewing internal officers of update to the organisation ID
        # for relevant applications.
        officer_list = get_officer_email_list(self)
        contact_email = EmailUser.objects.filter(email=request.user).first()
        if officer_list:
            send_organisation_id_upload_email_notification(
                officer_list, self, contact_email, applications, request)

    @staticmethod
    def existence(abn, name=None):
        exists = True
        org = None
        #TODO test with name=None, otherwise fix to use name
        organisation_response = get_search_organisation(name, abn)
        response_status = organisation_response.get("status", None)

        if response_status == status.HTTP_200_OK:
            ledger_org = organisation_response.get("data", {})[0]
            try:
                org = Organisation.objects.get(
                    organisation_id=ledger_org["organisation_id"]
                )
            except Organisation.DoesNotExist:
                exists = False
        else:
            exists = False

        if exists:
            if has_atleast_one_admin(org):
                return {
                    "exists": exists,
                    "id": org.id,
                    "first_five": org.first_five,
                }
            else:
                return {"exists": has_atleast_one_admin(org)}
        return {"exists": exists}

    @property
    def name(self):
        return self.organisation.name

    @property
    def abn(self):
        return self.organisation.abn

    @property
    def address(self):
        return self.organisation.postal_address

    @property
    def address_string(self):
        org_address = self.organisation.postal_address
        if org_address:
            address_string = '{} {} {} {} {}'.format(
                org_address.line1,
                org_address.locality,
                org_address.state,
                org_address.postcode,
                org_address.country
            )
            return address_string
        else:
            return ''

    @property
    def email(self):
        return self.organisation.email

    @property
    def first_five(self):
        """
        :return: A string of names for the first five Administrator delegates.
        """
        _names = ''
        for user in OrganisationContact.objects.filter(
                organisation_id=self.id,
                user_role=OrganisationContact.ORG_CONTACT_ROLE_ADMIN,
                user_status=OrganisationContact.ORG_CONTACT_STATUS_ACTIVE,
                is_admin=True):
            _names += get_full_name(user)

        return _names

    @property
    def all_admin_emails(self):
        return [org_admin.email for org_admin in
                    OrganisationContact.objects.filter(
                        organisation_id=self.id,
                        user_role=OrganisationContact.ORG_CONTACT_ROLE_ADMIN,
                        user_status=OrganisationContact.ORG_CONTACT_STATUS_ACTIVE,
                        is_admin=True
                    )
                ]

    @property
    def has_no_admins(self):
        return self.contacts.filter(user_role=OrganisationContact.ORG_CONTACT_ROLE_ADMIN).count() < 1

   #not in use and would not work (no request param)
   #@property
   #def can_contact_user_edit(self):
   #    """
   #    :return: True if the application is in one of the editable status.
   #    """
   #    org_contact = OrganisationContact.objects.get(
   #        organisation_id=self.id, first_name=request.user.first_name)

   #    return org_contact.is_admin \
   #        and org_contact.user_status == OrganisationContact.ORG_CONTACT_STATUS_ACTIVE \
   #        and org_contact.user_role == OrganisationContact.ORG_CONTACT_ROLE_ADMIN

    @property
    def can_user_edit(self, email):
        """
        :return: True if the application is in one of the editable status.
        """
        org_contact = OrganisationContact.objects.get(
            organisation_id=self.id, email=email)

        return org_contact.is_admin \
            and org_contact.user_status == OrganisationContact.ORG_CONTACT_STATUS_ACTIVE \
            and org_contact.user_role == OrganisationContact.ORG_CONTACT_ROLE_ADMIN

    @property
    def get_related_items_identifier(self):
        return self.abn

    @property
    def get_related_items_descriptor(self):
        return self.name


class OrganisationIntelligenceDocument(Document):
    organisation = models.ForeignKey(Organisation, related_name='intelligence_documents', on_delete=models.CASCADE)
    _file = models.FileField(max_length=255, storage=private_storage)

    class Meta:
        app_label = 'wildlifecompliance'
        #verbose_name = 'CM_ProsecutionNoticeDocument'
        #verbose_name_plural = 'CM_ProsecutionNoticeDocuments'


@python_2_unicode_compatible
class OrganisationContact(models.Model):
    ORG_CONTACT_STATUS_DRAFT = 'draft'
    ORG_CONTACT_STATUS_PENDING = 'pending'
    ORG_CONTACT_STATUS_ACTIVE = 'active'
    ORG_CONTACT_STATUS_DECLINED = 'declined'
    ORG_CONTACT_STATUS_UNLINKED = 'unlinked'
    ORG_CONTACT_STATUS_SUSPENDED = 'suspended'
    USER_STATUS_CHOICES = (
        (ORG_CONTACT_STATUS_DRAFT, 'Draft'),
        (ORG_CONTACT_STATUS_PENDING, 'Pending'),
        (ORG_CONTACT_STATUS_ACTIVE, 'Active'),
        (ORG_CONTACT_STATUS_DECLINED, 'Declined'),
        (ORG_CONTACT_STATUS_UNLINKED, 'Unlinked'),
        (ORG_CONTACT_STATUS_SUSPENDED, 'Suspended')
    )
    ORG_CONTACT_ROLE_ADMIN = 'organisation_admin'
    ORG_CONTACT_ROLE_USER = 'organisation_user'
    ORG_CONTACT_ROLE_CONSULTANT = 'consultant'
    USER_ROLE_CHOICES = (
        (ORG_CONTACT_ROLE_ADMIN, 'Organisation Admin'),
        (ORG_CONTACT_ROLE_USER, 'Organisation User'),
        (ORG_CONTACT_ROLE_CONSULTANT, 'Consultant')
    )
    user_status = models.CharField(
        'Status',
        max_length=40,
        choices=USER_STATUS_CHOICES,
        default=ORG_CONTACT_STATUS_DRAFT)
    user_role = models.CharField(
        'Role',
        max_length=40,
        choices=USER_ROLE_CHOICES,
        default=ORG_CONTACT_ROLE_USER)
    organisation = models.ForeignKey(Organisation, related_name='contacts', on_delete=models.CASCADE)
    email = models.EmailField(blank=False)
    first_name = models.CharField(
        max_length=128,
        blank=False,
        verbose_name='Given name(s)')
    last_name = models.CharField(max_length=128, blank=False)
    phone_number = models.CharField(max_length=50, null=True, blank=True,
                                    verbose_name="phone number", help_text='')
    mobile_number = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="mobile number",
        help_text='')
    fax_number = models.CharField(max_length=50, null=True, blank=True,
                                  verbose_name="fax number", help_text='')
    is_admin = models.BooleanField(default=False)

    class Meta:
        app_label = 'wildlifecompliance'
        unique_together = (('organisation', 'email'),)

    def __str__(self):
        return get_full_name(self)

    @property
    def can_edit(self):
        """
        :return: True if the application is in one of the editable status.
        """
        return self.is_admin \
            and self.user_status == OrganisationContact.ORG_CONTACT_STATUS_ACTIVE \
            and self.user_role == OrganisationContact.ORG_CONTACT_ROLE_ADMIN

    @property
    def check_consultant(self):
        """
        :return: True if the application is in one of the editable status.
        """
        return self.user_status == OrganisationContact.ORG_CONTACT_STATUS_ACTIVE \
            and self.user_role == OrganisationContact.ORG_CONTACT_ROLE_CONSULTANT

    # def unlink_user(self,user,request):
    #     with transaction.atomic():
    #         try:
    #             delegate = UserDelegation.objects.get(organisation=self.organisation_id,user=user)
    #         except UserDelegation.DoesNotExist:
    #             raise ValidationError('This user is not a member of {}'.format(str(self.organisation_id)))

    #         # delete delegate
    #         delegate.delete()
    #         self.user_status ='unlinked'
    #         self.save()
    #         # org = Organisation.objects.get(id=self.organisation_id)
    #         # log linking
    #         # self.log_user_action(OrganisationContactAction.ACTION_UNLINK.format('{} {}({})'.format(user.first_name,user.last_name,user.email)),request)
    #         # send email
    #         send_organisation_unlink_email_notification(user,request.user,self,request)

    def log_user_action(self, action, request):
        return OrganisationContactAction.log_action(self, action, request.user)


class OrganisationContactAction(UserAction):
    ACTION_ORGANISATION_CONTACT_ACCEPT = "Accept request {}"
    ACTION_ORGANISATION_CONTACT_DECLINE = "Decline Request {}"
    ACTION_UNLINK = "Unlinked the user{}"

    @classmethod
    def log_action(cls, request, action, user):
        return cls.objects.create(
            request=request,
            who=user,
            what=str(action)
        )

    request = models.ForeignKey(
        OrganisationContact,
        related_name='action_logs', on_delete=models.CASCADE)

    class Meta:
        app_label = 'wildlifecompliance'
        ordering = ['-when']


class OrganisationContactDeclinedDetails(models.Model):
    request = models.ForeignKey(OrganisationContact, on_delete=models.CASCADE)
    officer = models.ForeignKey(EmailUser, null=False, on_delete=models.CASCADE)
    # reason = models.TextField(blank=True)

    class Meta:
        app_label = 'wildlifecompliance'


class UserDelegation(models.Model):
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    user = models.ForeignKey(EmailUser, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('organisation', 'user'),)
        app_label = 'wildlifecompliance'


class OrganisationAction(UserAction):
    ACTION_REQUEST_APPROVED = "Organisation Request {} Approved"
    ACTION_LINK = "Linked {}"
    ACTION_UNLINK = "Unlinked {}"
    ACTION_CONTACT_ADDED = "Added new contact {}"
    ACTION_CONTACT_DECLINED = "Declined contact {}"
    ACTION_MAKE_CONTACT_ADMIN = "Made contact Organisation Admin {}"
    ACTION_MAKE_CONTACT_USER = "Made contact Organisation User {}"
    ACTION_CONTACT_REMOVED = "Removed contact {}"
    ACTION_ORGANISATIONAL_DETAILS_SAVED_NOT_CHANGED = "Details saved without changes"
    ACTION_ORGANISATIONAL_DETAILS_SAVED_CHANGED = "Details saved with the following changes: \n{}"
    ACTION_ORGANISATIONAL_ADDRESS_DETAILS_SAVED_NOT_CHANGED = "Address Details saved without changes"
    ACTION_ORGANISATIONAL_ADDRESS_DETAILS_SAVED_CHANGED = "Addres Details saved with folowing changes: \n{}"
    ACTION_ORGANISATION_CONTACT_ACCEPT = "Accepted contact {}"
    ACTION_CONTACT_DECLINE = "Declined contact {}"
    ACTION_MAKE_CONTACT_SUSPEND = "Suspended contact {}"
    ACTION_MAKE_CONTACT_REINSTATE = "REINSTATED contact {}"
    ACTION_ID_UPDATE = "Organisation {} Identification Updated"

    organisation = models.ForeignKey(Organisation, related_name='action_logs', on_delete=models.CASCADE)

    class Meta:
        app_label = 'wildlifecompliance'
        ordering = ['-when']

    @classmethod
    def log_action(cls, organisation, action, user):
        return cls.objects.create(
            organisation=organisation,
            who=user,
            what=str(action)
        )


class OrganisationLogEntry(CommunicationsLogEntry):
    organisation = models.ForeignKey(Organisation, related_name='comms_logs', on_delete=models.CASCADE)

    def save(self, **kwargs):
        # save the request id if the reference not provided
        if not self.reference:
            self.reference = self.organisation.id
        super(OrganisationLogEntry, self).save(**kwargs)

    class Meta:
        app_label = 'wildlifecompliance'


class OrganisationRequest(models.Model):
    ORG_REQUEST_STATUS_WITH_ASSESSOR = 'with_assessor'
    ORG_REQUEST_STATUS_AMENDMENT_REQUESTED = 'amendment_requested'
    ORG_REQUEST_STATUS_APPROVED = 'approved'
    ORG_REQUEST_STATUS_DECLINED = 'declined'
    STATUS_CHOICES = (
        (ORG_REQUEST_STATUS_WITH_ASSESSOR, 'With Assessor'),
        (ORG_REQUEST_STATUS_AMENDMENT_REQUESTED, 'Amendment Requested'),
        (ORG_REQUEST_STATUS_APPROVED, 'Approved'),
        (ORG_REQUEST_STATUS_DECLINED, 'Declined')
    )
    ORG_REQUEST_ROLE_EMPLOYEE = 'employee'
    ORG_REQUEST_ROLE_CONSULTANT = 'consultant'
    ROLE_CHOICES = (
        (ORG_REQUEST_ROLE_EMPLOYEE, 'Employee'),
        (ORG_REQUEST_ROLE_CONSULTANT, 'Consultant')
    )
    name = models.CharField(max_length=128)
    abn = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='ABN')
    requester = models.ForeignKey(EmailUser, on_delete=models.CASCADE)
    assigned_officer = models.ForeignKey(
        EmailUser,
        blank=True,
        null=True,
        related_name='org_request_assignee', on_delete=models.CASCADE)
    identification = models.FileField(
        upload_to='wildlifecompliance/organisation/requests/%Y/%m/%d',
        null=True,
        blank=True,
        storage=private_storage)
    status = models.CharField(
        max_length=100,
        choices=STATUS_CHOICES,
        default=ORG_REQUEST_STATUS_WITH_ASSESSOR)
    role = models.CharField(
        max_length=100,
        choices=ROLE_CHOICES,
        default=ORG_REQUEST_ROLE_EMPLOYEE)
    lodgement_number = models.CharField(max_length=9, blank=True, default='')
    lodgement_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'wildlifecompliance'

    # Append 'OAR' to Application id to generate Lodgement number. Lodgement
    # number and lodgement sequence are used to generate Reference.
    def save(self, *args, **kwargs):
        super(OrganisationRequest, self).save(*args, **kwargs)
        if self.lodgement_number == '':
            new_lodgement_id = 'OAR{0:06d}'.format(self.pk)
            self.lodgement_number = new_lodgement_id
            self.save()

    def accept(self, request):
        with transaction.atomic():
            if is_wildlife_compliance_officer(request):
                self.status = OrganisationRequest.ORG_REQUEST_STATUS_APPROVED
                self.save()
                self.log_user_action(
                    OrganisationRequestUserAction.ACTION_ACCEPT_REQUEST.format(
                        self.id), request)
                # Continue with remaining logic
                self.__accept(request)

    def __accept(self, request):
        if is_wildlife_compliance_officer(request):
            from wildlifecompliance.components.applications.models import ActivityPermissionGroup

            # Check if orgsanisation exists in ledger
            ledger_org = None

            organisation_response = get_search_organisation(self.name, self.abn)
            response_status = organisation_response.get("status", None)

            if response_status == status.HTTP_404_NOT_FOUND:
                # Note: Do we want to create a new organisation here?
                raise NotImplementedError(
                    "Organisation does not exist in the ledger. Please create it first."
                )

            if response_status != status.HTTP_200_OK:
                raise ValidationError(
                    "Failed to retrieve organisation details from the ledger."
                )

            ledger_org = organisation_response.get("data", {})[0]

            # Create Organisation in wildlifecompliance
            org, created = Organisation.objects.get_or_create(
                organisation_id=ledger_org["organisation_id"])
            # org.generate_pins()
            # Link requester to organisation
            delegate, created = UserDelegation.objects.get_or_create(
                user=self.requester, organisation=org)
            
            # log who approved the request
            # org.log_user_action(OrganisationAction.ACTION_REQUEST_APPROVED.format(self.id),request)
            # log who created the link
            org.log_user_action(
                OrganisationAction.ACTION_LINK.format(
                    '{} {}({})'.format(
                        get_first_name(delegate.user),
                        get_last_name(delegate.user),
                        delegate.user.email)),
                request)

            if self.role == OrganisationRequest.ORG_REQUEST_ROLE_CONSULTANT:
                role = OrganisationContact.ORG_CONTACT_ROLE_CONSULTANT
            else:
                role = OrganisationContact.ORG_CONTACT_ROLE_ADMIN
            # Create contact person

            OrganisationContact.objects.get_or_create(
                organisation=org,
                first_name=get_first_name(self.requester),
                last_name=get_last_name(self.requester),
                mobile_number=self.requester.mobile_number,
                phone_number=self.requester.phone_number,
                fax_number=self.requester.fax_number,
                email=self.requester.email,
                user_role=role,
                user_status=OrganisationContact.ORG_CONTACT_STATUS_ACTIVE,
                is_admin=True
            )

            # send email to requester
            send_organisation_request_accept_email_notification(self, org, request)
            # Notify other Organisation Access Group members of acceptance.
            groups = ActivityPermissionGroup.objects.filter(
                permissions__codename='organisation_access_request'
            )
            for group in groups:
                recipients = [member.email for member in group.members.exclude(
                            email=request.user.email)]
                if recipients:
                    send_organisation_request_accept_admin_email_notification(
                        self, request, recipients)

    def amendment_request(self, request):
        with transaction.atomic():
            if is_wildlife_compliance_officer(request):
                self.status = OrganisationRequest.ORG_REQUEST_STATUS_AMENDMENT_REQUESTED
                self.save()
                self.log_user_action(
                    OrganisationRequestUserAction.ACTION_AMENDMENT_REQUEST.format(
                        self.id), request)
                # Continue with remaining logic
                self.__amendment_request(request)

    def __amendment_request(self, request):
        if is_wildlife_compliance_officer(request):
            # Check if orgsanisation exists in ledger
            ledger_org = None
            ledger_org = None

            organisation_response = get_search_organisation(self.name, self.abn)
            response_status = organisation_response.get("status", None)

            if response_status == status.HTTP_404_NOT_FOUND:
                # Note: Do we want to create a new organisation here?
                raise NotImplementedError(
                    "Organisation does not exist in the ledger. Please create it first."
                )

            if response_status != status.HTTP_200_OK:
                raise ValidationError(
                    "Failed to retrieve organisation details from the ledger."
                )

            ledger_org = organisation_response.get("data", {})[0]

            # Create Organisation in wildlifecompliance
            org, created = Organisation.objects.get_or_create(
                organisation_id=ledger_org["organisation_id"])
            # send email to original requester
            send_organisation_request_amendment_requested_email_notification(
                self, org, request)

    def reupload_identification_amendment_request(self, request):
        with transaction.atomic():
            if self.status == OrganisationRequest.ORG_REQUEST_STATUS_AMENDMENT_REQUESTED:
                self.status = OrganisationRequest.ORG_REQUEST_STATUS_WITH_ASSESSOR
                self.identification = request.data.dict()['identification']
                self.save()
                self.log_user_action(
                    OrganisationRequestUserAction.ACTION_REUPLOAD_IDENTIFICATION_AMENDMENT_REQUEST.format(
                        self.id), request)
                # Continue with remaining logic
                self.__reupload_identification_amendment_request(request)

    def __reupload_identification_amendment_request(self, request):
        # Check if orgsanisation exists in ledger
        ledger_org = None
        ledger_org = None

        organisation_response = get_search_organisation(self.name, self.abn)
        response_status = organisation_response.get("status", None)

        if response_status == status.HTTP_404_NOT_FOUND:
            # Note: Do we want to create a new organisation here?
            raise NotImplementedError(
                "Organisation does not exist in the ledger. Please create it first."
            )

        if response_status != status.HTTP_200_OK:
            raise ValidationError(
                "Failed to retrieve organisation details from the ledger."
            )

        ledger_org = organisation_response.get("data", {})[0]
        # Create Organisation in wildlifecompliance
        org = Organisation.objects.get(organisation_id=ledger_org["organisation_id"])
        # send email to original requester
        # TODO:
        # send_organisation_request_amendment_requested_email_notification(self,
        # org, request)

    def assign_officer(self, user, request):
        with transaction.atomic():
            if is_wildlife_compliance_officer(request):
                self.assigned_officer = user
                self.save()
                self.log_user_action(
                    OrganisationRequestUserAction.ACTION_ASSIGN_TO.format(
                        user.get_full_name()), request)

    def unassign_officer(self, request):
        with transaction.atomic():
            if is_wildlife_compliance_officer(request):
                self.assigned_officer = None
                self.save()
                self.log_user_action(
                    OrganisationRequestUserAction.ACTION_UNASSIGN, request)

    def decline(self, request):
        from wildlifecompliance.components.applications.models import ActivityPermissionGroup

        with transaction.atomic():
            if is_wildlife_compliance_officer(request):
                self.status = OrganisationRequest.ORG_REQUEST_STATUS_DECLINED
                self.save()
                OrganisationRequestDeclinedDetails.objects.create(
                    officer=request.user,
                    reason=OrganisationRequest.ORG_REQUEST_STATUS_DECLINED,
                    request=self
                )
                self.log_user_action(
                    OrganisationRequestUserAction.ACTION_DECLINE_REQUEST.format(
                        '{} {}({})'.format(
                            get_first_name(request.user),
                            get_last_name(request.user),
                            request.user.email)),
                    request)
                send_organisation_request_decline_email_notification(self, request)
                # Notify other members of organisation access group of decline.
                groups = ActivityPermissionGroup.objects.filter(
                    permissions__codename='organisation_access_request'
                )
                for group in groups:
                    recipients = [member.email for member in group.members.exclude(
                                email=request.user.email)]
                    if recipients:
                        send_organisation_request_decline_admin_email_notification(
                            self, request, recipients)

    def send_organisation_request_email_notification(self, request):
        from wildlifecompliance.components.applications.models import ActivityPermissionGroup

        # user submits a new organisation request
        # send email to organisation access group
        groups = ActivityPermissionGroup.objects.filter(
            permissions__codename='organisation_access_request'
        )
        for group in groups:
            org_access_recipients = [member.email for member in group.members]
            if org_access_recipients:
                send_organisation_request_email_notification(
                    self, request, org_access_recipients)

    def log_user_action(self, action, request):
        return OrganisationRequestUserAction.log_action(
            self, action, request.user)


class OrganisationRequestUserAction(UserAction):
    ACTION_LODGE_REQUEST = "Lodge request {}"
    ACTION_ASSIGN_TO = "Assign to {}"
    ACTION_UNASSIGN = "Unassign"
    ACTION_ACCEPT_REQUEST = "Accept request {}"
    ACTION_AMENDMENT_REQUEST = "Amendment request {}"
    ACTION_REUPLOAD_IDENTIFICATION_AMENDMENT_REQUEST = "Reupload identification amendment request {}"
    ACTION_DECLINE_REQUEST = "Decline request {}"
    # Assessors
    ACTION_CONCLUDE_REQUEST = "Conclude request {}"

    @classmethod
    def log_action(cls, request, action, user):
        return cls.objects.create(
            request=request,
            who=user,
            what=str(action)
        )

    request = models.ForeignKey(
        OrganisationRequest,
        related_name='action_logs', on_delete=models.CASCADE)

    class Meta:
        app_label = 'wildlifecompliance'
        ordering = ['-when']


class OrganisationRequestDeclinedDetails(models.Model):
    request = models.ForeignKey(OrganisationRequest, on_delete=models.CASCADE)
    officer = models.ForeignKey(EmailUser, null=False, on_delete=models.CASCADE)
    reason = models.TextField(blank=True)

    class Meta:
        app_label = 'wildlifecompliance'


class OrganisationRequestLogEntry(CommunicationsLogEntry):
    request = models.ForeignKey(OrganisationRequest, related_name='comms_logs', on_delete=models.CASCADE)

    def save(self, **kwargs):
        # save the request id if the reference not provided
        if not self.reference:
            self.reference = self.request.id
        super(OrganisationRequestLogEntry, self).save(**kwargs)

    class Meta:
        app_label = 'wildlifecompliance'
        ordering = ['-created']

'''
NOTE: REGISTER MODELS FOR REVERSION HERE.
'''
import reversion
#reversion.register(Organisation)
#reversion.register(OrganisationAction)
#reversion.register(OrganisationContact)
#reversion.register(OrganisationContactAction)
#reversion.register(OrganisationContactDeclinedDetails)
#reversion.register(OrganisationLogEntry)
#reversion.register(OrganisationRequest)
#reversion.register(OrganisationRequestDeclinedDetails)
#reversion.register(OrganisationRequestLogEntry)
#reversion.register(OrganisationRequestUserAction)

reversion.register(Organisation, follow=['intelligence_documents', 'contacts', 'userdelegation_set', 'action_logs', 'comms_logs', 'organisation_inspected', 'org_applications', 'offender_organisation'])
reversion.register(OrganisationIntelligenceDocument, follow=[])
reversion.register(OrganisationContact, follow=['action_logs', 'organisationcontactdeclineddetails_set'])
reversion.register(OrganisationContactAction, follow=[])
reversion.register(OrganisationContactDeclinedDetails, follow=[])
reversion.register(UserDelegation, follow=[])
reversion.register(OrganisationAction, follow=[])
reversion.register(OrganisationLogEntry, follow=[])
reversion.register(OrganisationRequest, follow=['action_logs', 'organisationrequestdeclineddetails_set', 'comms_logs'])
reversion.register(OrganisationRequestUserAction, follow=[])
reversion.register(OrganisationRequestDeclinedDetails, follow=[])
reversion.register(OrganisationRequestLogEntry, follow=[])

