# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2022-02-17 02:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0589_auto_20220214_1424'),
    ]

    operations = [
        migrations.AddField(
            model_name='calltype',
            name='index',
            field=models.SmallIntegerField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='wildcarespeciestype',
            name='check_pinky_joe',
            field=models.BooleanField(default=False),
        ),
    ]
