from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.utils.text import wrap
from django.utils.translation import ugettext as _
from django.utils import timezone
from django.core.urlresolvers import reverse
from django.conf import settings

from castle.models import *
from .models import *
from .mail import *

import re

#-----------------------------------------------------------------------------

re_crlf = re.compile(r'(\r\n|\r|\n)')

#-----------------------------------------------------------------------------
def get_foo(request, foo, key):

    nid = request.get(key, None)
    if ((nid is None) or (nid == '') or (nid == 'None')):  # Text 'None' results in None return
        return None

    # The id may be invalid; the note may not exist.
    # Return it if it's there or None otherwise
    sl = foo.objects.filter(pk=nid)
    if (sl):
        return sl[0]
    else:
        return None

#-----------------------------------------------------------------------------
@login_required
def inbox(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Get target user's information
    author = Profile.objects.filter(pen_name_uc = profile.pen_name.upper())
    if (not author):
        raise Http404()
    author = author[0]          # Get single object from collection

    # Is logged-in user the author?
    owner = ((profile is not None) and (profile == author))

    note_list = Note.objects.inbox_for(request.user.profile)

    context = { 'profile' 		: profile,
                'author'		: author,
                'page_title'	: u'Inbox',
                'note_list'		: note_list,
              }

    return render(request, 'notes/inbox.html', context)

#-----------------------------------------------------------------------------
@login_required
def outbox(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Get target user's information
    author = Profile.objects.filter(pen_name_uc = profile.pen_name.upper())
    if (not author):
        raise Http404()
    author = author[0]          # Get single object from collection

    # Is logged-in user the author?
    owner = ((profile is not None) and (profile == author))

    note_list = Note.objects.outbox_for(request.user.profile)

    context = { 'profile' 		: profile,
                'author'		: author,
                'page_title'	: u'Outbox',
                'note_list'		: note_list,
              }

    return render(request, 'notes/outbox.html', context)

#-----------------------------------------------------------------------------
@login_required
def trash(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Get target user's information
    author = Profile.objects.filter(pen_name_uc = profile.pen_name.upper())
    if (not author):
        raise Http404()
    author = author[0]          # Get single object from collection

    # Is logged-in user the author?
    owner = ((profile is not None) and (profile == author))

    note_list = Note.objects.trash_for(request.user.profile)

    context = { 'profile' 		: profile,
                'author'		: author,
                'page_title'	: u'Trash',
                'note_list'		: note_list,
              }

    return render(request, 'notes/trash.html', context)

#-----------------------------------------------------------------------------
@login_required
def view(request, note_id):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Get target user's information
    author = Profile.objects.filter(pen_name_uc = profile.pen_name.upper())
    if (not author):
        raise Http404()
    author = author[0]          # Get single object from collection

    # Is logged-in user the author?
    owner = ((profile is not None) and (profile == author))

    now = timezone.now()
    note = get_object_or_404(Note, id=note_id)
    if (note.sender != profile) and (note.recipient != profile):
        raise Http404
    if note.read_date is None and note.recipient == profile:
        note.read_date = now
        note.save()

    context = {	'profile'		: profile,
                'author'		: author,
                'page_title'	: u'View note',
                'note'			: note,
              }
        
    return render(request, 'notes/view.html', context)

#-----------------------------------------------------------------------------
@login_required
def new_note(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Get target user's information
    author = Profile.objects.filter(pen_name_uc = profile.pen_name.upper())
    if (not author):
        raise Http404()
    author = author[0]          # Get single object from collection

    # Is logged-in user the author?
    owner = ((profile is not None) and (profile == author))

    if request.GET.get('recipient', ''):
        recipient_obj = request.GET.get('recipient', '')
        recipient = get_object_or_404(Profile, pen_name_uc = recipient_obj.upper())

        # Create a blank note from an author page
        note = Note(recipient = recipient)
    else:
        # Create a blank note
        note = Note()

    context = {	'profile'		: profile,
                'author'		: author,
                'page_title'	: u'Write note',
                'note'			: note,
                'length_limit'	: 2048,
              }

    return render(request, 'notes/compose.html', context)

#-----------------------------------------------------------------------------
@login_required
def submit_note(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Get target user's information
    author = Profile.objects.filter(pen_name_uc = profile.pen_name.upper())
    if (not author):
        raise Http404()
    author = author[0]          # Get single object from collection

    # Get bits and bobs
    errors     	= []
    note      	= get_foo(request.POST, Note,  'nid')
    new_note	= (note is None)

    # Is logged-in user the author?
    owner = ((profile is not None) and (profile == author))

    if (not profile.email_authenticated()):
        errors.append(u'You must have authenticated your e-mail address before writing a note.')

    # Get story object, either existing or new
    if (note is None):
        note = Note(user       = profile,
                    )

    # Lookup user ID of recipient
    recipient = request.POST.get('recipient', '')
    recipient_obj = Profile.objects.get(pen_name_uc = recipient.upper())
    recipient_id = recipient_obj.user_id

    # Populate story object with data from submitted form
    note.sender_id		= profile.user_id
    note.recipient_id	= recipient_id
    note.subject		= request.POST.get('subject', '')
    note.body			= request.POST.get('body', '')

    # Condense all end-of-line markers into \n
    note.body = re_crlf.sub(u"\n", note.body)

    # Check for submission errors
    l = len(note.body)
    if (len(note.subject) < 1):
        errors.append(u'Story title must be at least 1 character long')

    if (l > 1024):
        errors.append(u'Note is over 2048 characters (currently ' + unicode(l) + u')')

    # If there have been errors, re-display the page
    if (errors):
    # Build context and render page
        context = {	'profile'		: profile,
                    'author'		: author,
                    'note'			: note,
                    'length_limit'	: 2048,
                    'error_messages': errors,
                  }

        return render(request, 'notes/compose.html', context)

    # Set sent time
    note.sent_date = timezone.now()

    # No problems, update the database and redirect
    note.save()

    # Send notification email
    send_note_email(note)
    
    return HttpResponseRedirect(reverse('notes_inbox'))
    
#-----------------------------------------------------------------------------
@login_required
def reply(request, note_id):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Get target user's information
    author = Profile.objects.filter(pen_name_uc = profile.pen_name.upper())
    if (not author):
        raise Http404()
    author = author[0]          # Get single object from collection

    # Is logged-in user the author?
    owner = ((profile is not None) and (profile == author))

    parent = get_object_or_404(Note, pk=note_id)
    reply_recipient_id = parent.sender_id
    reply_recipient_obj = Profile.objects.get(pk = reply_recipient_id)
    reply_recipient = reply_recipient_obj.pen_name

    # Format subject line
    if 'Re: ' in parent.subject:
        subject = parent.subject
    else:
        subject = u'Re: ' + parent.subject

    # Format quote body
    lines = wrap(parent.body, 55).split('\n')
    for i, line in enumerate(lines):
        lines[i] = "> %s" % line
    quote = '\n'.join(lines)

    # Populate reply fields
    note = Note(sender		= profile,
                recipient	= reply_recipient_obj,
                subject		= subject,
                body		= quote,
                )

    # Build context and render page
    context = {	'profile'		: profile,
                'author'		: author,
                'page_title'	: u'Reply',
                'note'			: note,
                'length_limit'	: 2048,
              }

    return render(request, 'notes/compose.html', context)

#-----------------------------------------------------------------------------
@login_required
def forward(request, note_id):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Get target user's information
    author = Profile.objects.filter(pen_name_uc = profile.pen_name.upper())
    if (not author):
        raise Http404()
    author = author[0]          # Get single object from collection

    # Is logged-in user the author?
    owner = ((profile is not None) and (profile == author))

    parent = get_object_or_404(Note, pk=note_id)

    # Format subject line
    if 'Fw: ' in parent.subject:
        subject = parent.subject
    else:
        subject = u'Fw: ' + parent.subject

    # Format quote body
    lines = wrap(parent.body, 55).split('\n')
    for i, line in enumerate(lines):
        lines[i] = "> %s" % line
    quote = '\n'.join(lines)

    # Populate reply fields
    note = Note(sender		= profile,
                subject		= subject,
                body		= quote,
                )

    # Build context and render page
    context = {	'profile'		: profile,
                'author'		: author,
                'page_title'	: u'Reply',
                'note'			: note,
                'length_limit'	: 2048,
              }

    return render(request, 'notes/compose.html', context)

#-----------------------------------------------------------------------------
@login_required
def delete(request, note_id, success_url=None):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Get target user's information
    author = Profile.objects.filter(pen_name_uc = profile.pen_name.upper())
    if (not author):
        raise Http404()
    author = author[0]          # Get single object from collection

    # Is logged-in user the author?
    owner = ((profile is not None) and (profile == author))

    # Has the author's email been confirmed?
    email_conf = (author.email_auth == 0)

    now = timezone.now()
    note = get_object_or_404(Note, id=note_id)
    deleted = False
    if success_url is None:
        success_url = reverse('notes_inbox')
    if 'next' in request.GET:
        success_url = request.GET['next']
    if note.sender == profile:
        note.sender_deleted_date = now
        deleted = True
    if note.recipient == profile:
        note.recipient_deleted_date = now
        deleted = True
    if deleted:
        note.save()
        return HttpResponseRedirect(success_url)
    raise Http404

#-----------------------------------------------------------------------------
@login_required
def undelete(request, note_id, success_url=None):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Get target user's information
    author = Profile.objects.filter(pen_name_uc = profile.pen_name.upper())
    if (not author):
        raise Http404()
    author = author[0]          # Get single object from collection

    # Is logged-in user the author?
    owner = ((profile is not None) and (profile == author))

    # Has the author's email been confirmed?
    email_conf = (author.email_auth == 0)

    note = get_object_or_404(Note, id=note_id)
    undeleted = False
    if success_url is None:
        success_url = reverse('notes_inbox')
    if 'next' in request.GET:
        success_url = request.GET['next']
    if note.sender == profile:
        note.sender_deleted_date = None
        undeleted = True
    if note.recipient == profile:
        note.recipient_deleted_date = None
        undeleted = True
    if undeleted:
        note.save()
        return HttpResponseRedirect(success_url)
    raise Http404

#-----------------------------------------------------------------------------
