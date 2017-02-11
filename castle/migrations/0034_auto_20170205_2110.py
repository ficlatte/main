# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('castle', '0033_auto_20170203_1808'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='challenge',
            field=models.ForeignKey(blank=True, to='castle.Challenge', null=True),
        ),
        migrations.AddField(
            model_name='comment',
            name='prompt',
            field=models.ForeignKey(blank=True, to='castle.Prompt', null=True),
        ),
    ]
