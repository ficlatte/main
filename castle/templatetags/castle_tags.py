
#coding: utf-8

from django import template
from django.utils.safestring import mark_safe
from datetime import timedelta, datetime
from django.utils.timezone import utc
from django.utils.html import escape
from django.template.defaultfilters import stringfilter

register = template.Library()

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
def num_stories_txt(obj):
    c = obj.story_set.count()
    if (c == 1):
        return u'1 story';
    else:
        return unicode(c) + u' stories'

#-----------------------------------------------------------------------------
@register.filter
def age(value):
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
def author_link(profile):
    if (profile is None):
        return u''
    # FIXME: Need proper URL magic here
    return mark_safe(u'<a href="/authors/'+escape(profile.pen_name)+u'">'+ escape(profile.pen_name)+u'</a>')

#-----------------------------------------------------------------------------
@register.filter
def author_span(profile):
    return mark_safe(u'<span>Author: '+author_link(profile)+u'</span>')

#-----------------------------------------------------------------------------
@register.filter
@stringfilter
def encode_story(text):
    # FIXME: this is has no functionality
    return mark_safe(u'<p>' + escape(text) + u'</p>')

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
    t1 = ''
    t2 = ''
    if (tag is not None):
        t1 = u'<'+tag+u'>'
        t2 = u'</'+tag.partition(' ')[0]+u'>'   # Get bit before first space
    
    # FIXME: fix URL
    return mark_safe(u'<a href="/stories/' + unicode(story.id) + u'">' + t1 + escape(story.title) + t2 + u'</a>')

#-----------------------------------------------------------------------------
@register.filter
def avatar(profile):
    # FIXME: fix URL
    return mark_safe(u'<a href="/authors/' + escape(profile.pen_name) + u'"><img alt="' + escape(profile.pen_name) + u'" class="img-rounded img-responsive" src="/img/avatar/' + unicode(profile.id) + u'" /></a>')
