# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('castle', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='old_auth',
            field=models.BinaryField(max_length=64, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='profile',
            name='old_salt',
            field=models.BigIntegerField(default=0, null=True, blank=True),
            preserve_default=True,
        ),
    ]
