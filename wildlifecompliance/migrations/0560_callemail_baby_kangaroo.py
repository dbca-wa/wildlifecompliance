# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-11-24 08:07
from __future__ import unicode_literals

from django.db import migrations
import multiselectfield.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0559_auto_20211124_1537'),
    ]

    operations = [
        migrations.AddField(
            model_name='callemail',
            name='baby_kangaroo',
            field=multiselectfield.db.fields.MultiSelectField(blank=True, choices=[('pinky', 'Pinky'), ('joey', 'Joey')], max_length=30, null=True),
        ),
    ]
