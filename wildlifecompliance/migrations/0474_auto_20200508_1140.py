# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2020-05-08 03:40
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0473_auto_20200428_1024'),
    ]

    operations = [
        migrations.AddField(
            model_name='applicationselectedactivitypurpose',
            name='expiry_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='applicationselectedactivitypurpose',
            name='issue_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='applicationselectedactivitypurpose',
            name='original_issue_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='applicationselectedactivitypurpose',
            name='start_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]