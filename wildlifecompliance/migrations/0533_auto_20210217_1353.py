# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-02-17 05:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0532_auto_20210217_1340'),
    ]

    operations = [
        migrations.AddField(
            model_name='act',
            name='acronym',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='act',
            name='name',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
