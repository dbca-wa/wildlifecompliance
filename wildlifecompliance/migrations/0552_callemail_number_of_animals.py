# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-11-19 06:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0551_auto_20211118_1158'),
    ]

    operations = [
        migrations.AddField(
            model_name='callemail',
            name='number_of_animals',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
