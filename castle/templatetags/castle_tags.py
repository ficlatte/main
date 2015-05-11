
#coding: utf-8

from django import template
from django.utils.safestring import mark_safe
from datetime import timedelta, datetime
from django.utils.timezone import utc
from django.utils.html import escape
from django.utils.http import urlquote
from django.template.defaultfilters import stringfilter
from django.conf import settings
from castle.models import StoryLog
import math
import re
import unicodedata

register = template.Library()

#-----------------------------------------------------------------------------
@register.filter
def get_range(end, start=0):
    return range(start, end)

#-----------------------------------------------------------------------------
@register.filter
def num_comments_txt(obj):
    c = obj.comment_set.count()
    if (c == 1):
        return u'1 comment';
    else:
        return unicode(c) + u' comments'

#-----------------------------------------------------------------------------
@register.filter
def num_comments(obj):
    return obj.comment_set.count()

#-----------------------------------------------------------------------------
@register.filter
def num_stories_txt(obj):
    c = obj.story_set.count()
    if (c == 1):
        return u'1 story';
    else:
        return unicode(c) + u' stories'

#-----------------------------------------------------------------------------
@register.filter
def num_stories(obj):
    return obj.story_set.filter(draft = False).count()

#-----------------------------------------------------------------------------
@register.filter
def num_drafts(obj):
    return obj.story_set.filter(draft = True).count()

#-----------------------------------------------------------------------------
@register.filter
def profile_comments_txt(profile):
    c = profile.comments_made.count()
    if (c == 1):
        return u'1 comment';
    else:
        return unicode(c) + u' comments'

#-----------------------------------------------------------------------------
@register.filter
def num_friends_txt(profile):
    c = profile.friends.count()
    if (c == 1):
        return u'1 friend';
    else:
        return unicode(c) + u' friends'

#-----------------------------------------------------------------------------
@register.filter
def num_friends(profile):
    return profile.friends.count()

#-----------------------------------------------------------------------------
@register.filter
def num_followers(profile):
    return profile.followers.count()

#-----------------------------------------------------------------------------
@register.filter
def age(value):
    if (value is None):
        return u'<NULL TIME FIELD>'
    
    # Work out difference in seconds between now and the value parameter
    # FIXME: need to add hover text with the real date in
    now = datetime.utcnow().replace(tzinfo=utc)
    timediff = now - value
    age = timediff.total_seconds()

    if (age < 120):
        return u"a few moments ago"
    
    # Minutes
    age = int(age / 60)
    if (age < 60):
        s = u's' if (age != 1) else u''
        return unicode(age) + u' minute'+s+u' ago'

    # Hours
    age = int(age / 60)
    if (age < 48):
        s = u's' if (age != 1) else u''
        return unicode(age) + u' hour'+s+u' ago'

    # Days
    age = int(age / 24)
    if (age < 32):
        s = u's' if (age != 1) else u''
        return unicode(age) + u' day'+s+u' ago'

    # Months
    months = int((age * 12.0) / 365.25)
    if (months < 12):
        s = u's' if (months != 1) else u''
        return unicode(months) + u' month'+s+u' ago'

    # Years
    age = int(age / 365.25)
    s = u's' if (age != 1) else u''
    return unicode(age) + u' year'+s+u' ago'

#-----------------------------------------------------------------------------
@register.filter
def author_link(profile, tag=None):
    if (profile is None):
        return u''
    t1 = ''
    t2 = ''
    if (tag is not None):
        t1 = u'<'+tag+u'>'
        t2 = u'</'+tag.partition(' ')[0]+u'>'   # Get bit before first space
    
    # FIXME: Need proper URL magic here
    return mark_safe(t1+u'<a href="/authors/'+urlquote(profile.pen_name)+u'">'+ escape(profile.pen_name)+u'</a>'+t2)

#-----------------------------------------------------------------------------
@register.filter
def author_confirmed(profile, tag=None):
    if (profile is None):
        return u''
    if (profile.email_authenticated()):
        return u''
    t1 = ''
    t2 = ''
    if (tag is not None):
        t1 = u'<'+tag+u'>'
        t2 = u'</'+tag.partition(' ')[0]+u'>'   # Get bit before first space
    
    # FIXME: Need proper URL magic here
    return mark_safe(t1+u'<span style="color:red">  [Not confirmed]</span>'+t2)

#-----------------------------------------------------------------------------
@register.filter
def author_span(profile, tag=None):
    return mark_safe(u'<span>Author: '+author_link(profile,tag)+u'</span>')

#-----------------------------------------------------------------------------
@register.filter
@stringfilter
def url(text):
    return urlquote(text)

#-----------------------------------------------------------------------------
@register.filter
@stringfilter
def big_snippet(text):
    if (len(text) > 255):
        snippet = text[:255] + u'…'
    else:
        snippet = text

    return encode_story(snippet)

#-----------------------------------------------------------------------------
@register.filter
@stringfilter
def small_snippet(text):
    if (len(text) > 100):
        snippet = text[:100] + u'…'
    else:
        snippet = text

    return encode_story(snippet)

#-----------------------------------------------------------------------------
@register.filter
def story_link(story, tag=None):
    if (story is None):
        return u'<NULL STORY>'
    t1 = ''
    t2 = ''
    if (tag is not None):
        t1 = u'<'+tag+u'>'
        t2 = u'</'+tag.partition(' ')[0]+u'>'   # Get bit before first space
    
    d = '[DRAFT] ' if (story.draft) else ''
    
    # FIXME: fix URL
    return mark_safe(u'<a href="/stories/' + unicode(story.id) + u'">' + t1 + escape(d+story.title) + t2 + u'</a>')

#-----------------------------------------------------------------------------
@register.filter
def prompt_link(prompt, tag=None):
    if (story is None):
        return u'<NULL PROMPT>'
    t1 = ''
    t2 = ''
    if (tag is not None):
        t1 = u'<'+tag+u'>'
        t2 = u'</'+tag.partition(' ')[0]+u'>'   # Get bit before first space
    
    # FIXME: fix URL
    return mark_safe(u'<a href="/prompt/' + unicode(prompt.id) + u'">' + t1 + escape(prompt.title) + t2 + u'</a>')

#-----------------------------------------------------------------------------
@register.filter
def activity_entry(log):
    if (log.log_type == StoryLog.WRITE):
        return mark_safe(author_link(log.user)+u' wrote '+story_link(log.story))
    
    elif (log.log_type == StoryLog.COMMENT):
        return mark_safe(author_link(log.user)+u' wrote a comment on '+story_link(log.story))
        
    elif (log.log_type == StoryLog.SEQUEL):
        return mark_safe(author_link(log.user)+u' wrote '+story_link(log.story)+u', sequel to '+story_link(log.quel)+u' by '+author_link(log.quel.user))
        
    elif (log.log_type == StoryLog.PREQUEL):
        return mark_safe(author_link(log.user)+u' wrote '+story_link(log.story)+u', prequel to '+story_link(log.quel)+u' by '+author_link(log.quel.user))

    elif (log.log_type == StoryLog.STORY_MOD):
        return mark_safe(author_link(log.user)+u' updated '+story_link(log.story))

    return 'log_id={}, user={}; story={}, type={}'.format(log.id, log.user.id,log.story.id, log.log_type)
        
    return mark_safe(author_link(log.user) + u' ' + log.get_type() + u' ' + story_link(log.story))

#-----------------------------------------------------------------------------
@register.filter
def dashboard_entry(log):
    #WRITE   = 0
    #VIEW    = 1
    #RATE    = 2
    #COMMENT = 3
    #PREQUEL = 4
    #SEQUEL  = 5
    #CHALLENGE = 6  # Created a challenge
    #STORY_MOD = 7  # Modified an extant story
    #PROMPT    = 8  # Created a writing prompt
    #PROMPT_MOD= 9   # Modified a writing prompt

    prompt_txt = u''
    if (log.prompt):
        prompt_txt = u' prompt '+prompt_link(log.prompt)

    if (log.log_type == StoryLog.WRITE):
        return mark_safe(author_link(log.user)+u' wrote '+story_link(log.story)+prompt_txt)
    
    elif (log.log_type == StoryLog.COMMENT):
        return mark_safe(author_link(log.user)+u' wrote a comment on '+story_link(log.story)+u' by '+author_link(log.story.user))
        
    elif (log.log_type == StoryLog.RATE):
        return mark_safe(author_link(log.user)+u' rated '+story_link(log.story)+u' by '+author_link(log.story.user))
        
    elif (log.log_type == StoryLog.SEQUEL):
        return mark_safe(author_link(log.user)+u' wrote '+story_link(log.story)+u', sequel to '+story_link(log.quel)+u' by '+author_link(log.quel.user))
        
    elif (log.log_type == StoryLog.PREQUEL):
        return mark_safe(author_link(log.user)+u' wrote '+story_link(log.story)+u', prequel to '+story_link(log.quel)+u' by '+author_link(log.quel.user))

    elif (log.log_type == StoryLog.STORY_MOD):
        return mark_safe(author_link(log.user)+u' updated '+story_link(log.story))

    elif (log.log_type == StoryLog.PROMPT):
        return mark_safe(author_link(log.user)+u' wrote prompt '+prompt_link(log.prompt))

    elif (log.log_type == StoryLog.PROMPT_MOD):
        return mark_safe(author_link(log.user)+u' updated prompt '+prompt_link(log.prompt))

    return 'log_id={}, user={}; story={}, type={}'.format(log.id, log.user.id,log.story.id, log.log_type)
        
    return mark_safe(author_link(log.user) + u' ' + log.get_type() + u' ' + story_link(log.story))

#-----------------------------------------------------------------------------
@register.filter
def avatar(profile):
    # FIXME: fix URL
    #which_icon = unicode(profile.id)
    which_icon = 'default.png'
    
    return mark_safe(u'<a href="/authors/' + escape(profile.pen_name) + u'"><img alt="' + escape(profile.pen_name) + u'" class="img-rounded img-responsive" src="/static/img/avatar/' + which_icon + u'" /></a>')

#-----------------------------------------------------------------------------
@register.filter
def user_icon(profile):
    # FIXME: fix URL
    #which_icon = unicode(profile.id)
    which_icon = 'default.png'
    
    return mark_safe(u'<a href="/authors/' + escape(profile.pen_name) + u'"><img alt="' + escape(profile.pen_name) + u'" class="img-rounded img-responsive" src="/static/img/icon/' + which_icon + u'" /></a>')

#-----------------------------------------------------------------------------
@register.filter
def pager_button(page, url):
    # page is a two-element tuple; [0] describes the type of furniture
    # [1] contains the target page number
    target = url + u'?page_num=' + unicode(page[1])
    
    if (page[0] == 'P'):        # Previous page
        return mark_safe(u'<li><a href="' + target + u'">&laquo; Previous</a></li>')
    elif (page[0] == 'N'):      # Next page
        return mark_safe(u'<li><a href="' + target + u'">Next &raquo;</a></li>')
    elif (page[0] == 'G'):      # Go to page
        return mark_safe(u'<li><a href="' + target + u'">' + unicode(page[1]) + u'</a></li>')
    elif (page[0] == 'C'):      # Current page
        return mark_safe(u'<li class="active"><a href="#">' + unicode(page[1]) + u'</a></li>')
    elif (page[0] == 'S'):      # Separator
        return mark_safe(u'<li class="disabled"><a href="#">…</a></li>')
    else:
        return u'?'

#-----------------------------------------------------------------------------
@register.filter
def rating_pencils(rating):
    if (rating is None):
        return ''
    r = u''
    integer_rating = int(math.ceil(rating - 0.49))
    for i in range(0, integer_rating):
        r = r + u'<span class="glyphicon glyphicon-pencil" id="enabled"></span>'
    for i in range(integer_rating, 5):
        r = r + u'<span class="glyphicon glyphicon-pencil"></span>'
    return mark_safe(r)

#-----------------------------------------------------------------------------
@register.filter
def site_name(a):
    loc = getattr(settings, 'SERVER_LOCATION', 'dev')
    if (loc == 'production'):
        return u'Ficlatté'
    else:
        return u'Ficlatté dev site'
    
#-----------------------------------------------------------------------------
# ENCODE STORY FUNCTION.
#-----------------------------------------------------------------------------
def start_italic(mode):
    if (mode == u''):
        return (u'<em>', u'i')
    if (mode == u'b'):
        return (u'<em>', u'bi')
    return (u'', mode)

def end_italic(mode):
    if (mode == u'i'):
        return (u'</em>', u'')
    if (mode == u'bi'):
        return (u'</em>', u'b')
    if (mode == u'ib'):
        return (u'</strong></em><strong>', u'b')
    return (u'', mode)

def start_bold(mode):
    if (mode == u''):
        return (u'<strong>', u'b')
    if (mode == u'i'):
        return (u'<strong>', u'ib')
    return (u'', mode)

def end_bold(mode):
    if (mode == u'b'):
        return (u'</strong>', u'')
    if (mode == u'ib'):
        return (u'</strong>', u'i')
    if (mode == u'bi'):
        return (u'</em></strong><em>', u'i')
    return (u'', mode)

def end_all(mode):
    if (mode == u'b'):
        return u'</strong>'
    if (mode == u'i'):
        return u'</em>'
    if (mode == u'bi'):
        return u'</em></strong>'
    if (mode == u'ib'):
        return u'</strong></em>'
    return u''

def encode_story_line(line):
    # Ensure line is unicode
    line = unicode(line)
    
    # Blank lines get short shrift
    if (len(line) < 1):
        return mark_safe('<p></p>\n')
    
    mode = u''            # Start with nothing
    ctype = 0
    retval = u'<p>'
    
    for c in line:
        cat = unicodedata.category(c)[0]
        if (c == u'_'):         # We've got an underscore
            if (ctype):          # We've had letters, end italics
                (bit, mode) = end_italic(mode)
                retval += bit
            else:
                (bit, mode) = start_italic(mode)
                retval += bit
        elif (c == u'*'):        # We've got an star
            if (ctype):          # We've had letters, end bold
                (bit, mode) = end_bold(mode)
                retval += bit
            else:                # We've not had letters, start bold
                (bit, mode) = start_bold(mode)
                retval += bit
        elif (cat == 'Z'):
            ctype = 0            # Space: we're in mode 0
            retval += escape(c)
        elif (cat == 'L'):
            ctype = 1            # Letter: we're in mode 1
            retval += escape(c)
        else:
            retval += escape(c)
    
    retval += end_all(mode) + u'</p>\n'
    
    return retval

crlf = re.compile(r'(?:\r|\n|\r\n)')
ws = re.compile(r'(\s+)')

@register.filter
@stringfilter
def encode_story(text):
    story_lines = crlf.split(text)
    
    retval = u''
    for l in story_lines:
        retval += encode_story_line(l)
    return mark_safe(retval)

def poo_encode_story(text):
    # FIXME: this is has no functionality
    return mark_safe(u'<p>' + escape(text) + u'</p>')

#-----------------------------------------------------------------------------
