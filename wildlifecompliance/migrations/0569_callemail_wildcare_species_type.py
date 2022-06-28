# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-11-26 06:47
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0568_merge_20211126_1052'),
    ]

    operations = [
        migrations.AddField(
            model_name='callemail',
            name='wildcare_species_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='wildcare_species_type', to='wildlifecompliance.WildcareSpeciesType'),
        ),
    ]
