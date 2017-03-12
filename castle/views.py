#coding: utf-8
#This file is part of Ficlatté.
#Copyright (C) 2015 Paul Robertson
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

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Sum, Avg, Q, Count, F
from django.utils.http import urlquote_plus, urlquote
from django.conf import settings
from django.utils import timezone
from .models import *
from .mail import *
from datetime import datetime, timedelta, date
from random import randint
from struct import unpack
import os
import math
import re
import hashlib
from .forms import AvatarUploadForm
from .images import convert_avatars

#-----------------------------------------------------------------------------
# Global symbols
#-----------------------------------------------------------------------------
PAGE_COMMENTS   = 15
PAGE_STORIES    = 15
PAGE_BROWSE     = 25
PAGE_PROMPTS    = 20
PAGE_CHALLENGES = 15
PAGE_BLOG       = 10
PAGE_ALLTAGS    = 200

re_crlf = re.compile(r'(\r\n|\r|\n)')

#-----------------------------------------------------------------------------
# Pager
#-----------------------------------------------------------------------------
def bs_pager(cur_page, page_size, num_items):

    num_pages = int(math.ceil(num_items / (page_size+0.0)))

    # No need for a pager if we have fewer than two pages
    if (num_pages < 2):
        return None

    # Empty list
    page_nums = []

    if (cur_page > 1):  # Previous page mark if we're not on page 1
        page_nums.append(('P', cur_page-1));

    if (num_pages < 11):
        # Fewer than 13 pages, list them all
        for n in range(1, num_pages+1):
            if (n == cur_page):
                page_nums.append(('C', n))      # Current page
            else:
                page_nums.append(('G',n))       # Go to page n
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
                    page_nums.append(('G',n))   # Go to page n
            page_nums.append(('S', 0))          # Separator goes here
            page_nums.append(('G', num_pages-1))# then last two pages
            page_nums.append(('G', num_pages))
        elif (cur_page >= (num_pages-5)):
            # First two pages go here, then a separator
            page_nums.append(('G', 1))
            page_nums.append(('G', 2))
            page_nums.append(('S', 0))    # Separator goes here
            # Then the last nine pages
            for n in range (num_pages-8, num_pages+1):
                if (n == cur_page):
                    page_nums.append(('C', n))  # Current page
                else:
                    page_nums.append(('G',n))   # Go to page n
        else:
            # First two pages, a separator, then nine pages in the middle,
            # then another separator, then the last two.
            page_nums.append(('G', 1))
            page_nums.append(('G', 2))
            page_nums.append(('S', 0))    # Separator goes here
            # Then the last nine pages
            for n in range (cur_page-3, cur_page+4):
                if (n == cur_page):
                    page_nums.append(('C', n))  # Current page
                else:
                    page_nums.append(('G',n))   # Go to page n
            page_nums.append(('S', 0))    # Separator goes here
            page_nums.append(('G', num_pages-1))# then last two pages
            page_nums.append(('G', num_pages))

    if (cur_page < num_pages):  # Next page mark if we're not last page
        page_nums.append(('N', cur_page+1))

    return page_nums

#-----------------------------------------------------------------------------
# Helper functions
#-----------------------------------------------------------------------------
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

#-----------------------------------------------------------------------------
def safe_int(v, default=1):
    try:
        return int(v)
    except ValueError:
        return default

#-----------------------------------------------------------------------------
def random64():
    return unpack("!Q", os.urandom(8))[0]

#-----------------------------------------------------------------------------
def to_signed64(u):
    if (u > (1<<63)):
        return u - (1<<64)
    else:
        return u

#-----------------------------------------------------------------------------
def to_unsigned64(s):
    if (s < 0):
        return s + (1<<64)
    else:
        return s

#-----------------------------------------------------------------------------
def validate_email_addr( email ):
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError
    try:
        validate_email( email )
        return True
    except ValidationError:
        return False

#-----------------------------------------------------------------------------
# Registration and Authentication
#-----------------------------------------------------------------------------
@transaction.atomic
def signin(request):
    username = request.POST.get('username', None)
    password = request.POST.get('password', None)
    nxt = request.POST.get('next', None)

    if ((username is None) or (password is None)):
        raise Http404

    # Now we work magic to match the Django auth system with the
    # legacy Ficlatté auth system
    prof = Profile.objects.filter(pen_name_uc = username.upper())
    if (not prof):
        return render(request, 'castle/login.html', {
                'error_title' : u'Log in failed',
                'error_messages' : [u'Invalid pen name or password'],
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
            login(request,user)

            if (nxt):
                return HttpResponseRedirect(nxt)
            else:
                return HttpResponseRedirect(reverse('home'))

    else:
        user = authenticate(username=profile.user.username, password=password)

    if user is not None:
        if user.is_active:
            login(request, user)

            if (nxt):
                return HttpResponseRedirect(nxt)
            else:
                return HttpResponseRedirect(reverse('home'))
        else:
            return HttpResponse("Account disabled")
    else:
        return render(request, 'castle/login.html', {
                'error_title' : u'Log in failed',
                'error_messages' : [u'Invalid pen name or password'],
            })

#-----------------------------------------------------------------------------
def signout(request):
    logout(request)
    return HttpResponseRedirect(reverse('home'))

#-----------------------------------------------------------------------------
def new_email_flag_entry(request, items, profile, code, descr, perm=None):
    node = {}

    node['code']  = code
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

#-----------------------------------------------------------------------------
def confirmation(request, yesno, uid, token):
    profile = get_object_or_404(Profile, pk=uid)

    logged_in_user = None
    if (request.user.is_authenticated()):
        logged_in_user = request.user.profile

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
                           'status_message': u'E-mail address confirmed successfully',})
        elif (yesno == 'no'):
            # FIXME: need to add e-mail to blacklist
            return render(request, 'castle/status_message.html',
                          {'profile': logged_in_user,
                           'status_type': 'danger',
                           'status_message': u'E-mail address added to do-not-send list',})
        else:
            raise Http404

    return render(request, 'castle/status_message.html',
                      {'profile': logged_in_user,
                      'status_type': 'danger',
                      'status_message': u'Authentication token mismatch'})

#-----------------------------------------------------------------------------
@login_required
def resend_email_conf(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Get data from form
    pen_name        = profile.pen_name
    email_addr      = profile.email_addr
    email_auth      = profile.email_auth
    email_time      = profile.email_time

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

    #Build context and render page
    context = {
        'page_title'        : u'Resend email confirmation',
        'email_conf'        : email_conf,
        }

    return render(request, 'castle/registration/resend_email_confirmation.html', context)

#-----------------------------------------------------------------------------
# User Dashboard
#-----------------------------------------------------------------------------
@login_required
def dashboard(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    if ((profile is None) or (not request.user.has_perm("castle.admin"))):
        raise Http404

    # Count number of views in last 24 hours:
    date_from = timezone.now() - timedelta(days=1)
    views = StoryLog.objects.filter(log_type=StoryLog.VIEW, ctime__gte=date_from).count()

    # Count users
    users = Profile.objects.count()

    # Count stories
    tot_stories = Story.objects.count()
    act_stories = Story.objects.filter(activity__gt = 0).count()
    pub_stories = Story.objects.exclude(draft=True).count()

    # Recent log entries
    log = StoryLog.objects.exclude(log_type=StoryLog.VIEW).order_by('-ctime')[0:25]

    # Recent users
    recent_users = Profile.objects.all().order_by('-ctime')[0:10]

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
        }

    return render(request, 'castle/dashboard.html', context)
    
#-----------------------------------------------------------------------------    
@login_required
def add_friend(request, user_id):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # get friend object
    friend = get_object_or_404(Profile, pk=user_id)

    # Add friend to profile's friendship list
    profile.friends.add(friend)

    return HttpResponseRedirect(reverse('author', args=(friend.pen_name,)))

#-----------------------------------------------------------------------------
@login_required
def del_friend(request, user_id):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # get friend object
    friend = get_object_or_404(Profile, pk=user_id)

    # Add friend to profile's friendship list
    profile.friends.remove(friend)

    return HttpResponseRedirect(reverse('author', args=(friend.pen_name,)))    

#-----------------------------------------------------------------------------
@login_required
def avatar_upload(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

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
		'profile'		: profile,
        'page_title'    : u'Upload avatar',
        'form'          : form,
        }
    return render(request, 'castle/avatar_upload.html', context)

#-----------------------------------------------------------------------------
# Comment Submission
#-----------------------------------------------------------------------------
@login_required
@transaction.atomic
def submit_comment(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
    if (not profile):
        raise Http404

    # Get bits and bobs
    errors     = []
    old_rating = None
    blog       = get_foo(request.POST, Blog,  'bid')
    story      = get_foo(request.POST, Story, 'sid')
    prompt	   = get_foo(request.POST, Prompt, 'pid')
    challenge  = get_foo(request.POST, Challenge, 'chid')

    if (story):
        try:
            r = Rating.objects.get(user=profile, story=story)
            old_rating = r.rating
        except ObjectDoesNotExist:
            old_rating = None

    rating     = request.POST.get('rating', None)
    if (rating is not None):
        rating = int(rating)

    if (not profile.email_authenticated()):
        errors.append(u'You must have authenticated your e-mail address before posting a comment');

    # Create comment object
    comment = Comment(user = profile,
                        blog = blog,
                        story = story,
                        prompt = prompt,
                        challenge = challenge)

    # Populate comment object with data from submitted form
    comment.body   = request.POST.get('body', '')

    # Condense all end-of-line markers into \n
    comment.body = re_crlf.sub(u"\n", comment.body)

    # Check for submission errors
    l = len(comment.body)
    if ((l < 1) and (rating is None)):
        # Empty comments are allowed if the user is making a rating
        errors.append(u'Comment body must be at least 1 character long')

    if (l > 1024):
        errors.append(u'Comment is over 1024 characters (currently ' + unicode(l) + u')')

    # If there have been errors, re-display the page
    if (errors):
    # Build context and render page
        if (blog):
            return blog_view(request, blog.id, comment.body, 'Comment submission unsuccessful', errors)
        elif (story):
            return story_view(request, story.id, comment.body, rating, u'Comment submission failed', errors)
        elif (prompt):
            return prompt_view(request, prompt.id, comment.body, u'Comment submission failed', errors)
        else:
            return challenge_view(request, challenge.id, comment.body, u'Comment submission failed', errors)

    # Set modification time
    comment.mtime = timezone.now()

    # No problems, update the database and redirect
    if (l > 0):
        comment.save()

    # Update rating, if applicable
    if (story):
        if ((story is not None) and (rating is not None)):
            rating_set = Rating.objects.filter(story=story, user=profile)
            if (rating_set):
                rating_obj = rating_set[0]
            else:
                rating_obj = Rating(user=profile, story=story)
                rating_obj.rating = rating
                rating_obj.mtime = timezone.now()
                rating_obj.save()

    # Make log entries but only for story or challenge comments
    if (story):
        # If comment body is longer than 0, log that comment has been made
        if (l > 0):
            log = StoryLog(
                user = profile,
                story = story,
                comment = comment,
                log_type = StoryLog.COMMENT
                )
            log.save()
        # If there was no previous rating and there is a rating,
        # log that a rating has been made
        if ((rating is not None) and (old_rating is None)):
            log = StoryLog(
                user = profile,
                story = story,
                log_type = StoryLog.RATE
                )
            log.save()
    elif (prompt):
        # If comment body is longer than 0, log that comment has been made
        if (l > 0):
            log = StoryLog(
                user = profile,
                prompt = prompt,
                comment = comment,
                log_type = StoryLog.COMMENT
                )
            log.save()
    elif (challenge):
        # If comment body is longer than 0, log that comment has been made
        if (l > 0):
            log = StoryLog(
                user = profile,
                challenge = challenge,
                comment = comment,
                log_type = StoryLog.COMMENT
                )
            log.save()

    # Send e-mail messages to subscribed users
    send_notification_email_comment(comment)

    # Auto-subscribe to e-mail notifications according to user's preferences
    if (profile):
        if (blog):
            if (profile.email_flags & Profile.AUTOSUBSCRIBE_ON_BLOG_COMMENT):
                Subscription.objects.get_or_create(user=profile, blog=blog)
        elif (story):
            if (profile.email_flags & Profile.AUTOSUBSCRIBE_ON_STORY_COMMENT):
                Subscription.objects.get_or_create(user=profile, story=story)
        elif (prompt):
            if (profile.email_flags & Profile.AUTOSUBSCRIBE_ON_PROMPT_COMMENT):
                Subscription.objects.get_or_create(user=profile, prompt=prompt)
        elif (challenge):
            if (profile.email_flags & Profile.AUTOSUBSCRIBE_ON_CHALLENGE_COMMENT):
                Subscription.objects.get_or_create(user=profile, challenge=challenge)

    if (blog):
        return HttpResponseRedirect(reverse('blog', args=(blog.id,)))
    elif (story):
        return HttpResponseRedirect(reverse('story', args=(story.id,)))
    elif (prompt):
        return HttpResponseRedirect(reverse('prompt', args=(prompt.id,)))
    elif (challenge):
        return HttpResponseRedirect(reverse('challenge', args=(challenge.id,)))
        
#-----------------------------------------------------------------------------
# Static Views        
#-----------------------------------------------------------------------------
def static_view(request, template_name):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    context = {
        'profile'       : profile
        }
    return render(request, 'castle/'+template_name, context)
