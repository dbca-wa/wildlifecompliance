# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2020-01-20 01:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0390_remove_temporarydocument_input_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='legalcase',
            name='statement_of_facts',
            field=models.TextField(blank=True, null=True),
        ),
    ]
