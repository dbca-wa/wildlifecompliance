# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2020-08-29 09:00
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0511_auto_20200825_1220'),
    ]

    operations = [
        migrations.AddField(
            model_name='applicationselectedactivitypurpose',
            name='purpose_species_json',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default={}, null=True),
        ),
    ]
