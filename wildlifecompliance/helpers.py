from __future__ import unicode_literals

import logging

from rest_framework import serializers
from ledger_api_client.ledger_models import EmailUserRO as EmailUser
from wildlifecompliance import settings
from wildlifecompliance.components.applications.models import ActivityPermissionGroup
from wildlifecompliance.components.users.models import ComplianceManagementUserPreferences

from wildlifecompliance.components.main.models import WildlifeSystemGroup, WildlifeSystemGroupUser

from confy import env
from django.db.models import Q

DEBUG = env('DEBUG', False)
BASIC_AUTH = env('BASIC_AUTH', False)

logger = logging.getLogger(__name__)

def user_has_perm(user,perm):
    
    if not user or not perm:
        return False

    if user.is_superuser:
        return True
    
    groups_with_perm = WildlifeSystemGroup.objects.filter(permissions__codename=perm)
    groups_with_user = WildlifeSystemGroup.objects.filter(id__in=WildlifeSystemGroupUser.objects.filter(emailuser_id=user.id).values_list('group_id',flat=True))

    common_groups = groups_with_perm & groups_with_user
    return common_groups.exists()

def belongs_to(user, group_name):
    """
    Check if the user belongs to the given group.
    :param user:
    :param group_name:
    :return:
    """
    group = WildlifeSystemGroup.objects.filter(name=group_name)
    if group.exists():
        return user.id in list(WildlifeSystemGroupUser.objects.filter(group_id=group.first().id).values_list('emailuser_id', flat=True))
    else:
        return False


def belongs_to_list(user, group_names):
    """
    Check if the user belongs to the given list of groups.
    :param user:
    :param list_of_group_names:
    :return:
    """
    groups = WildlifeSystemGroup.objects.filter(name__in=group_names)
    return user.id in list(WildlifeSystemGroupUser.objects.filter(group_id__in=list(groups.values_list('id',flat=True))).values_list('emailuser_id', flat=True))


def is_wildlifecompliance_admin(request):
    return request.user.is_authenticated and \
           (
               user_has_perm(request.user, 'wildlifecompliance.system_administrator') or
               request.user.is_superuser or
               is_cm_compliance_admin(request) or
               is_cm_licensing_admin(request)
           )


def is_wildlifecompliance_payment_officer(request):
    wildlife_compliance_user = user_has_perm(request.user, 'wildlifecompliance.system_administrator') or request.user.is_superuser

    try:
        if request.user.is_authenticated and (
                WildlifeSystemGroup.objects.get(name=settings.GROUP_WILDLIFE_COMPLIANCE_PAYMENT_OFFICERS).wildlifesystemgroupuser_set.filter(emailuser_id=request.user.id)
            ):
            wildlife_compliance_user = True
    except:
        logging.error(f"{settings.GROUP_WILDLIFE_COMPLIANCE_PAYMENT_OFFICERS} does not exist in WildlifeSystemGroup. Payment officers cannot be authorised until group added to WildlifeSystemGroup or settings.GROUP_WILDLIFE_COMPLIANCE_PAYMENT_OFFICERS corrected.")

    return wildlife_compliance_user


def is_reception(request):
    '''
    A check whether request is performed by Wildlife Licensing Reception.
    '''
    from wildlifecompliance.components.licences.models import (
            WildlifeLicenceReceptionEmail,
    )

    is_reception_email = WildlifeLicenceReceptionEmail.objects.filter(
        email=request.user.email
    ).exists()

    return request.user.is_authenticated and is_reception_email

def is_customer(request):
    return request.user.is_authenticated and not is_internal(request)


def is_internal(request):
    if DEBUG and BASIC_AUTH:
        return True
    else:
        return (
            request.user.is_superuser or
            is_wildlifecompliance_admin(request) or
            is_compliance_internal_user(request) or
            is_officer(request) or
            is_wildlife_compliance_officer(request) or
            is_wildlifecompliance_payment_officer(request)
        )


def is_officer(request):
    licence_officer_groups = [group.name for group in ActivityPermissionGroup.objects.filter(
            permissions__codename__in=['wildlifecompliance.organisation_access_request',
                                       'wildlifecompliance.licensing_officer',
                                       'wildlifecompliance.issuing_officer',
                                       'wildlifecompliance.assessor',
                                       'wildlifecompliance.return_curator',
                                       'wildlifecompliance.payment_officer'])]
    licence_officer_groups = []
    return (request.user.is_authenticated 
        and (belongs_to_list(request.user, licence_officer_groups) 
        or request.user.is_superuser))

def is_external_url(request):
    external = False
    if request.path[:10] == '/external/':
        external = True
    return external

def is_internal_url(request):
    internal = False
    if request.path[:10] == '/internal/':
        internal = True
    return internal

def prefer_compliance_management(request=None):
    return settings.COMPLIANCE_APP

def is_wildlife_compliance_officer(request):
    wildlife_compliance_user = user_has_perm(request.user, 'wildlifecompliance.system_administrator') or request.user.is_superuser

    try:
        if request.user.is_authenticated and (
                WildlifeSystemGroup.objects.get(name=settings.GROUP_WILDLIFE_COMPLIANCE_OFFICERS).wildlifesystemgroupuser_set.filter(emailuser_id=request.user.id)
            ):
            wildlife_compliance_user = True
    except:
        logging.error(f"{settings.GROUP_WILDLIFE_COMPLIANCE_OFFICERS} does not exist in WildlifeSystemGroup. Wildlife compliance officers cannot be authorised until group added to WildlifeSystemGroup or settings.GROUP_WILDLIFE_COMPLIANCE_OFFICERS corrected.")

    return wildlife_compliance_user

def is_compliance_management_user(request):

    compliance_user = is_wildlifecompliance_admin(request)
    if request.user.is_authenticated and (
            is_compliance_management_readonly_user(request) or 
            is_compliance_management_callemail_readonly_user(request) or
            is_compliance_management_approved_external_user(request) or
            is_compliance_management_volunteer(request) or
            is_compliance_internal_user(request) 
            ):
        compliance_user = True
    return compliance_user


def is_compliance_internal_user(request):
    compliance_user = is_wildlifecompliance_admin(request)
    if request.user.is_authenticated and (
            is_compliance_management_officer(request) or 
            is_compliance_management_manager(request) or
            is_compliance_management_infringement_notice_coordinator(request) or
            is_cm_compliance_admin(request) or
            is_cm_licensing_admin(request) or
            is_compliance_management_inspection_officer(request) or
            is_compliance_management_prosecution_officer(request)
            ):
        compliance_user = True
    return compliance_user

def is_compliance_management_readonly_user(request):
    return request.user.is_authenticated and request.user.compliancemanagementsystemgrouppermission_set.filter(group__name=settings.GROUP_COMPLIANCE_MANAGEMENT_READ_ONLY).exists()

def is_compliance_management_callemail_readonly_user(request):
    return request.user.is_authenticated and request.user.compliancemanagementsystemgrouppermission_set.filter(group__name=settings.GROUP_COMPLIANCE_MANAGEMENT_CALL_EMAIL_READ_ONLY).exists()

def is_compliance_management_approved_external_user(request):
    return request.user.is_authenticated and request.user.compliancemanagementsystemgrouppermission_set.filter(group__name=settings.GROUP_COMPLIANCE_MANAGEMENT_APPROVED_EXTERNAL_USER).exists()

def is_compliance_management_volunteer(request):
    return request.user.is_authenticated and request.user.compliancemanagementsystemgrouppermission_set.filter(group__name=settings.GROUP_VOLUNTEER).exists()

def is_compliance_management_officer(request):
    return request.user.is_authenticated and request.user.compliancemanagementsystemgrouppermission_set.filter(group__name=settings.GROUP_OFFICER).exists()

def is_compliance_management_inspection_officer(request):
    return request.user.is_authenticated and request.user.compliancemanagementsystemgrouppermission_set.filter(group__name=settings.GROUP_INSPECTION_OFFICER).exists()

def is_compliance_management_prosecution_officer(request):
    return request.user.is_authenticated and \
    request.user.compliancemanagementsystemgrouppermission_set \
        .filter(Q(group__name=settings.GROUP_PROSECUTION_COORDINATOR) |
                Q(group__name=settings.GROUP_PROSECUTION_MANAGER) |
                Q(group__name=settings.GROUP_PROSECUTION_COUNCIL)).exists()

def is_compliance_management_manager(request):
    return request.user.is_authenticated and request.user.compliancemanagementsystemgrouppermission_set.filter(group__name=settings.GROUP_MANAGER).exists()

def is_compliance_management_infringement_notice_coordinator(request):
    return request.user.is_authenticated and request.user.compliancemanagementsystemgrouppermission_set.filter(group__name=settings.GROUP_INFRINGEMENT_NOTICE_COORDINATOR).exists()

def is_cm_compliance_admin(request):
    return request.user.is_authenticated and request.user.compliancemanagementsystemgrouppermission_set.filter(group__name=settings.GROUP_COMPLIANCE_ADMIN).exists()

def is_cm_licensing_admin(request):
    return request.user.is_authenticated and request.user.compliancemanagementsystemgrouppermission_set.filter(group__name=settings.GROUP_LICENSING_ADMIN).exists()

def is_able_to_view_sanction_outcome_pdf(request):
    return request.user.is_authenticated if (
        is_compliance_management_officer(request) or
        is_compliance_management_manager(request) or
        is_compliance_management_infringement_notice_coordinator(request)
        ) else False

def is_in_organisation_contacts(request, organisation):
    return request.user.email in organisation.contacts.all().values_list('email', flat=True)


def is_authorised_to_modify(request, instance):
    authorised = True
                
    # Can only modify if Open (not overdue, submitted, accepted).
    if instance.status not in ['open', 'overdue']:
        raise serializers.ValidationError('The status of this application means it cannot be modified: {}'
                                          .format(instance.status))

    # Submitter must be the offence holder.
    offender = instance.sanction_outcome.offender.person.email #TODO organisation to be handled later
    submitter = request.user.email
    authorised &= offender == submitter

    if not authorised:
        raise serializers.ValidationError('You are not authorised to modify this application.')