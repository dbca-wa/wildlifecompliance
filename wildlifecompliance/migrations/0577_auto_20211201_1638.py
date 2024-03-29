# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-12-01 08:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0576_auto_20211130_0944'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wildcarespeciessubtype',
            name='species_sub_name',
            field=models.CharField(choices=[('corella', 'Corella'), ('red_tailed_black', 'Red-tailed Black'), ('white_tailed_black', 'White-tailed Black'), ('swamphen', 'Swamphen'), ('darter', 'Darter'), ('goshawk', 'Goshawk'), ('osprey', 'Osprey'), ('kestrel', 'Kestrel'), ('peregrine', 'Peregrine'), ('wedge_tailed', 'Wedge-tailed'), ('white_bellied_sea', 'White-bellied Sea'), ('egret', 'Egret'), ('nankeen_night', 'Nankeen Night'), ('new_holland', 'New Holland'), ('wattlebird', 'Wattlebird'), ('blue_winged_kookaburra', 'Blue-winged Kookaburra'), ('laughing_kookaburra', 'Laughing Kookaburra'), ('sacred', 'Sacred'), ('barn', 'Barn'), ('bookbook', 'Bookbook'), ('28_australian_ringneck', '28 - Australian Ringneck'), ('cockatiel', 'Cockatiel'), ('galah_pink_and_grey', 'Galah - Pink and Grey'), ('rosella', 'Rosella'), ('little', 'Little'), ('welcome', 'Welcome'), ('tammar_wallaby', 'Tammar-Wallaby'), ('western_brush_wallaby', 'Western Brush Wallaby'), ('western_grey', 'Western Grey'), ('brushtail', 'Brushtail'), ('pygmy', 'Pygmy'), ('ringtail', 'Ringtail'), ('blue_tongue_bobtail', 'Blue Tongue, Bobtail'), ('goanna', 'Goanna'), ('monitor', 'Monitor'), ('skink', 'Skink'), ('dugite', 'Dugite'), ('python', 'Python'), ('tiger', 'Tiger'), ('long_necked_oblanga', 'Long-necked (oblanga)'), ('marine', 'Marine'), ('western_swamp', 'Western Swamp')], max_length=100),
        ),
    ]
