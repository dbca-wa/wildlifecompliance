# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2019-12-18 08:04
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0350_auto_20191217_1534'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='artifact',
            name='custodian',
        ),
    ]
