# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-11-25 04:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0562_auto_20211125_1212'),
    ]

    operations = [
        migrations.AlterField(
            model_name='callemail',
            name='brief_nature_of_call',
            field=models.TextField(blank=True),
        ),
    ]