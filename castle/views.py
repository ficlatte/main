
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
def author(request, pen_name):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Get target author's information
    author = Profile.objects.filter(pen_name_uc = pen_name.upper())
    if (not author):
        raise Http404()
    author = author[0]          # Get single object from collection

    # Is logged-in user the author?
    owner = ((profile is not None) and (profile == author))

    # Has the author's email been confirmed?
    email_conf = True
    if (profile):
        email_conf = (profile.email_auth == 0)

    # Build story list (owner sees their drafts)
    page_num = safe_int(request.GET.get('page_num', 1))
    if (owner):
        num_stories = Story.objects.filter(user = author).count()
        story_list = Story.objects.filter(user = author).order_by('-draft','-ptime','-mtime')[(page_num-1)*PAGE_STORIES:page_num*PAGE_STORIES]
        num_prompts = Prompt.objects.filter(user = author).count()
        prompt_list = Prompt.objects.filter(user = author).order_by('-mtime')[(page_num-1)*PAGE_PROMPTS:page_num*PAGE_PROMPTS]
        num_challenges = Challenge.objects.filter(user = author).count()
        challenge_list = Challenge.objects.filter(user = author).order_by('-mtime')[(page_num-1)*PAGE_CHALLENGES:page_num*PAGE_CHALLENGES]
    else:
        num_stories = Story.objects.filter(user = author, draft = False).count()
        story_list = Story.objects.filter(user = author, draft = False).order_by('-ptime')[(page_num-1)*PAGE_STORIES:page_num*PAGE_STORIES]
        num_prompts = Prompt.objects.filter(user = author).count()
        prompt_list = Prompt.objects.filter(user = author).order_by('-mtime')[(page_num-1)*PAGE_PROMPTS:page_num*PAGE_PROMPTS]
        num_challenges = Challenge.objects.filter(user = author).count()
        challenge_list = Challenge.objects.filter(user = author).order_by('-mtime')[(page_num-1)*PAGE_CHALLENGES:page_num*PAGE_CHALLENGES]

    # Friendship?
    is_friend = False
    if (profile and author):
        is_friend = profile.is_friend(author)

    # Build context and render page
    context = { 'profile'       : profile,
                'author'        : author,
                'owner'			: owner,
                'story_list'    : story_list,
                'num_prompts'   : num_prompts,
                'prompt_list'   : prompt_list,
                'num_challenges' : num_challenges,
                'challenge_list' : challenge_list,
                'email_conf'    : email_conf,
                'page_title'    : author.pen_name,
                'page_url'      : u'/authors/'+urlquote(author.pen_name)+u'/',
                'pages'         : bs_pager(page_num, PAGE_STORIES, num_stories),
                'is_friend'     : is_friend,
                'user_dashboard': owner,
                'other_user_sidepanel' : (not owner),
            }
    return render(request, 'castle/author.html', context)

#-----------------------------------------------------------------------------
@login_required
def drafts(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
    
    # Has the author's email been confirmed?
    email_conf = (profile.email_auth == 0)

    # Build story list (owner sees their drafts)
    page_num = safe_int(request.GET.get('page_num', 1))
    num_stories = Story.objects.filter(user = profile, draft=True).count()
    story_list = Story.objects.filter(user = profile, draft=True).order_by('-mtime')[(page_num-1)*PAGE_STORIES:page_num*PAGE_STORIES]

    # Build context and render page
    context = { 'profile'       : profile,
                'author'        : profile,
                'story_list'    : story_list,
                'page_title'    : profile.pen_name,
                'email_conf'	: email_conf,
                'page_url'      : u'/authors/'+urlquote(profile.pen_name)+u'/',
                'pages'         : bs_pager(page_num, PAGE_STORIES, num_stories),
                'drafts_page'   : True,
                'user_dashboard': True,
                'other_user_sidepanel' : False,
            }
    return render(request, 'castle/author.html', context)

#-----------------------------------------------------------------------------
@login_required
def author_prompts(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Has the author's email been confirmed?
    email_conf = (profile.email_auth == 0)

    # Build story list (owner sees their drafts)
    page_num = safe_int(request.GET.get('page_num', 1))
    num_prompts = Prompt.objects.count()
    prompt_list = Prompt.objects.filter(user = profile).order_by('-mtime')[(page_num-1)*PAGE_STORIES:page_num*PAGE_STORIES]

    # Build context and render page
    context = { 'profile'       : profile,
                'author'        : profile,
                'prompt_list'   : prompt_list,
                'page_title'    : profile.pen_name,
                'email_conf'	: email_conf,
                'page_url'      : u'/authors/'+urlquote(profile.pen_name)+u'/',
                'pages'         : bs_pager(page_num, PAGE_STORIES, num_prompts),
                'prompts_page'  : True,
                'user_dashboard': True,
                'other_user_sidepanel' : False,
            }
    return render(request, 'castle/author.html', context)

#-----------------------------------------------------------------------------
@login_required
def author_challenges(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
        
    # Has the author's email been confirmed?
    email_conf = (profile.email_auth == 0)

    # Build story list (owner sees their drafts)
    page_num = safe_int(request.GET.get('page_num', 1))
    num_challenges = Challenge.objects.count()
    challenge_list = Challenge.objects.filter(user = profile).order_by('-mtime')[(page_num-1)*PAGE_STORIES:page_num*PAGE_STORIES]

    # Build context and render page
    context = { 'profile'       : profile,
                'author'        : profile,
                'challenge_list': challenge_list,
                'page_title'    : profile.pen_name,
                'email_conf'	: email_conf,
                'page_url'      : u'/authors/'+urlquote(profile.pen_name)+u'/',
                'pages'         : bs_pager(page_num, PAGE_STORIES, num_challenges),
                'challenges_page' : True,
                'user_dashboard': True,
                'other_user_sidepanel' : False,
            }
    return render(request, 'castle/author.html', context)

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
# Blog views
#-----------------------------------------------------------------------------
def blogs(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Get blogs
    page_num = safe_int(request.GET.get('page_num', 1))
    blogs = Blog.objects.exclude(draft=True).order_by('-ptime')[(page_num-1)*PAGE_BLOG:page_num*PAGE_BLOG]
    num_blogs = Blog.objects.exclude(draft = True).count()

    # Build context and render page
    context = { 'profile'       : profile,
                'blogs'         : blogs,
                'page_title'    : u'Blog page {}'.format(page_num),
                'page_url'      : u'/blog/',
                'pages'         : bs_pager(1, 10, blogs.count()),
            }
    return render(request, 'castle/blogs.html', context)

#-----------------------------------------------------------------------------
def blog_view(request, blog_id, comment_text=None, error_title='', error_messages=None):
    blog = get_object_or_404(Blog, pk=blog_id)

    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Is logged-in user the author?
    author = blog.user
    owner = ((profile is not None) and (profile == author))

    # Get comments
    page_num = safe_int(request.GET.get('page_num', 1))
    comments = blog.comment_set.all().order_by('ctime')[(page_num-1)*PAGE_COMMENTS:page_num*PAGE_COMMENTS]

    # Is user subscribed?
    subscribed = False
    if (profile is not None):
        subscribed = (blog.subscriptions.filter(user=profile).count()>0)

    # Build context and render page
    context = { 'profile'       : profile,
                'author'        : blog.user,
                'blog'          : blog,
                'comments'      : comments,
                'page_url'      : u'/stories/'+unicode(blog_id),
                'pages'         : bs_pager(page_num, PAGE_COMMENTS, blog.comment_set.count()),
                'owner'         : owner,
                'comment_text'  : comment_text,
                'subscribed'    : subscribed,
                'error_title'   : error_title,
                'error_messages': error_messages,
                'page_title'    : u'Blog '+blog.title,
            }
    return render(request, 'castle/blog.html', context)

#-----------------------------------------------------------------------------
@login_required
def blog_unsubscribe(request, blog_id, comment_text=None, error_title='', error_messages=None):
    blog = get_object_or_404(Blog, pk=blog_id)
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
    if (profile is None):
        raise Http404

    Subscription.objects.filter(user=profile, blog=blog).delete()

    context = { 'thing'         : blog,
                'thing_type'    : u'blog',
                'thing_url'     : reverse('blog', args=[blog.id]),
                'page_title'    : u'Unsubscribe blog '+blog.title,
                'error_title'   : error_title,
                'error_messages': error_messages,
                'user_dashboard': True,
                'profile'       : profile,
        }

    return render(request, 'castle/unsubscribed.html', context)
    
#-----------------------------------------------------------------------------
@login_required
def new_blog(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    if ((profile is None) or (not request.user.has_perm("castle.post_blog"))):
        raise Http404

    # Build context and render page
    context = { 'profile'       : profile,
                'blog'          : Blog(),      # Create blank blog for default purposes
                'page_title'    : u'Write new blog',
                'length_limit'  : 20480,
                'length_min'    : 60,
                'user_dashboard': 1,
            }

    return render(request, 'castle/edit_blog.html', context)

#-----------------------------------------------------------------------------
@login_required
def edit_blog(request, blog_id):
    # Get blog
    blog = get_object_or_404(Blog, pk=blog_id)

    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    if ((profile is None) or (not request.user.has_perm("castle.post_blog"))):
        raise Http404

    # Build context and render page
    context = { 'profile'       : profile,
                'blog'          : blog,
                'page_title'    : u'Edit blog '+blog.title,
                'length_limit'  : 20480,
                'length_min'    : 60,
                'user_dashboard': 1,
            }

    return render(request, 'castle/edit_blog.html', context)

#-----------------------------------------------------------------------------
@login_required
@transaction.atomic
def submit_blog(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    if ((profile is None) or (not request.user.has_perm("castle.post_blog"))):
        raise Http404

    # Get bits and bobs
    errors     = []
    blog       = get_foo(request.POST, Blog,  'bid')
    new_blog   = (blog is None)
    was_draft  = False
    if (not new_blog):         # Remember if the blog was draft
        was_draft = blog.draft
    draft      = request.POST.get('is_draft', False)
    bbcode     = request.POST.get('is_bbcode', False)

    if (not profile.email_authenticated()):
        errors.append(u'You must have authenticated your e-mail address before posting a blog');
    else:
        # Get blog object, either existing or new
        if (blog is None):
            blog = Blog(user = profile)

        # Populate blog object with data from submitted form
        blog.title  = request.POST.get('title', '')
        blog.body   = request.POST.get('body', '')
        blog.draft  = draft
        blog.bbcode = bbcode

        # Condense all end-of-line markers into \n
        blog.body = re_crlf.sub(u"\n", blog.body)

        # Check for submission errors
        if (len(blog.title) < 1):
            errors.append(u'Blog title must be at least 1 character long')

        l = len(blog.body)
        if ((not blog.draft) and (l < 60)):
            errors.append(u'Blog body must be at least 60 characters long')

        if (l > 20480):
            errors.append(u'Blog is over 20480 characters (currently ' + unicode(l) + u')')

    # If there have been errors, re-display the page
    if (errors):
    # Build context and render page
        context = { 'profile'       : profile,
                    'blog'          : blog,
                    'page_title'    : u'Edit blog '+blog.title,
                    'length_limit'  : 20480,
                    'length_min'    : 60,
                    'user_dashboard': 1,
                    'error_title'   : 'Blog submission unsuccessful',
                    'error_messages': errors,
                }

        return render(request, 'castle/edit_blog.html', context)

    # Is the blog being published?
    if (not draft and (was_draft or new_blog)):
        blog.ptime = timezone.now()

    # Set modification time
    blog.mtime = timezone.now()

    # No problems, update the database and redirect
    blog.save()

    # Auto-subscribe to e-mail notifications according to user's preferences
    if (new_blog):
        if (profile.email_flags & Profile.AUTOSUBSCRIBE_ON_BLOG):
            Subscription.objects.get_or_create(user=profile, blog=blog)

    return HttpResponseRedirect(reverse('blog', args=(blog.id,)))

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
#@login_required
def profile_view(request, error_title=None, error_messages=None):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Do e-mail subscription bits
    email_flags = []

    new_email_flag_entry(request, email_flags, profile, Profile.AUTOSUBSCRIBE_ON_STORY, u'when you publish a story')
    new_email_flag_entry(request, email_flags, profile, Profile.AUTOSUBSCRIBE_ON_STORY_COMMENT, u'when you comment on a story')
    new_email_flag_entry(request, email_flags, profile, Profile.AUTOSUBSCRIBE_ON_BLOG, u'when you publish a blog post', 'castle.post_blog')
    new_email_flag_entry(request, email_flags, profile, Profile.AUTOSUBSCRIBE_ON_BLOG_COMMENT, u'when you comment on a blog post')
    new_email_flag_entry(request, email_flags, profile, Profile.AUTOSUBSCRIBE_ON_PROMPT, u'when you publish a prompt')
    new_email_flag_entry(request, email_flags, profile, Profile.AUTOSUBSCRIBE_ON_PROMPT_COMMENT, u'when you comment on a prompt')
    new_email_flag_entry(request, email_flags, profile, Profile.AUTOSUBSCRIBE_ON_CHALLENGE, u'when you publish a challenge')
    new_email_flag_entry(request, email_flags, profile, Profile.AUTOSUBSCRIBE_ON_CHALLENGE_COMMENT, u'when you comment on a challenge')
    new_email_flag_entry(request, email_flags, profile, Profile.AUTOSUBSCRIBE_TO_PREQUEL, u'when someone prequels a story you wrote')
    new_email_flag_entry(request, email_flags, profile, Profile.AUTOSUBSCRIBE_TO_SEQUEL, u'when someone sequels a story you wrote')
    new_email_flag_entry(request, email_flags, profile, Profile.AUTOSUBSCRIBE_TO_CHALLENGE_ENTRY, u'when someone enters a story in a challenge you created')

    # Page title
    if (profile):
        page_title = u'Profile of '+profile.pen_name
    else:
        page_title = u'Register new user'

    # Build context and render page
    context = { 'profile'       : profile,
                'length_limit'  : 1024,
                'length_min'    : 1,
                'page_title'    : page_title,
                'email_flags'   : email_flags,
                'error_title'   : error_title,
                'error_messages': error_messages,
            }

    return render(request, 'castle/profile.html', context)

#-----------------------------------------------------------------------------
@transaction.atomic
def submit_profile(request):
    # Get user profile
    new_registration = False
    new_email_addr = False
    if (request.user.is_authenticated()):
        profile = request.user.profile
    else:
        profile = Profile()
        new_registration = True

    # Get data from form
    pen_name        	= request.POST.get('pen_name', '')
    password        	= request.POST.get('password', '')
    new_password    	= request.POST.get('new_password', '')
    password_again  	= request.POST.get('password', '')
    site_url        	= request.POST.get('site_url', '')
    site_name       	= request.POST.get('site_name', '')
    facebook_username	= request.POST.get('facebook_username', '')
    twitter_username	= request.POST.get('twitter_username', '')
    wattpad_username	= request.POST.get('wattpad_username', '')
    biography       	= request.POST.get('biography', '')
    mature          	= request.POST.get('mature', '')
    email_addr      	= request.POST.get('email_addr', '')
    rules           	= request.POST.get('rules', False)

    # Update and verify profile object
    errors     = []
    if (pen_name and ((profile.pen_name_uc is None) or (pen_name.upper() != profile.pen_name_uc))):
        # Pen name is set and it is different from the stored value
        profile.pen_name = pen_name
        profile.pen_name_uc = pen_name.upper()
        if (Profile.objects.filter(pen_name_uc = pen_name.upper())):
            errors.append(u'Sorry, that pen-name is already taken')

    if (new_registration):
        # Password check for new user
        if (len(password) < 6):
            errors.append(u'Password must be at least 6 characters')
        if (password != password_again):
            errors.append(u'Password and password check did not match')
    elif (new_password):
        if (not request.user.check_password(password)):
            errors.append(u'Old password incorrect')
        if (len(new_password) < 6):
            errors.append(u'Password must be at least 6 characters')
        if (new_password != password_again):
            errors.append(u'Password and password check did not match')
    elif (password):
        if (not request.user.check_password(password)):
            errors.append(u'Old password incorrect')

    if (site_url == ''):
        profile.site_url = None
    else:
        profile.site_url = site_url
    
    if (site_name == ''):
        profile.site_name = None
    else:    
        profile.site_name = site_name
        
    if (facebook_username == ''):
        profile.facebook_username = None
    else:
        profile.facebook_username = facebook_username
        
    if (twitter_username == ''):
        profile.twitter_username = None
    else:
        profile.twitter_username = twitter_username
        
    if (wattpad_username == ''):
        profile.wattpad_username = None
    else:
        profile.wattpad_username = wattpad_username
    
    if (new_registration or biography):
        # Condense all end-of-line markers into \n
        profile.biography = re_crlf.sub(u"\n", biography)

        if (len(biography) < 2):
            errors.append(u'Biography must be at least 2 characters.  Tell us a bit about yourself')
    if (mature):
        profile.mature = True
    else:
        profile.mature = False
    if ((new_registration or email_addr) and not validate_email_addr(email_addr)):
        errors.append(u'Sorry, but we need an e-mail address')
    if (not rules):
        errors.append(u'You need to agree to the rules before you play')

    # E-mail preferences
    eflags = 0
    flag = 1
    for i in range(Profile.NUM_EMAIL_FLAGS):
        if 'ef_{}'.format(flag) in request.POST:
            eflags = eflags | flag
        flag *= 2
    profile.email_flags = eflags

    # If user is changing e-mail address, they need their password too
    if (not new_registration and (
            (email_addr and email_addr != profile.email_addr) or
            (pen_name   and pen_name.upper() != profile.pen_name_uc))):
        if (not password):
            errors.append(u'When you change your pen name or e-mail address, you need to supply your password too.')
        elif (not request.user.check_password(password)):
            errors.append(u'Old password incorrect')
        else:
            new_email_addr = True

    # Set modification time
    time_now = timezone.now()
    profile.mtime = time_now

    # If there have been errors, re-display the page
    if (errors):
        if (new_registration):
            return profile_view(request, 'Registration unsuccessful', errors)
        else:
            return profile_view(request, 'Profile update unsuccessful', errors)


    # If new registration, we should create a new Django user
    if (new_registration):
        # Create a temporary user name because we need to call the
        # user something whilst we create the profile entry
        # We then go back and update the Django user name to express clearly
        # the connection with the profile table
        un = u'{:016x}'.format(random64())
        user = User(
            username = u'user{}'+un,
            first_name = u'user',
            last_name = un,
            email = email_addr,
            )
        user.set_password(password)
        user.save()
        profile.user = user
        profile.save()
        un = unicode(profile.id)
        user.username = u'user'+un
        user.last_name = un;
        user.save()
        user = authenticate(username=profile.user.username, password=password)
        login(request, user)
    else:
        profile.save()

    # If this is a new user, or the e-mail address is changed, send a conf email
    if (new_registration or new_email_addr):
        # Get random 64 bit integer
        token = random64()
        token_s = to_signed64(token)
        profile.email_addr = email_addr
        profile.email_auth = token_s
        profile.email_time = time_now
        send_conf_email(profile, token)
        profile.save()

    return HttpResponseRedirect(reverse('author', args=(profile.pen_name,)))

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
def tags(request, tag_name):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    page_num = safe_int(request.GET.get('page_num', 1))

    # Find stories with this tag name (forced to upper case)
    tag_name = tag_name.upper()
    (num_stories, stories) = get_tagged_stories(tag_name, page_num, PAGE_BROWSE)
    if (num_stories == 0):
        # No stories found, give the user
        return tags_null(request, u'No stories tagged '+tag_name)

    label = u'Stories tagged “'+unicode(tag_name)+u'”'
    url = u'/tags/'+urlquote(tag_name)+u'/'

    # Build context and render page
    context = { 'profile'       : profile,
                'stories'       : stories,
                'page_title'    : u'Tag '+tag_name,
                'page_url'      : url,
                'pages'         : bs_pager(page_num, PAGE_BROWSE, num_stories),
                'user_dashboard': 1,
                'label'         : label,
              }
    return render(request, 'castle/browse.html', context)

#-----------------------------------------------------------------------------
def tags_null(request, error_msg = None):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    page_num = safe_int(request.GET.get('page_num', 1))

    # List all the tags
    num_tags = get_num_tags()
    tags     = get_all_tags(page_num, PAGE_ALLTAGS)

    url = u'/tags/'

    error_title = u'Tag not found' if (error_msg) else None
    error_messages = [error_msg] if (error_msg) else None

    # Build context and render page
    context = { 'profile'       : profile,
                'tags'          : tags,
                'page_title'    : u'Tag not found',
                'page_url'      : url,
                'pages'         : bs_pager(page_num, PAGE_ALLTAGS, num_tags),
                'user_dashboard': 1,
                'error_title'   : error_title,
                'error_messages': error_messages,
              }
    return render(request, 'castle/all_tags.html', context)

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
def static_view(request, template_name):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    context = {
        'profile'       : profile
        }
    return render(request, 'castle/'+template_name, context)

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
