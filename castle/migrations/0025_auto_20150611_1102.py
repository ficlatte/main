# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('castle', '0024_auto_20150517_2208'),
    ]

    operations = [
        migrations.AlterField(
            model_name='storylog',
            name='story',
            field=models.ForeignKey(blank=True, to='castle.Story', null=True),
            preserve_default=True,
        ),
    ]
