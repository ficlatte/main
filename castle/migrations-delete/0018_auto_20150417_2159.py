# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('castle', '0017_auto_20150417_2126'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='old_auth',
            field=models.CharField(max_length=64, null=True, blank=True),
            preserve_default=True,
        ),
    ]
