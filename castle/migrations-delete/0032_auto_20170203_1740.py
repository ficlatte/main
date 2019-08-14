# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('castle', '0031_auto_20170203_1635'),
    ]

    operations = [
        migrations.AlterField(
            model_name='challenge',
            name='body',
            field=models.CharField(max_length=1024),
        ),
    ]
