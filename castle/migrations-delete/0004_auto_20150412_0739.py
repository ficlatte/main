# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('castle', '0003_auto_20150412_0737'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='stored',
            field=models.ForeignKey(blank=True, to='castle.Story', null=True),
            preserve_default=True,
        ),
    ]
