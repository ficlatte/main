# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('castle', '0027_blog_bbcode'),
    ]

    operations = [
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('blog', models.ForeignKey(related_name='subscriptions', blank=True, to='castle.Blog', null=True)),
                ('story', models.ForeignKey(related_name='subscriptions', blank=True, to='castle.Story', null=True)),
                ('user', models.ForeignKey(to='castle.Profile')),
            ],
        ),
    ]
