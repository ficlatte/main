# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('castle', '0016_auto_20150416_1554'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='old_auth',
            field=models.CharField(max_length=32, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='profile',
            name='old_salt',
            field=models.CharField(max_length=16, null=True, blank=True),
            preserve_default=True,
        ),
    ]
