# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-02-23 04:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0536_sanctionoutcomewordtemplate'),
    ]

    operations = [
        migrations.AddField(
            model_name='sanctionoutcomewordtemplate',
            name='act',
            field=models.CharField(blank=True, choices=[('BCA', 'Biodiversity Conservation Act 2016'), ('CALM', 'Conservation and Land Management Act 1984')], max_length=30),
        ),
        migrations.AddField(
            model_name='sanctionoutcomewordtemplate',
            name='sanction_outcome_type',
            field=models.CharField(blank=True, choices=[('infringement_notice', 'Infringement Notice'), ('caution_notice', 'Caution Notice'), ('letter_of_advice', 'Letter of Advice'), ('remediation_notice', 'Remediation Notice')], max_length=30),
        ),
    ]
