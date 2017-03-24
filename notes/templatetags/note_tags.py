
#coding: utf-8
#This file is part of Ficlatté.
#Copyright (C) 2015-2017 Paul Robertson & Jim Stitzel
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

from django.template import Library, Node, TemplateSyntaxError
from django.utils.html import escape
from django.utils.http import urlquote
from django.utils.safestring import mark_safe
from notes.models import Note
from castle.models import Profile

register = Library()

#-----------------------------------------------------------------------------
@register.filter
def note_link(note):
    if note is None:
        return u'<NULL NOTE>'
    if note.read_date is None:
        return mark_safe(u'<b><a href="/notes/view/' + unicode(note.id) + u'" class="note-link">' + escape(note.subject) + u'</a></b>')
    else:
        return mark_safe(u'<a href="/notes/view/' + unicode(note.id) + u'" class="note-link">' + escape(note.subject) + u'</a>')

#-----------------------------------------------------------------------------
@register.filter
def inbox_count(profile):
    count = Note.objects.filter(recipient=profile, read_date__isnull=True, recipient_deleted_date__isnull=True).count()
    if count > 0:
        return mark_safe(u'<span class="inbox-count">' + escape(count) + u'</span>')
    else:
        return mark_safe(u'<span class="inbox-zero">' + escape(count) + u'</span>')

#-----------------------------------------------------------------------------
@register.filter
def author_msg(profile, wide=None):
    if (wide):
        wd = u' btn-block'
    else:
        wd = u''
        
    return mark_safe(u'<a class="btn btn-success'+wd+' author-msg-btn" href="/notes/compose?recipient=' + escape(profile.pen_name) + u'" type="button"><span class="glyphicon glyphicon-pencil"></span> Message ' + escape(profile.pen_name) + u'</a>')

#-----------------------------------------------------------------------------
