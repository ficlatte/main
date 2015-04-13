# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('castle', '0009_misc'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='site_name',
            field=models.CharField(max_length=1024, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='profile',
            name='site_url',
            field=models.URLField(max_length=254, null=True, blank=True),
            preserve_default=True,
        ),
    ]
