# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('castle', '0014_blog_ptime'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='profile',
            options={'permissions': ('post_blog', 'User can make blog posts')},
        ),
    ]
