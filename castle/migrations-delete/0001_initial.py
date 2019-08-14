# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Blog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=256)),
                ('body', models.CharField(max_length=20480)),
                ('draft', models.BooleanField(default=False)),
                ('published', models.BooleanField(default=False)),
                ('ctime', models.DateTimeField(default=datetime.datetime.now)),
                ('mtime', models.DateTimeField(default=datetime.datetime.now)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('body', models.CharField(max_length=1024)),
                ('ctime', models.DateTimeField(default=datetime.datetime.now)),
                ('mtime', models.DateTimeField(default=datetime.datetime.now)),
                ('author', models.ForeignKey(related_name='comments_received', to=settings.AUTH_USER_MODEL)),
                ('blog', models.ForeignKey(blank=True, to='castle.Blog', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pen_name', models.CharField(max_length=64)),
                ('pen_name_uc', models.CharField(max_length=64)),
                ('site_url', models.URLField(max_length=254)),
                ('site_name', models.CharField(max_length=1024)),
                ('biography', models.CharField(max_length=1024)),
                ('mature', models.BooleanField(default=False)),
                ('email_addr', models.EmailField(max_length=254)),
                ('email_flags', models.IntegerField(default=0)),
                ('email_auth', models.BigIntegerField(default=0)),
                ('email_time', models.DateTimeField(null=True, blank=True)),
                ('old_auth', models.BinaryField(max_length=64)),
                ('old_salt', models.BigIntegerField(default=0)),
                ('prefs', models.IntegerField(default=0)),
                ('flags', models.IntegerField(default=0)),
                ('ctime', models.DateTimeField(default=datetime.datetime.now)),
                ('mtime', models.DateTimeField(default=datetime.datetime.now)),
                ('atime', models.DateTimeField(default=datetime.datetime.now)),
                ('friends', models.ManyToManyField(related_name='friend_set', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Prompt',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=128)),
                ('body', models.CharField(max_length=256)),
                ('mature', models.BooleanField(default=False)),
                ('activity', models.FloatField(default=0.0)),
                ('ctime', models.DateTimeField(default=datetime.datetime.now)),
                ('mtime', models.DateTimeField(default=datetime.datetime.now)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Rating',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('rating', models.IntegerField(null=True, blank=True)),
                ('ctime', models.DateTimeField(default=datetime.datetime.now)),
                ('mtime', models.DateTimeField(default=datetime.datetime.now)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SiteLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ip', models.GenericIPAddressField()),
                ('url', models.URLField(max_length=254)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Story',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=256)),
                ('body', models.CharField(max_length=1536)),
                ('mature', models.BooleanField(default=False)),
                ('draft', models.BooleanField(default=False)),
                ('ficly', models.BooleanField(default=False)),
                ('published', models.BooleanField(default=False)),
                ('activity', models.FloatField(default=0.0)),
                ('prompt_text', models.CharField(max_length=256, null=True, blank=True)),
                ('ctime', models.DateTimeField(default=datetime.datetime.now)),
                ('mtime', models.DateTimeField(default=datetime.datetime.now)),
                ('ptime', models.DateTimeField(null=True, blank=True)),
                ('ftime', models.DateTimeField(null=True, blank=True)),
                ('prequel_to', models.ForeignKey(related_name='sequels', blank=True, to='castle.Story', null=True)),
                ('prompt', models.ForeignKey(blank=True, to='castle.Prompt', null=True)),
                ('sequel_to', models.ForeignKey(related_name='prequels', blank=True, to='castle.Story', null=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StoryLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('log_type', models.IntegerField(default=1, choices=[(0, b'wrote'), (1, b'viewed'), (2, b'rated'), (3, b'commented on'), (4, b'wrote a prequel to'), (5, b'wrote a sequel to')])),
                ('comment', models.ForeignKey(blank=True, to='castle.Comment', null=True)),
                ('quel', models.ForeignKey(related_name='activity_quel_set', blank=True, to='castle.Story', null=True)),
                ('story', models.ForeignKey(to='castle.Story')),
                ('them', models.ForeignKey(related_name='activity_set', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('tag', models.CharField(max_length=64)),
                ('story', models.ForeignKey(to='castle.Story')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='tag',
            unique_together=set([('story', 'tag')]),
        ),
        migrations.AddField(
            model_name='rating',
            name='story',
            field=models.ForeignKey(to='castle.Story'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='rating',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='rating',
            unique_together=set([('user', 'story')]),
        ),
        migrations.AddField(
            model_name='profile',
            name='stored',
            field=models.ForeignKey(to='castle.Story'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='profile',
            name='user',
            field=models.OneToOneField(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='comment',
            name='story',
            field=models.ForeignKey(blank=True, to='castle.Story', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='comment',
            name='user',
            field=models.ForeignKey(related_name='comments_made', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
