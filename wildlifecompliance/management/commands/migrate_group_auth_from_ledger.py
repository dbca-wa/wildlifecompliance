from django.core.management.base import BaseCommand
from django.db import transaction

import logging
logger = logging.getLogger(__name__)

from django.contrib.auth.models import Permission, Group
from ledger_api_client.ledger_models import UsersInGroup
from wildlifecompliance.components.main.models import WildlifeSystemPermission, WildlifeSystemGroup, WildlifeSystemGroupUser

def get_wlc_ledger_permissions(wlc_ledger_groups):
    logger.info("Getting all wildlifecompliance permissions from ledger")

    #only get permissions used by groups
    group_id_lists = list(map(lambda group: group.permissions.values_list('id', flat=True), wlc_ledger_groups))
    group_id_list = list(set([id for id_list in group_id_lists for id in id_list]))

    return Permission.objects.filter(id__in=group_id_list)

def create_wlc_permissions(wlc_ledger_permissions):
    logger.info("Creating wildlifecompliance permissions")

    wlc_ledger_permissions_id_map = {}

    for permission in wlc_ledger_permissions:
        #concat content type app label with codename for new codename
        codename = f"{permission.content_type.app_label}.{permission.codename}" if permission.content_type else permission.codename
        name = permission.name
        ledger_id = permission.id

        new_permission = WildlifeSystemPermission.objects.create(name=name,codename=codename)
        new_id = new_permission.id

        wlc_ledger_permissions_id_map[ledger_id] = new_id
        
    return wlc_ledger_permissions_id_map

def get_wlc_ledger_groups():
    logger.info("Getting all wildlifecompliance groups from ledger")
    return Group.objects.filter(name__icontains="wildlife compliance")

def create_wlc_groups(wlc_ledger_permissions_id_map, wlc_ledger_groups):
    logger.info("Creating wildlifecompliance groups")

    wlc_ledger_group_id_map = {}

    for group in wlc_ledger_groups:
        name = group.name
        ledger_id = group.id

        ledger_permission_ids = list(group.permissions.values_list('id', flat=True))
        wlc_permission_ids = list(map(lambda id: wlc_ledger_permissions_id_map[id], ledger_permission_ids))
        
        new_group = WildlifeSystemGroup.objects.create(name=name)
        new_group.permissions.add(*wlc_permission_ids)
        new_id = new_group.id

        wlc_ledger_group_id_map[ledger_id] = new_id

    return wlc_ledger_group_id_map

def get_ledger_user_group_memberships(wlc_ledger_groups):
    logger.info("Getting all user group memberships from ledger")
    return UsersInGroup.objects.filter(group_id__in=wlc_ledger_groups.values_list('id',flat=True))

def create_wlc_user_group_memberships(wlc_ledger_group_id_map, ledger_user_group_memberships):
    logger.info("Creating user group memberships")

    for membership in ledger_user_group_memberships:
        emailuser_id = membership.emailuser_id
        group_id = wlc_ledger_group_id_map[membership.group_id]
        WildlifeSystemGroupUser.objects.create(group_id=group_id,emailuser_id=emailuser_id)
    print(WildlifeSystemGroupUser.objects.count())

class Command(BaseCommand):
    help = 'Migrate Auth Group Membership, Groups, and Group Permissions from Ledger'

    def handle(self, *args, **options):
        try:    
            with transaction.atomic():
            
                logger.info('Running command {}'.format(__name__))
            
                check = input(
"""

WARNING: You are about to copy all groups, permissions, and group memberships from Ledger.

This should only ever be done once during initial set up of a new segregated WLC instance.

Doing this at a later date may override required authorisation group membership or restore previously removed authorisations.

Improper use of this command may lead to privelege escalation and/or denial of service.

Are you sure you want to continue? (y/n): """
            )

                if check.lower() != 'y':
                    print("\nMigration cancelled.\n")
                    logger.info('Command {} cancelled'.format(__name__))
                    return

                #get groups
                wlc_ledger_groups = get_wlc_ledger_groups()
                #get permissions
                wlc_ledger_permissions = get_wlc_ledger_permissions(wlc_ledger_groups)

                #create groups and permissions
                wlc_ledger_permissions_id_map = create_wlc_permissions(wlc_ledger_permissions)
                wlc_ledger_group_id_map = create_wlc_groups(wlc_ledger_permissions_id_map, wlc_ledger_groups)

                #then user membership
                ledger_user_group_memberships = get_ledger_user_group_memberships(wlc_ledger_groups)
                create_wlc_user_group_memberships(wlc_ledger_group_id_map, ledger_user_group_memberships)

                #FOR TESTING
                #raise RuntimeError("force rollback")

                logger.info('Command {} finished'.format(__name__))

        except Exception as e:
            logger.error('Error command {0} : {1}'.format(__name__, e))

