# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('castle', '0012_auto_20150413_1431'),
    ]

    operations = [
        migrations.AlterField(
            model_name='story',
            name='prequel_to',
            field=models.ForeignKey(related_name='prequels', blank=True, to='castle.Story', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='story',
            name='sequel_to',
            field=models.ForeignKey(related_name='sequels', blank=True, to='castle.Story', null=True),
            preserve_default=True,
        ),
    ]
