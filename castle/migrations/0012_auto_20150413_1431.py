# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('castle', '0011_storylog_ctime'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='blog',
            name='published',
        ),
        migrations.RemoveField(
            model_name='story',
            name='published',
        ),
    ]
