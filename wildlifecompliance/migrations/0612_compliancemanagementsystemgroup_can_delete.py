# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2022-06-14 07:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0611_compliancemanagementsystemgroup_compliancemanagementsystemgrouppermission'),
    ]

    operations = [
        migrations.AddField(
            model_name='compliancemanagementsystemgroup',
            name='can_delete',
            field=models.BooleanField(default=True),
        ),
    ]
