# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-02-23 03:13
from __future__ import unicode_literals

from django.db import migrations, models
import wildlifecompliance.components.main.models


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0535_auto_20210218_0748'),
    ]

    operations = [
        migrations.CreateModel(
            name='SanctionOutcomeWordTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_file', models.FileField(max_length=255, upload_to=wildlifecompliance.components.main.models.update_sanction_outcome_word_filename)),
                ('uploaded_date', models.DateTimeField(auto_now_add=True)),
                ('description', models.TextField(blank=True, verbose_name='description')),
            ],
            options={
                'verbose_name_plural': 'Wildlife Compliance Templates',
                'ordering': ['-id'],
            },
        ),
    ]
