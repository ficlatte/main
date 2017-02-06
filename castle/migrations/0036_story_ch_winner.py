# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('castle', '0035_auto_20170208_1944'),
    ]

    operations = [
        migrations.AddField(
            model_name='story',
            name='ch_winner',
            field=models.FloatField(default=0.0, null=True),
        ),
    ]
