
#coding: utf-8
#This file is part of Ficlatté.
#Copyright (C) 2015 Paul Robertson
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of version 3 of the GNU Affero General Public
#    License as published by the Free Software Foundation
#    
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime

# Create your models here.

# Extra user data
class Profile(models.Model):
    user        = models.OneToOneField(User)
    friends     = models.ManyToManyField('self', symmetrical=False, related_name='followers')
    pen_name    = models.CharField(max_length=64)
    pen_name_uc = models.CharField(max_length=64)
    site_url    = models.URLField(max_length=254, blank=True, null=True)
    site_name   = models.CharField(max_length=1024, blank=True, null=True)
    biography   = models.CharField(max_length=1024)
    mature      = models.BooleanField(default=False)
    email_addr  = models.EmailField(max_length=254)
    email_flags = models.IntegerField(default=0)
    email_auth  = models.BigIntegerField(default=0)
    email_time  = models.DateTimeField(blank=True, null=True)
    old_auth    = models.CharField(max_length=64, blank=True, null=True)     # DEPRECATED pass sha256 val
    old_salt    = models.CharField(max_length=16, blank=True, null=True)     # DEPRECATED pass salt
    prefs       = models.IntegerField(default=0)
    flags       = models.IntegerField(default=0)
    stored      = models.ForeignKey('Story', blank=True, null=True)            # User can make a note of a story for later use
    ctime       = models.DateTimeField(default=timezone.now)
    mtime       = models.DateTimeField(default=timezone.now)
    atime       = models.DateTimeField(default=timezone.now)

    # Flags
    HAS_AVATAR = 1
    
    def __unicode__(self):
        return unicode(self.pen_name)
    
    def email_authenticated(self):
        return (self.email_auth == 0L)
    
    def is_friend(self, other):
        return self.friends.filter(id=other.id).exists()
    
    class Meta:
        permissions = (
            ("post_blog", "User can make blog posts"),
            ("admin"    , "User can see dashboard, etc."),
        )

# Story prompts
class Prompt(models.Model):
    user        = models.ForeignKey(Profile)
    title       = models.CharField(max_length=128)
    body        = models.CharField(max_length=256)
    mature      = models.BooleanField(default=False)
    activity    = models.FloatField(default=0.0)
    ctime       = models.DateTimeField(default=timezone.now)
    mtime       = models.DateTimeField(default=timezone.now)

    def __unicode__(self):
        return unicode(self.title)
    
# Stories
class Story(models.Model):
    user        = models.ForeignKey(Profile)
    title       = models.CharField(max_length=256)
    body        = models.CharField(max_length=1536)
    prequel_to  = models.ForeignKey('self', blank=True, null=True, related_name='prequels')
    sequel_to   = models.ForeignKey('self', blank=True, null=True, related_name='sequels')
    prompt      = models.ForeignKey(Prompt, blank=True, null=True)
    mature      = models.BooleanField(default=False)
    draft       = models.BooleanField(default=False)
    ficly       = models.BooleanField(default=False)
    activity    = models.FloatField(default=0.0, null=True)
    prompt_text = models.CharField(max_length=256, blank=True, null=True)
    ctime       = models.DateTimeField(default=timezone.now)
    mtime       = models.DateTimeField(default=timezone.now)
    ptime       = models.DateTimeField(blank=True, null=True)
    ftime       = models.DateTimeField(blank=True, null=True)

    def __unicode__(self):
        return unicode(self.title)
    
# Story tags
class Tag(models.Model):
    story       = models.ForeignKey(Story)
    tag         = models.CharField(max_length=64)

    def __unicode__(self):
        return unicode(self.tag) + u' on ' + self.story.__unicode__()

    # Each tag must be unique within a story
    class Meta:
        unique_together = ('story', 'tag')

# Stories
class Blog(models.Model):
    user        = models.ForeignKey(Profile)
    title       = models.CharField(max_length=256)
    body        = models.CharField(max_length=20480)
    draft       = models.BooleanField(default=False)
    ctime       = models.DateTimeField(default=timezone.now)
    mtime       = models.DateTimeField(default=timezone.now)
    ptime       = models.DateTimeField(blank=True, null=True)

    def __unicode__(self):
        return unicode(self.title)
    
# Story rating
class Rating(models.Model):
    user        = models.ForeignKey(Profile)
    story       = models.ForeignKey(Story)
    rating      = models.IntegerField(blank=True, null=True)
    ctime       = models.DateTimeField(default=timezone.now)
    mtime       = models.DateTimeField(default=timezone.now)
    
    def __unicode__(self):
        return self.user.__unicode__() + u' rates "' + self.story.__unicode__() + u'" by ' + self.story.user.__unicode__() + u' with score ' + unicode(self.rating)

    # Each user can only rate an individual story once
    class Meta:
        unique_together = ('user', 'story')

# Comment on story or blog post
class Comment(models.Model):
    user        = models.ForeignKey(Profile, related_name='comments_made')       # User making the comment
    body        = models.CharField(max_length=1024)
    story       = models.ForeignKey(Story, blank=True, null=True)
    blog        = models.ForeignKey(Blog,  blank=True, null=True)
    ctime       = models.DateTimeField(default=timezone.now)
    mtime       = models.DateTimeField(default=timezone.now)    

    def __unicode__(self):
        if (self.story is not None):
            return self.user.__unicode__() + u' comment on story "' + self.story.__unicode__() + u'" by ' + self.story.user.__unicode__() + u' with text "' + unicode(self.body)[:30] + u'"'
        if (self.blog is not None):
            return self.user.__unicode__() + u' comment on blog post "' + self.blog.__unicode__() + u'" by ' + self.blog.user.__unicode__() + u' with text "' + unicode(self.body)[:30] + u'"'
        return self.user.__unicode__() + u' comment on nothing at all with text "' + unicode(self.body)[:30] + u'"'

    def get_rating(self):
        if (self.story is not None):
            r = Rating.objects.filter(story=self.story, user=self.user)
            if (r and (r[0].rating>0)):
                return r[0].rating
        return None


# Activity log
class StoryLog(models.Model):
    WRITE   = 0
    VIEW    = 1
    RATE    = 2
    COMMENT = 3
    PREQUEL = 4
    SEQUEL  = 5
    CHALLENGE = 6  # Created a challenge
    STORY_MOD = 7  # Modified an extant story
    PROMPT    = 8  # Created a writing prompt
    PROMPT_MOD= 9   # Modified a writing prompt

    LOG_OPTIONS = (
        (WRITE,     u'wrote'),
        (VIEW,      u'viewed'),
        (RATE,      u'rated'),
        (COMMENT,   u'commented on'),
        (PREQUEL,   u'wrote a prequel to'),
        (SEQUEL,    u'wrote a sequel to'),
        (CHALLENGE, u'created challenge'),
        (STORY_MOD, u'updated story'),
        (PROMPT,    u'wrote prompt'),
        (PROMPT_MOD,u'updated prompt'),
    )
    
    user        = models.ForeignKey(Profile)
    story       = models.ForeignKey(Story, blank=True, null=True)
    log_type    = models.IntegerField(default=1, choices=LOG_OPTIONS)
    comment     = models.ForeignKey(Comment, blank=True, null=True)     # ID of comment, if this log is for a comment
    quel        = models.ForeignKey(Story,   blank=True, null=True,
 related_name='activity_quel_set')     # ID of prequel/sequel if this log is for a prequel/sequel
    prompt      = models.ForeignKey(Prompt, blank=True, null=True)
    ctime       = models.DateTimeField(default=timezone.now)
    
    def get_opt(self, o):
        return LOG_OPTIONS[o][1]
    
    def get_type(self):
        # FIXME: LOG_OPTIONS[self.log_type][1] is not the right way to access
        #        the LOG_OPTIONS structure
        return self.LOG_OPTIONS[self.log_type][1]

    def __unicode__(self):
        # FIXME: LOG_OPTIONS[self.log_type][1] is not the right way to access
        #        the LOG_OPTIONS structure
        return unicode(self.id)+u': User ' + self.user.__unicode__() + u' ' + self.LOG_OPTIONS[self.log_type][1] + u' story "' + self.story.__unicode__() + u'" by ' + self.story.user.__unicode__()
        

# Site log
class SiteLog(models.Model):
    ip          = models.GenericIPAddressField()
    url         = models.URLField(max_length=254)
    
    def __unicode__(self):
        return unicode(self.url) + u' hit from IP ' + unicode(self.url)

# Misc bits
class Misc(models.Model):
    key         = models.CharField(primary_key=True, max_length=32)
    s_val       = models.CharField(max_length=128, blank=True, null=True)
    i_val       = models.BigIntegerField(blank=True, null=True)

    def __unicode__(self):
        r = u'key:"'+unicode(self.key)+u'" : '
        if (self.s_val is not None):
            r = r + u' s_val="'+unicode(self.s_val)+u'";'
        if (self.i_val is not None):
            r = r + u' i_val='+unicode(self.i_val)+u';'
        return r
            
