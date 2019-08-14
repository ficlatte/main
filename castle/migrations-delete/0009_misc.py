# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('castle', '0008_auto_20150413_0810'),
    ]

    operations = [
        migrations.CreateModel(
            name='Misc',
            fields=[
                ('key', models.CharField(max_length=32, serialize=False, primary_key=True)),
                ('s_val', models.CharField(max_length=128, null=True, blank=True)),
                ('i_val', models.BigIntegerField(null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
