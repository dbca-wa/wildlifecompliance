# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2019-05-30 07:55
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import wildlifecompliance.components.call_email.models


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0205_auto_20190528_1517'),
    ]

    operations = [
        migrations.CreateModel(
            name='ComplianceWorkflowDocument',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=100, verbose_name='name')),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('uploaded_date', models.DateTimeField(auto_now_add=True)),
                ('_file', models.FileField(upload_to=wildlifecompliance.components.call_email.models.update_compliance_workflow_log_filename)),
                ('input_name', models.CharField(blank=True, max_length=255, null=True)),
                ('can_delete', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='ComplianceWorkflowLogEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('details', models.TextField(blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('call_email', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='workflow_logs', to='wildlifecompliance.CallEmail')),
                ('district', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='callemail_district', to='wildlifecompliance.RegionDistrict')),
                ('region', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='callemail_region', to='wildlifecompliance.RegionDistrict')),
            ],
        ),
        migrations.AddField(
            model_name='complianceworkflowdocument',
            name='log_entry',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='wildlifecompliance.ComplianceWorkflowLogEntry'),
        ),
    ]
