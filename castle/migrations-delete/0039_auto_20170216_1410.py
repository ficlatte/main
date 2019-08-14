# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('castle', '0038_remove_story_ch_winner'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='pen_name_uc',
            field=models.CharField(unique=True, max_length=64),
        ),
    ]
