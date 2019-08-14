# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('castle', '0019_auto_20150419_1557'),
    ]

    operations = [
        migrations.AddField(
            model_name='storylog',
            name='prompt',
            field=models.ForeignKey(blank=True, to='castle.Prompt', null=True),
            preserve_default=True,
        ),
    ]
