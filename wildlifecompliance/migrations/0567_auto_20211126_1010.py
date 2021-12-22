# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-11-26 02:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0566_auto_20211125_1640'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wildcarespeciestype',
            name='species_name',
            field=models.CharField(choices=[('cane_toad', 'Cane Toad'), ('frog', 'Frog'), ('butcherbird', 'Butcherbird'), ('cockatoo', 'Cockatoo'), ('coot', 'Coot'), ('cormorant', 'Cormorant'), ('duck', 'Duck'), ('eagle_falcon_hawk', 'Eagle, Falcon, Hawk'), ('emu', 'Emu'), ('goose', 'Goose'), ('heron', 'Heron'), ('honeyeater', 'Honeyeater'), ('ibis', 'Ibis'), ('kingfisher', 'Kingfisher'), ('magpie', 'Magpie'), ('magpie_lark', 'Magpie-Lark'), ('owl', 'Owl'), ('parrot', 'Parrot'), ('peacock', 'Peacock'), ('penguin', 'Penguin'), ('quail', 'Quail'), ('rainbow_bee_eater', 'Rainbow Bee-Eater'), ('rainbow_lorikeet', 'Rainbow Lorikeet'), ('raven', 'Raven'), ('albatross', 'Albatross'), ('gull', 'Gull'), ('pelican', 'Pelican'), ('shearwater', 'Shearwater'), ('tern', 'tern'), ('swallow', 'Swallow'), ('swan', 'Swan'), ('tawny_frogmouth', 'Tawny Frogmouth'), ('willy_wagtail', 'Willy Wagtail'), ('snake', 'Snake')], max_length=100),
        ),
    ]