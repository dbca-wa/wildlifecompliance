# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2022-02-14 06:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0588_auto_20220214_1404'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wildcarespeciessubtype',
            name='species_sub_name',
            field=models.CharField(max_length=100, unique=True),
        ),
    ]
