# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2019-07-17 02:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0256_inspection_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inspection',
            name='party_inspected',
            field=models.CharField(choices=[('individual', 'individual'), ('organisation', 'organisation')], default='individual', max_length=30),
        ),
    ]
