# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2019-06-24 07:20
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0182_auto_20190624_1458'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='return',
            name='text',
        ),
        migrations.AlterField(
            model_name='return',
            name='application',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='returns_application', to='wildlifecompliance.Application'),
        ),
        migrations.AlterField(
            model_name='return',
            name='assigned_to',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='returns_curator', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='return',
            name='licence',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='returns_licence', to='wildlifecompliance.WildlifeLicence'),
        ),
        migrations.AlterField(
            model_name='return',
            name='submitter',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='returns_submitter', to=settings.AUTH_USER_MODEL),
        ),
    ]
