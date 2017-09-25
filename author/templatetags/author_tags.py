# coding: utf-8
# This file is part of Ficlatté.
# Copyright (C) 2015 Paul Robertson
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

from django.template import Library
from django.conf import settings
from django.utils.html import escape
from django.utils.safestring import mark_safe
from castle.models import Story

register = Library()

# -----------------------------------------------------------------------------
@register.filter
def recent_story(obj):
    r_story = Story.objects.filter(user_id=obj.id).order_by('-id')[0]
    return mark_safe(u'Most recent story: <a href="' + getattr(settings, "SITE_URL") + u'/stories/' + escape(r_story.id) + u'">' + escape(
        r_story.title) + u'</a>, published ' + escape(r_story.ptime.date()))

#-----------------------------------------------------------------------------
@register.filter
def is_friend(author, profile):

    # Is logged-in user the author?
    owner = ((profile is not None) and (profile == author))

    is_friend = False
    if profile and author:
        is_friend = profile.is_friend(author)

    if owner:
        return mark_safe(u'')
    elif is_friend:
        return mark_safe(u'<a class="btn btn-info btn-block" href="/friendship/del/' + escape(
            author.id) + u'/" id="make-link" type="button">Un-follow ' + escape(author.pen_name) + u'</a>')
    else:
        return mark_safe(u'<a class="btn btn-success btn-block" href="/friendship/add/' + escape(
            author.id) + u'/" id="make-link" type="button">Follow ' + escape(author.pen_name) + u'</a>')

#-----------------------------------------------------------------------------