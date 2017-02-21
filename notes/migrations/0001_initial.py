# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('castle', '0041_auto_20170216_1415'),
    ]

    operations = [
        migrations.CreateModel(
            name='Note',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('subject', models.CharField(max_length=140)),
                ('body', models.CharField(max_length=2048)),
                ('sent_date', models.DateTimeField(null=True, blank=True)),
                ('read_date', models.DateTimeField(null=True, blank=True)),
                ('replied_date', models.DateTimeField(null=True, blank=True)),
                ('sender_deleted_date', models.DateTimeField(null=True, blank=True)),
                ('recipient_deleted_date', models.DateTimeField(null=True, blank=True)),
                ('parent_msg', models.ForeignKey(related_name='parent', blank=True, to='notes.Note', null=True)),
                ('recipient', models.ForeignKey(related_name='recipient', to='castle.Profile')),
                ('sender', models.ForeignKey(related_name='sender', to='castle.Profile')),
                ('user', models.ForeignKey(to='castle.Profile')),
            ],
            options={
                'ordering': ['-sent_date'],
            },
        ),
    ]
