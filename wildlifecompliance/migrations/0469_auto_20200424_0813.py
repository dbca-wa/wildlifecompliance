# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2020-04-24 00:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0468_licenceinspection'),
    ]

    operations = [
        migrations.AlterField(
            model_name='applicationselectedactivitypurpose',
            name='processing_status',
            field=models.CharField(choices=[('selected', 'Selected for Proposal'), ('propose', 'Proposed for Issue'), ('decline', 'Declined'), ('issue', 'Issued')], default='propose', max_length=40, verbose_name='Processing Status'),
        ),
    ]
