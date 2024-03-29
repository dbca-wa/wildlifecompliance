# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2022-06-22 06:07
from __future__ import unicode_literals

from django.db import migrations, models
import multiselectfield.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0617_callemail_allocated_group'),
    ]

    operations = [
        migrations.AddField(
            model_name='compliancemanagementsystemgroup',
            name='group_email',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='callemail',
            name='age',
            field=multiselectfield.db.fields.MultiSelectField(blank=True, choices=[('baby', 'Baby'), ('juvenile', 'Juvenile'), ('adult', 'Adult')], max_length=30, null=True),
        ),
    ]
