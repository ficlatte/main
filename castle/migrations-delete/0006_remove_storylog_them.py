# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('castle', '0005_auto_20150412_0750'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='storylog',
            name='them',
        ),
    ]
