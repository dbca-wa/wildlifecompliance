# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2020-08-25 04:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0510_auto_20200825_1149'),
    ]

    operations = [
        migrations.AddField(
            model_name='applicationselectedactivitypurpose',
            name='additional_fee',
            field=models.DecimalField(decimal_places=2, default='0', max_digits=8),
        ),
        migrations.AddField(
            model_name='applicationselectedactivitypurpose',
            name='additional_fee_text',
            field=models.TextField(blank=True, null=True),
        ),
    ]
