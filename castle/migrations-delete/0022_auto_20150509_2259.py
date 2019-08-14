# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('castle', '0021_auto_20150419_2039'),
    ]

    operations = [
        migrations.AlterField(
            model_name='story',
            name='activity',
            field=models.FloatField(default=0.0, null=True),
            preserve_default=True,
        ),
    ]
