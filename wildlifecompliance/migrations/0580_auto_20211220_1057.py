# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-12-20 02:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0579_auto_20211220_0950'),
    ]

    operations = [
        migrations.AlterField(
            model_name='callemail',
            name='dead',
            field=models.CharField(blank=True, max_length=5, null=True),
        ),
        migrations.AlterField(
            model_name='callemail',
            name='euthanise',
            field=models.CharField(blank=True, max_length=5, null=True),
        ),
    ]
