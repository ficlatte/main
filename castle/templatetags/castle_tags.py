from django import template
from django.utils.safestring import mark_safe
from datetime import timedelta, datetime
from django.utils.timezone import utc
from django.utils.html import escape

register = template.Library()

#-----------------------------------------------------------------------------
@register.filter
def comments(obj):
    c = obj.comment_set.count()
    if (c == 1):
        return u'1 comment';
    else:
        return unicode(c) + u' comments'

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
    