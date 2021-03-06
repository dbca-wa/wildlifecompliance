# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2019-03-26 05:28
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0151_remove_application_processing_status'),
    ]

    operations = [
        migrations.RenameField(
            model_name='returntype',
            old_name='return_type',
            new_name='data_format',
        ),
        migrations.AddField(
            model_name='returntype',
            name='description',
            field=models.TextField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='returntype',
            name='replaced_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='wildlifecompliance.ReturnType'),
        ),
        migrations.AddField(
            model_name='returntype',
            name='version',
            field=models.SmallIntegerField(default=1),
        ),
        migrations.AlterUniqueTogether(
            name='returntype',
            unique_together=set([('Name', 'version')]),
        ),
    ]
