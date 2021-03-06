# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2020-10-16 05:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0522_licencepurpose_regulation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='application',
            name='customer_status',
            field=models.CharField(choices=[('draft', 'Draft'), ('awaiting_payment', 'Awaiting Payment'), ('under_review', 'Under Review'), ('amendment_required', 'Draft'), ('accepted', 'Approved'), ('partially_approved', 'Partially Approved'), ('declined', 'Declined')], default='draft', max_length=40, verbose_name='Customer Status'),
        ),
    ]
