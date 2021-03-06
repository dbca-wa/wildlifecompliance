# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2019-04-24 05:20
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import wildlifecompliance.components.call_email.models


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0171_compliancedocument_version_comment'),
    ]

    operations = [
        migrations.CreateModel(
            name='ComplianceLogDocument',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=100, verbose_name='name')),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('uploaded_date', models.DateTimeField(auto_now_add=True)),
                ('_file', models.FileField(upload_to=wildlifecompliance.components.call_email.models.update_compliance_comms_log_filename)),
            ],
        ),
        migrations.CreateModel(
            name='ComplianceLogEntry',
            fields=[
                ('communicationslogentry_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wildlifecompliance.CommunicationsLogEntry')),
                ('call_email', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comms_logs', to='wildlifecompliance.CallEmail')),
            ],
            bases=('wildlifecompliance.communicationslogentry',),
        ),
        migrations.AddField(
            model_name='compliancelogdocument',
            name='log_entry',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='wildlifecompliance.ComplianceLogEntry'),
        ),
    ]
