
#coding: utf-8
#This file is part of Ficlatté.
#Copyright (C) 2015-2017 Paul Robertson, Jim Stitzel, & Shu Sam Chen
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

import hashlib
import math
import os
import re
from datetime import timedelta
from struct import unpack
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, get_object_or_404
from .forms import AvatarUploadForm
from .images import convert_avatars
from .mail import *
from the_pit.views import the_pit

# -----------------------------------------------------------------------------
# Global symbols
# -----------------------------------------------------------------------------
PAGE_COMMENTS   = 15
PAGE_STORIES    = 15
PAGE_BROWSE     = 25
PAGE_PROMPTS    = 20
PAGE_CHALLENGES = 15
PAGE_BLOG       = 10
PAGE_AUTHORS    = 25
PAGE_ALLTAGS    = 200

re_crlf = re.compile(r'(\r\n|\r|\n)')


# -----------------------------------------------------------------------------
# Pager
# -----------------------------------------------------------------------------
def bs_pager(cur_page, page_size, num_items):
    num_pages = int(math.ceil(num_items / (page_size + 0.0)))

    # No need for a pager if we have fewer than two pages
    if (num_pages < 2):
        return None

    # Empty list
    page_nums = []

    if (cur_page > 1):  # Previous page mark if we're not on page 1
        page_nums.append(('P', cur_page - 1))

    if (num_pages < 11):
        # Fewer than 13 pages, list them all
        for n in range(1, num_pages + 1):
            if (n == cur_page):
                page_nums.append(('C', n))  # Current page
            else:
                page_nums.append(('G', n))  # Go to page n
    else:
        # More than ten pages, we have three cases here
        # We aim to show the current page, and 4 pages either side of
        # the current page.  At each end we always show the first two and
        # and the last two pages.
        #   case 1: cur_page near the start
        #   case 2: cur_page near the end
        #   case 3: cur_page not near either end
        if (cur_page < 6):
            for n in range(1, 10):
                if (n == cur_page):
                    page_nums.append(('C', n))  # Current page
                else:
                    page_nums.append(('G', n))  # Go to page n
            page_nums.append(('S', 0))  # Separator goes here
            page_nums.append(('G', num_pages - 1))  # then last two pages
            page_nums.append(('G', num_pages))
        elif (cur_page >= (num_pages - 5)):
            # First two pages go here, then a separator
            page_nums.append(('G', 1))
            page_nums.append(('G', 2))
            page_nums.append(('S', 0))  # Separator goes here
            # Then the last nine pages
            for n in range(num_pages - 8, num_pages + 1):
                if (n == cur_page):
                    page_nums.append(('C', n))  # Current page
                else:
                    page_nums.append(('G', n))  # Go to page n
        else:
            # First two pages, a separator, then nine pages in the middle,
            # then another separator, then the last two.
            page_nums.append(('G', 1))
            page_nums.append(('G', 2))
            page_nums.append(('S', 0))  # Separator goes here
            # Then the last nine pages
            for n in range(cur_page - 3, cur_page + 4):
                if (n == cur_page):
                    page_nums.append(('C', n))  # Current page
                else:
                    page_nums.append(('G', n))  # Go to page n
            page_nums.append(('S', 0))  # Separator goes here
            page_nums.append(('G', num_pages - 1))  # then last two pages
            page_nums.append(('G', num_pages))

    if (cur_page < num_pages):  # Next page mark if we're not last page
        page_nums.append(('N', cur_page + 1))

    return page_nums


# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------
def get_foo(request, foo, key):
    """Uses a request.POST or a request.GET enquiry to attempt to
       get hold of a named GET or POST parameter and look it up in the
       relevant database
       eg. to use the GET field 'sid' as a key in the Story table, use

       get_foo(request.GET, Story, 'sid')
       """
    sid = request.get(key, None)
    if ((sid is None) or (sid == '') or (sid == 'None')):  # Text 'None' results in None return
        return None

    # The id may be invalid; the story may not exist.
    # Return it if it's there or None otherwise
    sl = foo.objects.filter(pk=sid)
    if (sl):
        return sl[0]
    else:
        return None


# -----------------------------------------------------------------------------
def safe_int(v, default=1):
    try:
        return int(v)
    except ValueError:
        return default


# -----------------------------------------------------------------------------
def random64():
    return unpack("!Q", os.urandom(8))[0]


# -----------------------------------------------------------------------------
def to_signed64(u):
    if (u > (1 << 63)):
        return u - (1 << 64)
    else:
        return u


# -----------------------------------------------------------------------------
def to_unsigned64(s):
    if (s < 0):
        return s + (1 << 64)
    else:
        return s


# -----------------------------------------------------------------------------
def validate_email_addr(email):
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False


# -----------------------------------------------------------------------------
# Registration and Authentication
# -----------------------------------------------------------------------------
@transaction.atomic
def signin(request):
    username = request.POST.get('username', None)
    password = request.POST.get('password', None)
    nxt = request.POST.get('next', None)

    if ((username is None) or (password is None)):
        raise Http404

    # Now we work magic to match the Django auth system with the
    # legacy Ficlatté auth system
    prof = Profile.objects.filter(pen_name_uc=username.upper())
    if (not prof):
        return render(request, 'castle/login.html', {
            'error_title': u'Log in failed',
            'error_messages': [u'Invalid pen name or password'],
        })
    profile = prof[0]

    user = None
    grunt = "none"
    # Check to see if legacy auth tokens remain
    if (profile.old_salt is not None and len(profile.old_salt) == 16):
        # Run old-fashioned auth
        ph = hashlib.sha256()
        ph.update(profile.old_salt)
        ph.update(password)
        grunt = "old auth but failed"
        if (ph.hexdigest() == profile.old_auth):
            grunt = "old auth succeeded"
            # Fake successful authentication
            user = profile.user
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            user.set_password(password)
            profile.old_salt = None
            profile.old_auth = None
            user.save()
            profile.save()
            # For some reason, we need to log in again now
            user = authenticate(username=profile.user.username, password=password)
            login(request, user)

            if (nxt):
                return HttpResponseRedirect(nxt)
            else:
                return HttpResponseRedirect(reverse('home'))

    else:
        user = authenticate(username=profile.user.username, password=password)

    if (user is not None):
        if (user.is_active):
            login(request, user)

            if (nxt):
                return HttpResponseRedirect(nxt)
            else:
                return HttpResponseRedirect(reverse('home'))
        else:
            return HttpResponse("Account disabled")
    else:
        return render(request, 'castle/login.html', {
            'error_title': u'Log in failed',
            'error_messages': [u'Invalid pen name or password'],
        })


# -----------------------------------------------------------------------------
def signout(request):
    logout(request)
    return HttpResponseRedirect(reverse('home'))


# -----------------------------------------------------------------------------
def new_email_flag_entry(request, items, profile, code, descr, perm=None):
    node = {}

    node['code'] = code
    node['descr'] = descr
    if (profile):
        node['is_set'] = ((profile.email_flags & code) > 0)
    else:
        node['is_set'] = True

    # If permissions required, check
    if (perm):
        if (request.user.has_perm(perm)):
            items.append(node)
    else:
        items.append(node)


# -----------------------------------------------------------------------------
def confirmation(request, yesno, uid, token):
    profile = get_object_or_404(Profile, pk=uid)

    logged_in_user = None
    if (request.user.is_authenticated()):
        logged_in_user = request.user.profile
        if (logged_in_user.spambot):
            return the_pit(request)

    int_token = safe_int(token, -1)

    # Check to see if the UID and token are valid before we do anything else.
    # Also, keep user feedback vague, as we don't want to leak user data

    # The request is valid if the profile object has a non-null email_auth
    # and the token in the request matches it.  We send the token unsigned
    # but the underlying database stores it signed, so we need to do a bit
    # of munging before we do the comparison
    if (not profile.email_auth):
        return render(request, 'castle/status_message.html',
                      {'profile': logged_in_user,
                       'status_type': 'info',
                       'status_message': u'E-mail address already authenticated.'})
    elif (int_token == to_unsigned64(profile.email_auth)):
        # Request is authorised, now we look at the yes/no
        if (yesno == 'yes'):
            # It's a valid e-mail confirmation message
            profile.email_auth = 0
            profile.email_time = timezone.now()
            profile.save()
            return render(request, 'castle/status_message.html',
                          {'profile': logged_in_user,
                           'status_type': 'success',
                           'status_message': u'E-mail address confirmed successfully', })
        elif (yesno == 'no'):
            # FIXME: need to add e-mail to blacklist
            return render(request, 'castle/status_message.html',
                          {'profile': logged_in_user,
                           'status_type': 'danger',
                           'status_message': u'E-mail address added to do-not-send list', })
        else:
            raise Http404

    return render(request, 'castle/status_message.html',
                  {'profile': logged_in_user,
                   'status_type': 'danger',
                   'status_message': u'Authentication token mismatch'})


# -----------------------------------------------------------------------------
@login_required
def resend_email_conf(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
        if (profile.spambot):
            return the_pit(request)

    # Set modification time
    time_now = timezone.now()

    # Has the author's email address been confirmed?
    email_conf = (profile.email_auth == 0)
    if (not email_conf):
        # Get random 64 bit integer
        token = random64()
        token_s = to_signed64(token)
        profile.email_auth = token_s
        profile.email_time = time_now
        send_conf_email(profile, token)
        profile.save()

    # Build context and render page
    context = {
        'page_title': u'Resend email confirmation',
        'email_conf': email_conf,
    }

    return render(request, 'castle/registration/resend_email_confirmation.html', context)


# -----------------------------------------------------------------------------
# User Dashboard
# -----------------------------------------------------------------------------
@login_required
def dashboard(request):
    # Get user profile
    profile = None
    if request.user.is_authenticated():
        profile = request.user.profile

    if (profile is None) or (not request.user.has_perm("castle.admin")):
        raise Http404

    # Count number of views in last 24 hours:
    date_from = timezone.now() - timedelta(days=1)
    views = StoryLog.objects.filter(log_type=StoryLog.VIEW, ctime__gte=date_from).count()

    # Count users
    users = Profile.objects.count()

    # Count stories
    tot_stories = Story.objects.count()
    act_stories = Story.objects.filter(activity__gt=0).count()
    pub_stories = Story.objects.exclude(draft=True).count()

    # Recent log entries
    log = StoryLog.objects.exclude(log_type=StoryLog.VIEW).order_by('-ctime')[0:25]

    # Recent users
    recent_users = Profile.objects.all().order_by('-ctime')[0:10]
    
    # Spam stats
    quarantined    = Comment.objects.filter(spam=Comment.SPAM_QUARANTINE).count()
    confirmed_spam = Comment.objects.filter(spam=Comment.SPAM_CONFIRMED).count()
    not_spam       = Comment.objects.filter(spam=Comment.SPAM_APPROVED).count()
    spambots       = Profile.objects.filter(spambot=True).count()

    # Build context and render page
    context = {
               'profile'       : profile,
               'views'         : views,
               'users'         : users,
               'page_title'    : u'Dashboard',
               'tot_stories'   : tot_stories,
               'act_stories'   : act_stories,
               'pub_stories'   : pub_stories,
               'log'           : log,
               'recent_users'  : recent_users,
               'quarantined'   : quarantined,
               'confirmed_spam': confirmed_spam,
               'not_spam'      : not_spam,
               'spambots'      : spambots,
              }

    return render(request, 'castle/dashboard.html', context)


# -----------------------------------------------------------------------------
@login_required
def add_friend(request, user_id):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
        if (profile.spambot):
            return the_pit(request)

    # get friend object
    friend = get_object_or_404(Profile, pk=user_id)

    # Add friend to profile's friendship list
    profile.friends.add(friend)

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


# -----------------------------------------------------------------------------
@login_required
def del_friend(request, user_id):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
        if (profile.spambot):
            return the_pit(request)

    # get friend object
    friend = get_object_or_404(Profile, pk=user_id)

    # Add friend to profile's friendship list
    profile.friends.remove(friend)

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


# -----------------------------------------------------------------------------
@login_required
def avatar_upload(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
        if (profile.spambot):
            return the_pit(request)

    if (request.method == 'POST'):
        form = AvatarUploadForm(request.POST, request.FILES)
        if (form.is_valid()):
            # Happy
            f = request.FILES['image_file']
            path = getattr(settings, 'AVATAR_PATH', None)
            fnm = path + '/tmp/' + str(profile.id)
            destination = open(fnm, 'wb+')
            for chunk in f.chunks():
                destination.write(chunk)
            destination.close()
            failure = convert_avatars(profile)
            os.remove(fnm)
            if (not failure):
                profile.flags = profile.flags | Profile.HAS_AVATAR
                profile.save()

            return HttpResponseRedirect(reverse('home'))
    else:
        form = AvatarUploadForm()

    context = {
               'profile'      : profile,
               'page_title'   : u'Upload avatar',
               'form'         : form,
              }
    return render(request, 'castle/avatar_upload.html', context)


# -----------------------------------------------------------------------------
# Static Views        
# -----------------------------------------------------------------------------
def static_view(request, template_name):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
        if (profile.spambot):
            return the_pit(request)

    context = {
               'profile': profile
              }
    return render(request, 'castle/' + template_name, context)
