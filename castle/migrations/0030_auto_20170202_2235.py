# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('castle', '0029_challenge'),
    ]

    operations = [
        migrations.AddField(
            model_name='story',
            name='challenge',
            field=models.ForeignKey(blank=True, to='castle.Challenge', null=True),
        ),
        migrations.AddField(
            model_name='storylog',
            name='challenge',
            field=models.ForeignKey(blank=True, to='castle.Challenge', null=True),
        ),
        migrations.AlterField(
            model_name='challenge',
            name='winner',
            field=models.ForeignKey(related_name='winner', to='castle.Story', null=True),
        ),
        migrations.AlterField(
            model_name='storylog',
            name='log_type',
            field=models.IntegerField(default=1, choices=[(0, 'wrote'), (1, 'viewed'), (2, 'rated'), (3, 'commented on'), (4, 'wrote a prequel to'), (5, 'wrote a sequel to'), (10, 'created challenge'), (7, 'updated story'), (8, 'wrote prompt'), (9, 'updated prompt'), (10, 'created a challenge'), (11, 'updated a challenge')]),
        ),
    ]
