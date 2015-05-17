# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('castle', '0023_auto_20150514_0934'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='friends',
            field=models.ManyToManyField(related_name='followers', to='castle.Profile'),
            preserve_default=True,
        ),
    ]
