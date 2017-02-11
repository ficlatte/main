# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('castle', '0028_subscription'),
    ]

    operations = [
        migrations.CreateModel(
            name='Challenge',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=128)),
                ('body', models.CharField(max_length=1536)),
                ('mature', models.BooleanField(default=False)),
                ('activity', models.FloatField(default=0.0)),
                ('ctime', models.DateTimeField(default=django.utils.timezone.now)),
                ('mtime', models.DateTimeField(default=django.utils.timezone.now)),
                ('stime', models.DateTimeField(default=django.utils.timezone.now)),
                ('etime', models.DateTimeField(default=django.utils.timezone.now)),
                ('user', models.ForeignKey(to='castle.Profile')),
                ('winner', models.ForeignKey(related_name='winner', to='castle.Story')),
            ],
        ),
    ]
