# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2022-06-01 03:38
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        #('accounts', '0034_auto_20220601_1138'),
        ('wildlifecompliance', '0600_remove_region_head_office'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='compliancepermissiongroup',
            name='district',
        ),
        migrations.RemoveField(
            model_name='compliancepermissiongroup',
            name='group_ptr',
        ),
        migrations.RemoveField(
            model_name='compliancepermissiongroup',
            name='region',
        ),
        migrations.RemoveField(
            model_name='callemail',
            name='allocated_group',
        ),
        migrations.RemoveField(
            model_name='inspection',
            name='allocated_group',
        ),
        migrations.RemoveField(
            model_name='legalcase',
            name='allocated_group',
        ),
        migrations.RemoveField(
            model_name='offence',
            name='allocated_group',
        ),
        migrations.RemoveField(
            model_name='sanctionoutcome',
            name='allocated_group',
        ),
        migrations.DeleteModel(
            name='CompliancePermissionGroup',
        ),
    ]
