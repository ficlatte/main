# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('castle', '0032_auto_20170203_1740'),
    ]

    operations = [
        migrations.AlterField(
            model_name='challenge',
            name='etime',
            field=models.DateField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='challenge',
            name='stime',
            field=models.DateField(default=django.utils.timezone.now),
        ),
    ]
