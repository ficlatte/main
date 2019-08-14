# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('castle', '0026_auto_20150703_1810'),
    ]

    operations = [
        migrations.AddField(
            model_name='blog',
            name='bbcode',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
