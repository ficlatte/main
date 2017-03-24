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
