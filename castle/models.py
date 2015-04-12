from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

# Create your models here.

# Extra user data
class Profile(models.Model):
    user        = models.OneToOneField(User)
    friends     = models.ManyToManyField(User, symmetrical=False, related_name='friend_set')
    pen_name    = models.CharField(max_length=64)
    pen_name_uc = models.CharField(max_length=64)
    site_url    = models.URLField(max_length=254)
    site_name   = models.CharField(max_length=1024)
    biography   = models.CharField(max_length=1024)
    mature      = models.BooleanField(default=False)
    email_addr  = models.EmailField(max_length=254)
    email_flags = models.IntegerField(default=0)
    email_auth  = models.BigIntegerField(default=0)
    email_time  = models.DateTimeField(blank=True, null=True)
    old_auth    = models.BinaryField(max_length=64)     # DEPRECATED pass md5 val
    old_salt    = models.BigIntegerField(default=0)     # DEPRECATED pass salt
    prefs       = models.IntegerField(default=0)
    flags       = models.IntegerField(default=0)
    stored      = models.ForeignKey('Story')            # User can make a note of a story for later use
    ctime       = models.DateTimeField(default=datetime.now)
    mtime       = models.DateTimeField(default=datetime.now)
    atime       = models.DateTimeField(default=datetime.now)

# Story prompts
class Prompt(models.Model):
    user        = models.ForeignKey(User)
    title       = models.CharField(max_length=128)
    body        = models.CharField(max_length=256)
    mature      = models.BooleanField(default=False)
    activity    = models.FloatField(default=0.0)
    ctime       = models.DateTimeField(default=datetime.now)
    mtime       = models.DateTimeField(default=datetime.now)
    
# Stories
class Story(models.Model):
    user      = models.ForeignKey(User)
    title       = models.CharField(max_length=256)
    body        = models.CharField(max_length=1536)
    prequel_to  = models.ForeignKey('self', blank=True, null=True, related_name='sequels')      # I am a prequel so, from the linked story's point of view, I am one of its sequels
    sequel_to   = models.ForeignKey('self', blank=True, null=True, related_name='prequels')     # I am a sequel so, from the linked story's point of view, I am one of its prequels
    prompt      = models.ForeignKey(Prompt, blank=True, null=True)
    mature      = models.BooleanField(default=False)
    draft       = models.BooleanField(default=False)
    ficly       = models.BooleanField(default=False)
    published   = models.BooleanField(default=False)
    activity    = models.FloatField(default=0.0)
    prompt_text = models.CharField(max_length=256, blank=True, null=True)
    ctime       = models.DateTimeField(default=datetime.now)
    mtime       = models.DateTimeField(default=datetime.now)
    ptime       = models.DateTimeField(blank=True, null=True)
    ftime       = models.DateTimeField(blank=True, null=True)
    
# Story tags
class Tag(models.Model):
    story       = models.ForeignKey(Story)
    tag         = models.CharField(max_length=64)

    # Each tag must be unique within a story
    class Meta:
        unique_together = ('story', 'tag')

# Stories
class Blog(models.Model):
    user      = models.ForeignKey(User)
    title       = models.CharField(max_length=256)
    body        = models.CharField(max_length=20480)
    draft       = models.BooleanField(default=False)
    published   = models.BooleanField(default=False)
    ctime       = models.DateTimeField(default=datetime.now)
    mtime       = models.DateTimeField(default=datetime.now)
    
# Story rating
class Rating(models.Model):
    user        = models.ForeignKey(User)
    story       = models.ForeignKey(Story)
    rating      = models.IntegerField(blank=True, null=True)
    ctime       = models.DateTimeField(default=datetime.now)
    mtime       = models.DateTimeField(default=datetime.now)
    
    # Each user can only rate an individual story once
    class Meta:
        unique_together = ('user', 'story')

# Comment on story or blog post
class Comment(models.Model):
    user        = models.ForeignKey(User, related_name='comments_made')       # User making the comment
    author      = models.ForeignKey(User, related_name='comments_received')       # Author of the commented story
    body        = models.CharField(max_length=1024)
    story       = models.ForeignKey(Story, blank=True, null=True)
    blog        = models.ForeignKey(Blog,  blank=True, null=True)
    ctime       = models.DateTimeField(default=datetime.now)
    mtime       = models.DateTimeField(default=datetime.now)    

# Activity log
class StoryLog(models.Model):
    WRITE   = 0
    VIEW    = 1
    RATE    = 2
    COMMENT = 3
    PREQUEL = 4
    SEQUEL  = 5
    
    LOG_OPTIONS = (
        (WRITE,   'wrote'),
        (VIEW,    'viewed'),
        (RATE,    'rated'),
        (COMMENT, 'commented on'),
        (PREQUEL, 'wrote a prequel to'),
        (SEQUEL,  'wrote a sequel to'),
    )
    
    user        = models.ForeignKey(User)
    story       = models.ForeignKey(Story)
    them        = models.ForeignKey(User, related_name='activity_set')       # Author of target story
    log_type    = models.IntegerField(default=1, choices=LOG_OPTIONS)
    comment     = models.ForeignKey(Comment, blank=True, null=True)     # ID of comment, if this log is for a comment
    quel        = models.ForeignKey(Story,   blank=True, null=True, related_name='activity_quel_set')     # ID of prequel/sequel if this log is for a prequel/sequel

# Site log
class SiteLog(models.Model):
    ip          = models.GenericIPAddressField()
    url         = models.URLField(max_length=254)