# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('castle', '0010_auto_20150413_0852'),
    ]

    operations = [
        migrations.AddField(
            model_name='storylog',
            name='ctime',
            field=models.DateTimeField(default=datetime.datetime.now),
            preserve_default=True,
        ),
    ]
