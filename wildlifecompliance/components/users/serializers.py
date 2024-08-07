import os
from django.conf import settings
from ledger.accounts.models import EmailUser, Address, Profile, EmailIdentity, EmailUserAction, Document, PrivateDocument
from wildlifecompliance.components.organisations.models import (
    Organisation,
    OrganisationRequest,
    OrganisationContact
)
from wildlifecompliance.components.users.models import (
        #CompliancePermissionGroup, 
        ComplianceManagementUserPreferences
        )
from wildlifecompliance.components.organisations.utils import can_admin_org, is_consultant
from wildlifecompliance.helpers import (
    is_customer,
    is_internal,
    is_reception,
    is_wildlifecompliance_payment_officer,
    is_new_to_wildlifelicensing,
    is_compliance_management_user,
    is_compliance_management_approved_external_user,
)
from rest_framework import serializers
from django.core.exceptions import ValidationError
from rest_framework.fields import CurrentUserDefault
from django.contrib.auth.models import Permission

from wildlifecompliance.components.main.utils import (
    get_full_name,
    get_dob,
    get_first_name,
    get_last_name,
)

class DocumentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Document
        fields = ('id', 'description', 'file', 'name', 'uploaded_date')


class IdentificationSerializer(DocumentSerializer):
    '''
    Serializer to obfuscate the file name and description from identification.
    '''

    class Meta:
        model = Document
        fields = ('id', 'uploaded_date')

class Identification2Serializer(DocumentSerializer):
    '''
    Serializer to obfuscate the file name and description from identification.
    '''

    class Meta:
        model = PrivateDocument
        fields = ('id', 'created')


class UpdateComplianceManagementUserPreferencesSerializer(serializers.ModelSerializer):
    email_user_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)

    class Meta:
        model = ComplianceManagementUserPreferences
        fields = (
               'email_user_id',
               'prefer_compliance_management'
               )


class UserOrganisationContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganisationContact
        fields = (
            'user_status',
            'user_role',
            'email',
        )


class UserOrganisationSerializer(serializers.ModelSerializer):
    # Serializer for an Organisation linked with a User
    name = serializers.CharField(source='organisation.name')
    abn = serializers.CharField(source='organisation.abn')
    email = serializers.SerializerMethodField()
    is_consultant = serializers.SerializerMethodField(read_only=True)
    is_admin = serializers.SerializerMethodField(read_only=True)

    class Meta():
        model = Organisation
        fields = (
            'id',
            'name',
            'abn',
            'email',
            'is_consultant',
            'is_admin'
        )

    def get_is_admin(self, obj):
        user = EmailUser.objects.get(id=self.context.get('user_id'))
        return can_admin_org(obj, user)

    def get_is_consultant(self, obj):
        user = EmailUser.objects.get(id=self.context.get('user_id'))
        return is_consultant(obj, user)

    def get_email(self, obj):
        email = EmailUser.objects.get(id=self.context.get('user_id')).email
        return email


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailUser
        fields = (
            'id',
            'email',
            'phone_number',
            'mobile_number',
        )

    def validate(self, obj):
        if not obj.get('phone_number') and not obj.get('mobile_number'):
            raise serializers.ValidationError(
                'You must provide a mobile/phone number')
        return obj


class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = (
            'id',
            'line1',
            'line2',
            'line3',
            'locality',
            'state',
            'country',
            'postcode',
        )


class UserProfileSerializer(serializers.ModelSerializer):
    postal_address = UserAddressSerializer()

    class Meta:
        model = Profile
        fields = (
            'id',
            'user',
            'name',
            'email',
            'institution',
            'postal_address'
        )

    def create(self, validated_data):
        profile = Profile()
        profile.user = validated_data['user']
        profile.name = validated_data['name']
        profile.email = validated_data['email']
        profile.institution = validated_data.get('institution', '')
        postal_address_data = validated_data.pop('postal_address')
        if profile.email:
            if EmailIdentity.objects.filter(
                    email=profile.email).exclude(
                    user=profile.user).exists():
                # Email already used by other user in email identity.
                raise ValidationError(
                    "This email address is already associated with an existing account or profile.")
        new_postal_address, address_created = Address.objects.get_or_create(
            user=profile.user, **postal_address_data)
        profile.postal_address = new_postal_address
        setattr(profile, "auth_identity", True)
        profile.save()
        return profile

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.email = validated_data.get('email', instance.email)
        instance.institution = validated_data.get(
            'institution', instance.institution)
        postal_address_data = validated_data.pop('postal_address')
        if instance.email:
            if EmailIdentity.objects.filter(
                    email=instance.email).exclude(
                    user=instance.user).exists():
                # Email already used by other user in email identity.
                raise ValidationError(
                    "This email address is already associated with an existing account or profile.")
        postal_address, address_created = Address.objects.get_or_create(
            user=instance.user, **postal_address_data)
        instance.postal_address = postal_address
        setattr(instance, "auth_identity", True)
        instance.save()
        return instance

class ComplianceManagementSaveUserAddressSerializer(serializers.ModelSerializer):
    #user_id = serializers.IntegerField(
    #    required=False, write_only=True, allow_null=True)
    line1 = serializers.CharField(allow_blank=True)  # We need allow_blank=True otherwise blank is not allowed by blank=False setting in the model
    postcode = serializers.CharField(allow_blank=True)  # We need allow_blank=True otherwise blank is not allowed by blank=False setting in the model
    locality = serializers.CharField(allow_blank=True)  # We need allow_blank=True otherwise blank is not allowed by blank=False setting in the model
    country = serializers.CharField(allow_blank=True)  # We need allow_blank=True otherwise blank is not allowed by blank=False setting in the model
    user_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)

    class Meta:
        model = Address
        fields = (
            'id',
            'line1',
            #'line2',
            #'line3',
            'locality',
            'state',
            'country',
            'postcode',
            'user_id',
        )
        read_only_fields = ('id', )


class ComplianceManagementSaveUserSerializer(serializers.ModelSerializer):
    residential_address_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)

    class Meta:
        model = EmailUser
        fields = (
            'id',
            'last_name',
            'first_name',
            'dob',
            'email',
            'residential_address_id',
            'phone_number',
            'mobile_number',
        )
        read_only_fields = ('id',)


class ComplianceManagementUserSerializer(serializers.ModelSerializer):
    #residential_address = UserAddressSerializer(required=False)
    residential_address = ComplianceManagementSaveUserAddressSerializer(
            required=False,
            read_only=True)
    dob = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()

    class Meta:
        model = EmailUser
        fields = (
            'id',
            'last_name',
            'first_name',
            'dob',
            'email',
            'residential_address',
            'residential_address_id',
            'phone_number',
            'mobile_number',
        )
        #read_only_fields = ('id',)

    def get_dob(self, obj):
        formatted_date = get_dob(obj)
        return formatted_date.strftime(
            '%d/%m/%Y'
        ) if formatted_date else None
    
    def get_first_name(self, obj):
        return get_first_name(obj)
    
    def get_last_name(self, obj):
        return get_last_name(obj)


class UserSerializer(serializers.ModelSerializer):
    residential_address = UserAddressSerializer()
    personal_details = serializers.SerializerMethodField()
    address_details = serializers.SerializerMethodField()
    contact_details = serializers.SerializerMethodField()
    wildlifecompliance_organisations = serializers.SerializerMethodField()
    # identification = IdentificationSerializer()
    identification2 = Identification2Serializer()
    dob = serializers.SerializerMethodField()
    legal_dob = serializers.SerializerMethodField()
    acc_mgmt_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = EmailUser
        fields = (
            'title',
            'id',
            'last_name',
            'first_name',
            'legal_last_name',
            'legal_first_name',
            'dob',
            'legal_dob',
            'email',
            'identification2',
            'residential_address',
            'phone_number',
            'mobile_number',
            'fax_number',
            'character_flagged',
            'character_comments',
            'wildlifecompliance_organisations',
            'personal_details',
            'address_details',
            'contact_details',
            'acc_mgmt_url',
        )

    def get_dob(self, obj):
        formatted_date = obj.dob.strftime(
            '%d/%m/%Y'
        ) if obj.dob else None

        return formatted_date
    
    def get_legal_dob(self, obj):
        formatted_date = obj.legal_dob.strftime(
            '%d/%m/%Y'
        ) if obj.legal_dob else None

        return formatted_date

    def get_personal_details(self, obj):
        return True if obj.last_name and obj.first_name and (obj.dob or obj.legal_dob) else False

    def get_address_details(self, obj):
        return True if obj.residential_address else False

    def get_contact_details(self, obj):
        if obj.mobile_number and obj.email:
            return True
        elif obj.phone_number and obj.email:
            return True
        elif obj.mobile_number and obj.phone_number:
            return True
        else:
            return False

    def get_wildlifecompliance_organisations(self, obj):
        wildlifecompliance_organisations = obj.wildlifecompliance_organisations
        serialized_orgs = UserOrganisationSerializer(
            wildlifecompliance_organisations, many=True, context={
                'user_id': obj.id}).data
        return serialized_orgs
    
    def get_acc_mgmt_url(self,obj):
        request = self.context.get('request')
        if settings.LEDGER_UI_URL and request and is_internal(request):
            return settings.LEDGER_UI_URL + "/ledger/account-management/" + str(obj.id) + "/change/"
        return ''


class FirstTimeUserSerializer(UserSerializer):
    '''
    Specialised UserSerializer with flag for minimal details provided check for 
    first-time user.
    '''
    has_complete_first_time = serializers.SerializerMethodField(read_only=True)
    prefer_compliance_management = serializers.SerializerMethodField(read_only=True)
    is_compliance_management_approved_external_user = serializers.SerializerMethodField(read_only=True)
    sso_setting_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = EmailUser
        fields = (
            'title',
            'id',
            'last_name',
            'first_name',
            'dob',
            'legal_last_name',
            'legal_first_name',
            'legal_dob',
            'email',
            'identification',
            'residential_address',
            'phone_number',
            'mobile_number',
            'fax_number',
            'character_flagged',
            'character_comments',
            'wildlifecompliance_organisations',
            'personal_details',
            'address_details',
            'contact_details',
            'has_complete_first_time',
            'prefer_compliance_management',
            'is_compliance_management_approved_external_user',
            'sso_setting_url',
        )

    def get_has_complete_first_time(self, obj):
        '''
        Verify request user has completed adding reqired details for first time
        usage.
        '''
        is_completed = False

        request = self.context.get('request')

        if is_internal(request):
            is_completed = True
        else:
            is_completed = not is_new_to_wildlifelicensing(request)

        return is_completed

    def get_prefer_compliance_management(self, obj):
        if ComplianceManagementUserPreferences.objects.filter(email_user_id=obj.id):
            return obj.compliancemanagementuserpreferences.prefer_compliance_management
        return False

    def get_is_compliance_management_approved_external_user(self, obj):
        return is_compliance_management_approved_external_user(self.context.get('request'))

    def get_sso_setting_url(self, obj):
        return settings.SSO_SETTING_URL

class DTUserSerializer(serializers.ModelSerializer):

    dob = serializers.SerializerMethodField(read_only=True)
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()

    class Meta:
        model = EmailUser
        fields = (
            'title',
            'id',
            'last_name',
            'first_name',
            'dob',
            'email',
            'phone_number',
            'mobile_number',
            'fax_number',
            'character_flagged',
            'character_comments',
        )
        # the serverSide functionality of datatables is such that only columns that have field 'data'
        # defined are requested from the serializer. Use datatables_always_serialize to force render
        # of fields that are not listed as 'data' in the datatable columns
        datatables_always_serialize = fields

    def get_dob(self, obj):
        formatted_date = get_dob(obj)
        return formatted_date.strftime(
            '%d/%m/%Y'
        ) if formatted_date else None
    
    def get_first_name(self, obj):
        return get_first_name(obj)
    
    def get_last_name(self, obj):
        return get_last_name(obj)


class MyUserDetailsSerializer(serializers.ModelSerializer):
    residential_address = UserAddressSerializer()
    personal_details = serializers.SerializerMethodField()
    address_details = serializers.SerializerMethodField()
    contact_details = serializers.SerializerMethodField()
    wildlifecompliance_organisations = serializers.SerializerMethodField()
    #identification = IdentificationSerializer()
    identification2 = Identification2Serializer()
    is_customer = serializers.SerializerMethodField()
    is_internal = serializers.SerializerMethodField()
    prefer_compliance_management = serializers.SerializerMethodField()
    is_compliance_management_user = serializers.SerializerMethodField()
    is_compliance_management_approved_external_user = serializers.SerializerMethodField()
    is_reception = serializers.SerializerMethodField()
    dob = serializers.SerializerMethodField(read_only=True)
    legal_dob = serializers.SerializerMethodField(read_only=True)
    is_payment_officer = serializers.SerializerMethodField(read_only=True)
    has_complete_first_time = serializers.SerializerMethodField(read_only=True)
    sso_setting_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = EmailUser
        fields = (
            'title',
            'id',
            'last_name',
            'first_name',
            'dob',
            'legal_last_name',
            'legal_first_name',
            'legal_dob',
            'email',
            # 'identification',
            'identification2',
            'residential_address',
            'phone_number',
            'mobile_number',
            'fax_number',
            'wildlifecompliance_organisations',
            'personal_details',
            'address_details',
            'contact_details',
            'is_customer',
            'is_internal',
            'prefer_compliance_management',
            'is_reception',
            'is_payment_officer',
            'has_complete_first_time',
            'is_compliance_management_user',
            'is_compliance_management_approved_external_user',
            'sso_setting_url',
        )

    def get_has_complete_first_time(self, obj):
        '''
        Verify request user has completed adding reqired details for first time
        usage.
        '''
        is_completed = False

        request = self.context.get('request')

        if is_internal(request):
            is_completed = True
        else:
            is_completed = not is_new_to_wildlifelicensing(request)

        return is_completed

    def get_is_payment_officer(self, obj):
        is_officer = is_wildlifecompliance_payment_officer(
            self.context.get('request')
        )
        return is_officer

    def get_dob(self, obj):
        formatted_date = obj.dob.strftime(
            '%d/%m/%Y'
        ) if obj.dob else None

        return formatted_date
    
    def get_legal_dob(self, obj):
        formatted_date = obj.legal_dob.strftime(
            '%d/%m/%Y'
        ) if obj.legal_dob else None

        return formatted_date

    def get_personal_details(self, obj):
        return True if obj.last_name and obj.first_name and (obj.dob or obj.legal_dob)  else False

    def get_address_details(self, obj):
        return True if obj.residential_address else False

    def get_contact_details(self, obj):
        if obj.mobile_number and obj.email:
            return True
        elif obj.phone_number and obj.email:
            return True
        elif obj.mobile_number and obj.phone_number:
            return True
        else:
            return False

    def get_wildlifecompliance_organisations(self, obj):
        wildlifecompliance_organisations = obj.wildlifecompliance_organisations
        serialized_orgs = UserOrganisationSerializer(
            wildlifecompliance_organisations, many=True, context={
                'user_id': obj.id}).data
        return serialized_orgs

    def get_is_customer(self, obj):
        return is_customer(self.context.get('request'))

    def get_is_internal(self, obj):
        return is_internal(self.context.get('request'))

    def get_is_compliance_management_approved_external_user(self, obj):
        return is_compliance_management_approved_external_user(self.context.get('request'))

    def get_is_compliance_management_user(self, obj):
        return is_compliance_management_user(self.context.get('request'))

    def get_prefer_compliance_management(self, obj):
        if ComplianceManagementUserPreferences.objects.filter(email_user_id=obj.id):
            return obj.compliancemanagementuserpreferences.prefer_compliance_management
        return False

    def get_is_reception(self, obj):
        return is_reception(self.context.get('request'))
    
    def get_sso_setting_url(self, obj):
        return settings.SSO_SETTING_URL

class ComplianceUserDetailsSerializer(serializers.ModelSerializer):
    residential_address = UserAddressSerializer()
    personal_details = serializers.SerializerMethodField()
    address_details = serializers.SerializerMethodField()
    contact_details = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    # compliance_permissions = serializers.SerializerMethodField()
    dob = serializers.SerializerMethodField(read_only=True)
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()

    class Meta:
        model = EmailUser
        fields = (
            'title',
            'id',
            'last_name',
            'first_name',
            'full_name',
            'dob',
            'email',
            'residential_address',
            'phone_number',
            'mobile_number',
            'fax_number',
            # 'compliance_permissions',
            'personal_details',
            'address_details',
            'contact_details'
        )

    def get_full_name(self, obj):
        #return True if obj.last_name and obj.first_name and obj.dob else False
        return get_full_name(obj)
    
    def get_dob(self, obj):
        formatted_date = get_dob(obj)
        return formatted_date.strftime(
            '%d/%m/%Y'
        ) if formatted_date else None
    
    def get_first_name(self, obj):
        return get_first_name(obj)
    
    def get_last_name(self, obj):
        return get_last_name(obj)

    def get_personal_details(self, obj):
        return True if obj.last_name and obj.first_name and (obj.dob or obj.legal_dob)  else False

    def get_address_details(self, obj):
        return True if obj.residential_address else False

    def get_contact_details(self, obj):
        if obj.mobile_number and obj.email:
            return True
        elif obj.phone_number and obj.email:
            return True
        elif obj.mobile_number and obj.phone_number:
            return True
        else:
            return False

    # def get_wildlifecompliance_organisations(self, obj):
    #     wildlifecompliance_organisations = obj.wildlifecompliance_organisations
    #     serialized_orgs = UserOrganisationSerializer(
    #         wildlifecompliance_organisations, many=True, context={
    #             'user_id': obj.id}).data
    #     return serialized_orgs


class ComplianceUserDetailsOptimisedSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()

    class Meta:
        model = EmailUser
        fields = (
            'title',
            'id',
            'last_name',
            'first_name',
            'email',
            'full_name',
        )
    
    def get_full_name(self, obj):
        return get_full_name(obj)
    
    def get_first_name(self, obj):
        return get_first_name(obj)
    
    def get_last_name(self, obj):
        return get_last_name(obj)


class EmailUserActionSerializer(serializers.ModelSerializer):
    who = serializers.CharField(source='who.get_full_name')

    class Meta:
        model = EmailUserAction
        fields = '__all__'


class PersonalSerializer(serializers.ModelSerializer):
    dob = serializers.DateField(
        input_formats=['%d/%m/%Y'],
        required=False,
        allow_null=True
    )

    class Meta:
        model = EmailUser
        fields = (
            'id',
            #'last_name',
            #'first_name',
            'dob',
        )


class EmailIdentitySerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = EmailIdentity
        fields = (
            'user',
            'email'
        )


#class RegionDistrictSerializer(serializers.ModelSerializer):
#    # region = RegionDistrictSerializer(many=True)
#
#    class Meta:
#        model = RegionDistrict
#        fields = (
#            'id',
#            'district',
#            'region',
#            'display_name',
#            'districts'
#        )


#class CompliancePermissionGroupSerializer(serializers.ModelSerializer):
#
#    class Meta:
#        model = CompliancePermissionGroup
#        fields = (
#            'id',
#            'name',
#            'region_id',
#            'district_id',
#            'display_name',
#            )
#
#
#class CompliancePermissionGroupMembersSerializer(serializers.ModelSerializer):
#    members = ComplianceUserDetailsOptimisedSerializer(many=True)
#
#    class Meta:
#        model = CompliancePermissionGroup
#        fields = (
#            'members',
#            )


class PermissionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Permission
        fields = (
            'codename',
        )
        read_only_fields = (
            'codename',
        )


#class CompliancePermissionGroupDetailedSerializer(serializers.ModelSerializer):
#    #region_district = RegionDistrictSerializer(many=True)
#    members = ComplianceUserDetailsOptimisedSerializer(many=True)
#    # permissions = PermissionSerializer(many=True)
#    permissions_list = serializers.SerializerMethodField(read_only=True)
#
#    class Meta:
#        model = CompliancePermissionGroup
#        fields = (
#            'id',
#            'name',
#            #'region_district',
#            'region_id', 
#            'district_id',
#            'display_name',
#            'members',
#            # 'permissions',
#            'permissions_list',
#            )
#
#    def get_permissions_list(self, obj):
#        permissions_list = []
#        for permission in obj.permissions.all():
#            permissions_list.append(permission.codename)
#        return permissions_list
