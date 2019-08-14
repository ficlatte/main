# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('castle', '0013_auto_20150414_1514'),
    ]

    operations = [
        migrations.AddField(
            model_name='blog',
            name='ptime',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
