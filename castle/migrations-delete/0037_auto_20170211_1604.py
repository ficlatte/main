# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('castle', '0036_story_ch_winner'),
    ]

    operations = [
        migrations.AlterField(
            model_name='story',
            name='body',
            field=models.CharField(max_length=2048),
        ),
    ]
