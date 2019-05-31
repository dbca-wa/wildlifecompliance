# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2019-05-30 10:00
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0212_auto_20190530_1754'),
    ]

    operations = [
        migrations.AlterField(
            model_name='complianceworkflowdocument',
            name='workflow',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='wildlifecompliance.ComplianceWorkflowLogEntry'),
        ),
    ]
