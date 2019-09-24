
#coding: utf-8
#This file is part of Ficlatté.
#Copyright © 2015-2017 Paul Robertson, Jim Stitzel, & Shu Sam Chen
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

import math
import re
import unicodedata
from datetime import datetime
from django import template
from django.conf import settings
from django.db.models import F
from django.template.defaultfilters import stringfilter
from django.utils.html import escape
from django.utils.http import urlquote
from django.utils.safestring import mark_safe
from django.utils.timezone import utc
from bbcode import util as bbcode
from castle.models import StoryLog, Profile, Comment

register = template.Library()


# -----------------------------------------------------------------------------
@register.filter
def get_range(end, start=0):
    return range(start, end)


# -----------------------------------------------------------------------------
@register.filter
def num_comments_txt(obj):
    c = obj.comment_set.filter(spam__lt=Comment.SPAM_QUARANTINE).count()
    if c == 1:
        return u'1 comment'
    else:
        return unicode(c) + u' comments'


# -----------------------------------------------------------------------------
@register.filter
def num_comments(obj):
    return obj.comment_set.filter(spam__lt=Comment.SPAM_QUARANTINE).count()
        
#-----------------------------------------------------------------------------
@register.filter
def num_comment_likes(obj):
    return obj.commentlike_set.count()

#-----------------------------------------------------------------------------
@register.filter
def users_liked(obj):
    users = '\n'.join(Profile.objects.filter(comment_liked__comment_id=obj.id).values_list('pen_name', flat=True))
    return users


#-----------------------------------------------------------------------------
@register.filter
def comment_like(obj, profile):
    if obj.commentlike_set.filter(user_id=profile.id, comment_id=obj.id):
        return mark_safe(u'<a class="like-comment" href="#" data-url="/comment/' + unicode(obj.id) + u'/unlike/">Unlike</a>')
    else:
        return mark_safe(u'<a class="like-comment" href="#" data-url="/comment/' + unicode(obj.id) + u'/like">Like</a>')

# -----------------------------------------------------------------------------
@register.filter
def num_stories_txt(obj):
    c = obj.story_set.filter(draft=False).count()
    if c == 1:
        return u'1 story'
    else:
        return unicode(c) + u' stories'


# -----------------------------------------------------------------------------
@register.filter
def num_stories(obj):
    return obj.story_set.filter(draft=False).count()


# -----------------------------------------------------------------------------
@register.filter
def num_drafts(obj):
    return obj.story_set.filter(draft=True).count()


# -----------------------------------------------------------------------------
@register.filter
def num_prompts(obj):
    return obj.prompt_set.count()


# -----------------------------------------------------------------------------
@register.filter
def num_prompts_txt(obj):
    c = obj.prompt_set.count()
    if c == 1:
        return u'1 prompt'
    else:
        return unicode(c) + u' prompts'


# -----------------------------------------------------------------------------
@register.filter
def num_challenges(obj):
    return obj.challenge_set.count()


# -----------------------------------------------------------------------------
@register.filter
def num_challenges_txt(obj):
    c = obj.challenge_set.count()
    if c == 1:
        return u'1 challenge'
    else:
        return unicode(c) + u' challenges'


# -----------------------------------------------------------------------------
@register.filter
def num_challenge_wins(obj):
    return obj.story_set.filter(challenge__winner=F('id')).count()


# -----------------------------------------------------------------------------
@register.filter
def profile_comments_txt(profile):
    c = profile.comments_made.count()
    if c == 1:
        return u'1 comment'
    else:
        return unicode(c) + u' comments'


# -----------------------------------------------------------------------------
@register.filter
def num_friends_txt(profile):
    c = profile.friends.count()
    if c == 1:
        return u'1 friend'
    else:
        return unicode(c) + u' friends'


# -----------------------------------------------------------------------------
@register.filter
def num_friends(profile):
    return profile.friends.count()


# -----------------------------------------------------------------------------
@register.filter
def num_followers(profile):
    return profile.followers.count()


# -----------------------------------------------------------------------------
@register.filter
def age(value):
    if value is None:
        return u'<NULL TIME FIELD>'

    # Work out difference in seconds between now and the value parameter
    # FIXME: need to add hover text with the real date in
    now = datetime.utcnow().replace(tzinfo=utc)
    timediff = now - value
    age = timediff.total_seconds()

    if age < 120:
        return u"a few moments ago"

    # Minutes
    age = int(age / 60)
    if age < 60:
        s = u's' if (age != 1) else u''
        return unicode(age) + u' minute' + s + u' ago'

    # Hours
    age = int(age / 60)
    if age < 48:
        s = u's' if (age != 1) else u''
        return unicode(age) + u' hour' + s + u' ago'

    # Days
    age = int(age / 24)
    if age < 32:
        s = u's' if (age != 1) else u''
        return unicode(age) + u' day' + s + u' ago'

    # Months
    months = int((age * 12.0) / 365.25)
    if months < 12:
        s = u's' if (months != 1) else u''
        return unicode(months) + u' month' + s + u' ago'

    # Years
    age = int(age / 365.25)
    s = u's' if (age != 1) else u''
    return unicode(age) + u' year' + s + u' ago'


# -----------------------------------------------------------------------------
@register.filter
def author_link(profile, tag=None):
    if profile is None:
        return u''
    t1 = ''
    t2 = ''
    if tag is not None:
        t1 = u'<' + tag + u'>'
        t2 = u'</' + tag.partition(' ')[0] + u'>'  # Get bit before first space

    # FIXME: Need proper URL magic here
    try:
        return mark_safe(
            t1 + u'<a href="/authors/' + urlquote(profile.pen_name) + u'">' + escape(profile.pen_name) + u'</a>' + t2)
    except AttributeError:
        return mark_safe(t1+u'<a href="#">no profile</a>' + t2)

# -----------------------------------------------------------------------------
@register.filter
def author_social_media(profile):
    if profile is None:
        return u''
    s = ''
    f = ''
    t = ''
    w = ''

    if profile.site_url is not None:
        s = u'<a href="' + profile.site_url + u'" title="' + profile.site_name + u'" target="_blank"><img src="/static/img/social-media/earth.png" class="social-media-icon"></a>'
    if profile.facebook_username is not None:
        f = u'<a href="http://facebook.com/' + profile.facebook_username + u'" title="Facebook" target="_blank"><img src="/static/img/social-media/facebook.png" class="social-media-icon"></a>'
    if profile.twitter_username is not None:
        t = u'<a href="http://twitter.com/' + profile.twitter_username + u'" title="Twitter" target="_blank"><img src="/static/img/social-media/twitter.png" class="social-media-icon"></a>'
    if profile.wattpad_username is not None:
        w = u'<a href="http://wattpad.com/user/' + profile.wattpad_username + u'" title="Wattpad" target="_blank"><img src="/static/img/social-media/wattpad.png" class="social-media-icon"></a>'

    return mark_safe(f + t + w + s)


# -----------------------------------------------------------------------------
@register.filter
def author_confirmed(profile, tag=None):
    if profile is None:
        return u''
    if profile.email_authenticated():
        return u''
    t1 = ''
    t2 = ''
    if tag is not None:
        t1 = u'<' + tag + u'>'
        t2 = u'</' + tag.partition(' ')[0] + u'>'  # Get bit before first space

    # FIXME: Need proper URL magic here
    return mark_safe(t1 + u'<span style="color:red">  [Not confirmed]</span>' + t2)


# -----------------------------------------------------------------------------
@register.filter
def author_span(profile, tag=None):
    return mark_safe(u'<span class="byline">Author: ' + author_link(profile, tag) + u'</span>')


# -----------------------------------------------------------------------------
@register.filter
@stringfilter
def url(text):
    return urlquote(text)


# -----------------------------------------------------------------------------
@register.filter
@stringfilter
def big_snippet(text):
    if len(text) > 255:
        snippet = text[:255] + u'…'
    else:
        snippet = text

    return encode_story(snippet)


# -----------------------------------------------------------------------------
@register.filter
@stringfilter
def small_snippet(text):
    if len(text) > 100:
        snippet = text[:100] + u'…'
    else:
        snippet = text

    return encode_story(snippet)


# -----------------------------------------------------------------------------
@register.filter
def story_link(story, tag=None):
    if story is None:
        return u'<NULL STORY>'
    t1 = ''
    t2 = ''
    if tag is not None:
        t1 = u'<' + tag + u'>'
        t2 = u'</' + tag.partition(' ')[0] + u'>'  # Get bit before first space

    d = '[DRAFT] ' if story.draft else ''
    m = u'<span class="glyphicon glyphicon-flash" style="color:red"></span>' if story.mature else ''

    w = u'<img src="/static/img/badge-40.png">' if (story.winner.count() > 0) else ''
    # FIXME: fix URL
    if tag == 'h1':
        return mark_safe(t1 + escape(d + story.title) + u' ' + mark_safe(w) + mark_safe(m) + t2)
    else:
        return mark_safe(u'<a href="/stories/' + unicode(story.id) + u'" class="story-link">' + t1 + escape(
            d + story.title) + u' ' + mark_safe(w) + mark_safe(m) + t2 + u'</a>')

# -----------------------------------------------------------------------------
@register.filter
def prompt_link(prompt, tag=None):
    if prompt is None:
        return u'<NULL PROMPT>'
    t1 = ''
    t2 = ''
    if tag is not None:
        t1 = u'<' + tag + u'>'
        t2 = u'</' + tag.partition(' ')[0] + u'>'  # Get bit before first space

    m = ' <span class="glyphicon glyphicon-flash" style="color:red"></span>' if prompt.mature else ''
    # FIXME: fix URL
    if tag == 'h1':
        return mark_safe(t1 + escape(prompt.title) + u' ' + mark_safe(m) + t2)
    else:
        return mark_safe(u'<a href="/prompts/' + unicode(prompt.id) + u'" class="prompt-link">' + t1 + escape(
            prompt.title) + mark_safe(m) + t2 + u'</a>')


# -----------------------------------------------------------------------------
@register.filter
def challenge_link(challenge, tag=None):
    if challenge is None:
        return u'<NULL CHALLENGE>'
    t1 = ''
    t2 = ''
    if tag is not None:
        t1 = u'<' + tag + u'>'
        t2 = u'</' + tag.partition(' ')[0] + u'>'  # Get bit before first space

    m = ' <span class="glyphicon glyphicon-flash" style="color:red"></span>' if challenge.mature else ''
    # FIXME: fix URL
    if tag == 'h1':
        return mark_safe(t1 + escape(challenge.title) + u' ' + mark_safe(m) + t2)
    else:
        return mark_safe(u'<a href="/challenges/' + unicode(challenge.id) + u'" class="challenge-link">' + t1 + escape(
            challenge.title) + mark_safe(m) + t2 + u'</a>')


# -----------------------------------------------------------------------------
@register.filter
def activity_entry(log):
    if log is None:
        return u'None'

    if log.log_type == StoryLog.WRITE:
        return mark_safe(author_link(log.user) + u' wrote ' + story_link(log.story))

    elif log.log_type == StoryLog.COMMENT:
        if log.story:
            return mark_safe(author_link(log.user) + u' wrote a comment on ' + story_link(log.story))
        if log.prompt:
            return mark_safe(author_link(log.user) + u' wrote a comment on ' + prompt_link(log.prompt))
        else:
            return mark_safe(author_link(log.user) + u' wrote a comment on ' + challenge_link(log.challenge))

    elif log.log_type == StoryLog.SEQUEL:
        return mark_safe(author_link(log.user) + u' wrote a sequel, ' + story_link(log.story) + u', to ' + story_link(
            log.quel) + u' by ' + author_link(log.quel.user))

    elif log.log_type == StoryLog.PREQUEL:
        return mark_safe(author_link(log.user) + u' wrote a prequel, ' + story_link(log.story) + u', to ' + story_link(
            log.quel) + u' by ' + author_link(log.quel.user))

    elif log.log_type == StoryLog.STORY_MOD:
        return mark_safe(author_link(log.user) + u' updated ' + story_link(log.story))

    elif log.log_type == StoryLog.PROMPT:
        return mark_safe(author_link(log.user) + u' wrote prompt ' + prompt_link(log.prompt))

    elif log.log_type == StoryLog.PROMPT_MOD:
        return mark_safe(author_link(log.user) + u' updated prompt ' + prompt_link(log.prompt))

    elif log.log_type == StoryLog.CHALLENGE:
        return mark_safe(author_link(log.user) + u' created challenge ' + challenge_link(log.challenge))

    elif log.log_type == StoryLog.CHALLENGE_MOD:
        return mark_safe(author_link(log.user) + u' updated challenge ' + challenge_link(log.challenge))

    elif log.log_type == StoryLog.CHALLENGE_ENT:
        return mark_safe(
            author_link(log.user) + u' entered ' + story_link(log.story) + u' into the challenge ' + challenge_link(
                log.challenge))

    elif log.log_type == StoryLog.CHALLENGE_WON:
        return mark_safe(
            author_link(log.user) + u' won the challenge ' + challenge_link(log.challenge) + u' with ' + story_link(
                log.story))

    return mark_safe(author_link(log.user) + u' ' + log.get_type() + u' ' + story_link(log.story))


# -----------------------------------------------------------------------------
@register.filter
def dashboard_entry(log):
    # WRITE   = 0
    # VIEW    = 1
    # RATE    = 2
    # COMMENT = 3
    # PREQUEL = 4
    # SEQUEL  = 5
    # CHALLENGE = 6  # Created a challenge
    # STORY_MOD = 7  # Modified an extant story
    # PROMPT    = 8  # Created a writing prompt
    # PROMPT_MOD= 9   # Modified a writing prompt
    # CHALLENGE	= 10 # Created a challenge
    # CHALLENGE_MOD = 11 # Modified a challenge
    # CHALLENGE_ENT = 12 # Entered a challenge
    # CHALLENGE_WON = 13 # Won a challenge

    prompt_txt = u''
    if log.prompt:
        prompt_txt = u' prompt ' + prompt_link(log.prompt)

    if log.log_type == StoryLog.WRITE:
        return mark_safe(author_link(log.user) + u' wrote ' + story_link(log.story) + prompt_txt)

    elif log.log_type == StoryLog.COMMENT:
        if log.story:
            txt = author_link(log.user) + u' wrote a comment on ' + story_link(log.story) + u' by ' + author_link(log.story.user)
            if (log.comment.spam == Comment.SPAM_QUARANTINE):
                txt += u' QUARANTINED!'
            return mark_safe(txt)
        if log.prompt:
            return mark_safe(author_link(log.user) + u' wrote a comment on ' + prompt_link(log.prompt))
        else:
            return mark_safe(
                author_link(log.user) + u' wrote a comment on ' + challenge_link(log.challenge) + u' by ' + author_link(
                    log.challenge.user))

    elif log.log_type == StoryLog.RATE:
        return mark_safe(
            author_link(log.user) + u' rated ' + story_link(log.story) + u' by ' + author_link(log.story.user))

    elif log.log_type == StoryLog.SEQUEL:
        return mark_safe(author_link(log.user) + u' wrote ' + story_link(log.story) + u', sequel to ' + story_link(
            log.quel) + u' by ' + author_link(log.quel.user))

    elif log.log_type == StoryLog.PREQUEL:
        return mark_safe(author_link(log.user) + u' wrote ' + story_link(log.story) + u', prequel to ' + story_link(
            log.quel) + u' by ' + author_link(log.quel.user))

    elif log.log_type == StoryLog.STORY_MOD:
        return mark_safe(author_link(log.user) + u' updated ' + story_link(log.story))

    elif log.log_type == StoryLog.PROMPT:
        return mark_safe(author_link(log.user) + u' wrote prompt ' + prompt_link(log.prompt))

    elif log.log_type == StoryLog.PROMPT_MOD:
        return mark_safe(author_link(log.user) + u' updated prompt ' + prompt_link(log.prompt))

    elif log.log_type == StoryLog.CHALLENGE:
        return mark_safe(author_link(log.user) + u' created challenge ' + challenge_link(log.challenge))

    elif log.log_type == StoryLog.CHALLENGE_MOD:
        return mark_safe(author_link(log.user) + u' updated challenge ' + challenge_link(log.challenge))

    elif log.log_type == StoryLog.CHALLENGE_ENT:
        return mark_safe(
            author_link(log.user) + u' entered ' + story_link(log.story) + u' into the challenge ' + challenge_link(
                log.challenge))

    elif log.log_type == StoryLog.CHALLENGE_WON:
        return mark_safe(
            author_link(log.user) + u' won the challenge ' + challenge_link(log.challenge) + u' with ' + story_link(
                log.story))

    return mark_safe(author_link(log.user) + u' ' + log.get_type() + u' ' + story_link(log.story))


# -----------------------------------------------------------------------------
@register.filter
def avatar(profile):
    if profile.flags & Profile.HAS_AVATAR:
        which_icon = str(profile.id) + '.png'
    else:
        which_icon = 'default.png'

    return mark_safe(u'<a href="/authors/' + escape(profile.pen_name) + u'"><img class="author-avatar" alt="' + escape(
        profile.pen_name) + u'" title="' + escape(profile.pen_name) + u'" src="/static/img/avatar/' + which_icon + u'" /></a>')


# -----------------------------------------------------------------------------
@register.filter
def user_icon(profile):
    if profile.flags & Profile.HAS_AVATAR:
        which_icon = str(profile.id) + '.png'
    else:
        which_icon = 'default.png'

    return mark_safe(u'<a href="/authors/' + escape(profile.pen_name) + u'"><img class="author-icon" alt="' + escape(
        profile.pen_name) + u'" title="' + escape(profile.pen_name) + u'" src="/static/img/icon/' + which_icon + u'" height="48" width="48"/></a>')


# -----------------------------------------------------------------------------
@register.filter
def pager_button(page, url):
    # page is a two-element tuple; [0] describes the type of furniture
    # [1] contains the target page number
    target = url + u'?page_num=' + unicode(page[1])

    if page[0] == 'P':  # Previous page
        return mark_safe(u'<li><a href="' + target + u'">&laquo; Previous</a></li>')
    elif page[0] == 'N':  # Next page
        return mark_safe(u'<li><a href="' + target + u'">Next &raquo;</a></li>')
    elif page[0] == 'G':  # Go to page
        return mark_safe(u'<li><a href="' + target + u'">' + unicode(page[1]) + u'</a></li>')
    elif page[0] == 'C':  # Current page
        return mark_safe(u'<li class="active"><a href="#">' + unicode(page[1]) + u'</a></li>')
    elif page[0] == 'S':  # Separator
        return mark_safe(u'<li class="disabled"><a href="#">…</a></li>')
    else:
        return u'?'


# -----------------------------------------------------------------------------
@register.filter
def rating_pencils(rating):
    if rating is None:
        return ''
    r = u''
    integer_rating = int(math.ceil(rating - 0.49))
    for i in range(0, integer_rating):
        r += u'<span class="glyphicon glyphicon-pencil" id="enabled"></span>'
    for i in range(integer_rating, 5):
        r += u'<span class="glyphicon glyphicon-pencil"></span>'
    return mark_safe(r)


# -----------------------------------------------------------------------------
@register.filter
def site_name(a):
    loc = getattr(settings, 'SERVER_LOCATION', 'dev')
    if loc == 'production':
        return u'Ficlatté'
    else:
        return u'Ficlatté dev site'


# -----------------------------------------------------------------------------
# ENCODE STORY FUNCTION.
# -----------------------------------------------------------------------------
def start_italic(mode):
    if mode == u'':
        return u'<em>', u'i'
    if mode == u'b':
        return u'<em>', u'bi'
    return u'', mode


def end_italic(mode):
    if mode == u'i':
        return u'</em>', u''
    if mode == u'bi':
        return u'</em>', u'b'
    if mode == u'ib':
        return u'</strong></em><strong>', u'b'
    return u'', mode


def start_bold(mode):
    if mode == u'':
        return u'<strong>', u'b'
    if mode == u'i':
        return u'<strong>', u'ib'
    return u'', mode


def end_bold(mode):
    if mode == u'b':
        return u'</strong>', u''
    if mode == u'ib':
        return u'</strong>', u'i'
    if mode == u'bi':
        return u'</em></strong><em>', u'i'
    return u'', mode


def end_all(mode):
    if mode == u'b':
        return u'</strong>'
    if mode == u'i':
        return u'</em>'
    if mode == u'bi':
        return u'</em></strong>'
    if mode == u'ib':
        return u'</strong></em>'
    return u''


def encode_story_line(line):
    # Ensure line is unicode
    line = unicode(line)

    # Blank lines get short shrift
    if len(line) < 1:
        return mark_safe('<p></p>\n')

    mode = u''  # Start with nothing
    ctype = 0
    retval = u'<p>'

    for c in line:
        cat = unicodedata.category(c)[0]
        if c == u'_':  # We've got an underscore
            if ctype:  # We've had letters, end italics
                (bit, mode) = end_italic(mode)
                retval += bit
            else:
                (bit, mode) = start_italic(mode)
                retval += bit
        elif c == u'*':  # We've got an star
            if ctype:  # We've had letters, end bold
                (bit, mode) = end_bold(mode)
                retval += bit
            else:  # We've not had letters, start bold
                (bit, mode) = start_bold(mode)
                retval += bit
        elif cat == 'Z':
            ctype = 0  # Space: we're in mode 0
            retval += escape(c)
        elif cat == 'L':
            ctype = 1  # Letter: we're in mode 1
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


# -----------------------------------------------------------------------------
@register.filter
def encode_blog(blog):
    if blog.bbcode:
        return mark_safe(bbcode.to_html(blog.body))
    else:
        return encode_story(blog.body)


# -----------------------------------------------------------------------------
@register.filter
def blog_snippet(blog):
    if len(blog.body) > 255:
        snippet = blog.body[:255] + u'…'
    else:
        snippet = blog.body

    if blog.bbcode:
        return mark_safe(bbcode.to_html(snippet))
    else:
        return encode_story(snippet)

# -----------------------------------------------------------------------------
