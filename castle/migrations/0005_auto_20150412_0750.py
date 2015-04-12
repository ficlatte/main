# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('castle', '0004_auto_20150412_0739'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blog',
            name='user',
            field=models.ForeignKey(to='castle.Profile'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='comment',
            name='author',
            field=models.ForeignKey(related_name='comments_received', to='castle.Profile'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='comment',
            name='user',
            field=models.ForeignKey(related_name='comments_made', to='castle.Profile'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='profile',
            name='friends',
            field=models.ManyToManyField(related_name='friend_set', null=True, to='castle.Profile', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='prompt',
            name='user',
            field=models.ForeignKey(to='castle.Profile'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rating',
            name='user',
            field=models.ForeignKey(to='castle.Profile'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='story',
            name='user',
            field=models.ForeignKey(to='castle.Profile'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='storylog',
            name='them',
            field=models.ForeignKey(related_name='activity_set', to='castle.Profile'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='storylog',
            name='user',
            field=models.ForeignKey(to='castle.Profile'),
            preserve_default=True,
        ),
    ]
