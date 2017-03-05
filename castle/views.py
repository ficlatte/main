
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
from .forms import AvatarUploadForm, ChallengeDateForm
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
# Query functions
#-----------------------------------------------------------------------------
def get_popular_stories(page_num=1, page_size=10):
    db = getattr(settings, 'DB', 'mysql')
    if (db == 'mysql'):
        return Story.objects.raw(
        "SELECT s.id as id, " +
        "SUM(1/(TIMESTAMPDIFF(day, l.ctime, NOW())+1)) AS score " +
        "FROM castle_storylog AS l " +
        "LEFT JOIN castle_story AS s ON s.id=l.story_id " +
        "WHERE l.user_id != s.user_id " +
        "AND l.log_type = " + str(StoryLog.VIEW) + " "+
        "AND ((s.draft IS NULL) OR (NOT s.draft)) " +
        "GROUP BY l.story_id ORDER BY score DESC LIMIT " +
        str((page_num-1) * page_size) + "," + str(page_size))
    elif (db == 'postgres'):
        return Story.objects.raw(
        "SELECT s.id as id, " +
        "SUM(1/(date_part('day', NOW() - l.ctime)+1)) AS score " +
        "FROM castle_storylog AS l " +
        "LEFT JOIN castle_story AS s ON s.id=l.story_id " +
        "WHERE l.user_id != s.user_id " +
        "AND l.log_type = " + str(StoryLog.VIEW) +" "+
        "AND ((s.draft IS NULL) OR (NOT s.draft)) " +
        "GROUP BY s.id ORDER BY score DESC LIMIT " + str(page_size) +" "+
        "OFFSET " + str((page_num-1) * page_size))
    return Story.objects.all()

#-----------------------------------------------------------------------------
def get_active_stories(page_num=1, page_size=10):
    first = (page_num-1) * page_size
    last  = first + page_size
    return Story.objects.filter(activity__isnull=False, activity__gt = 0).order_by('-activity')[first:last]

#-----------------------------------------------------------------------------
def get_num_active_stories():
    return Story.objects.filter(activity__gt = 0).count()

#-----------------------------------------------------------------------------
def get_recent_stories(page_num=1, page_size=10):
    first = (page_num-1) * page_size
    last  = first + page_size
    return Story.objects.filter(draft = False).order_by('-ptime')[first:last]

#-----------------------------------------------------------------------------
def get_old_stories(page_size=10):
    total = Story.objects.filter(draft = False).count()
    end = 0 if (total < page_size) else (total - page_size)
    first = randint(0, end)
    last  = first + page_size
    return Story.objects.filter(draft = False).order_by('ptime')[first:last]
    
#-----------------------------------------------------------------------------
def get_random_story(page_size=10):
    total = Story.objects.filter(draft = False).count()
    end = 0 if (total < page_size) else (total - page_size)
    first = randint(0, end)
    story = Story.objects.filter(draft = False).order_by('ptime')[first]
    return story.id
    
#-----------------------------------------------------------------------------
def get_tagged_stories(tag_name, page_num=1, page_size=10):
    num = Tag.objects.filter(tag=tag_name.upper()).count()
    if (num == 0):
        return (0, None)

    first = (page_num-1) * page_size
    last  = first + page_size
    stories = Story.objects.filter(draft = False, tag__tag=tag_name.upper()).order_by('-ptime')[first:last]

    return (num, stories)

#-----------------------------------------------------------------------------
def get_all_tags(page_num=1, page_size=10):
    first = (page_num-1) * page_size
    last  = first + page_size
    return Tag.objects.values('tag').annotate(n=Count('tag')).order_by('tag')[first:last]

#-----------------------------------------------------------------------------
def get_num_tags():
    return Tag.objects.values('tag').distinct().count()

#-----------------------------------------------------------------------------
def get_activity_log(profile, entries):
    if (profile is None):
        return None
    log_entries = StoryLog.objects.exclude(log_type = StoryLog.VIEW).exclude(log_type = StoryLog.RATE).filter(Q(user = profile) | Q(story__user = profile)).order_by('-ctime')[:entries]

    return log_entries

#-----------------------------------------------------------------------------
def get_popular_prompts(page_num=1, page_size=10):
    db = getattr(settings, 'DB', 'mysql')
    if (db == 'mysql'):
        return Prompt.objects.raw(
        "SELECT p.id as id, " +
        "SUM(1/(TIMESTAMPDIFF(day, l.ctime, NOW())+1)) AS score " +
        "FROM castle_storylog AS l " +
        "LEFT JOIN castle_prompt AS p ON p.id=l.prompt_id " +
        "WHERE l.user_id != p.user_id " +
        "AND l.log_type = " + str(StoryLog.VIEW) + " "+
        "GROUP BY l.prompt_id ORDER BY score DESC LIMIT " +
        str((page_num-1) * page_size) + "," + str(page_size))
    elif (db == 'postgres'):
        return Prompt.objects.raw(
        "SELECT p.id as id, " +
        "SUM(1/(date_part('day', NOW() - l.ctime)+1)) AS score " +
        "FROM castle_storylog AS l " +
        "LEFT JOIN castle_prompt AS c ON p.id=l.prompt_id " +
        "WHERE l.user_id != p.user_id " +
        "AND l.log_type = " + str(StoryLog.VIEW) +" "+
        "GROUP BY p.id ORDER BY score DESC LIMIT " + str(page_size) +" "+
        "OFFSET " + str((page_num-1) * page_size))
    return Prompt.objects.all()
    
#-----------------------------------------------------------------------------
def get_active_prompts(page_num=1, page_size=10):
    first = (page_num-1) * page_size
    last  = first + page_size
    return Prompt.objects.filter(activity__isnull=False, activity__gt = 0).order_by('-activity')[first:last]
    
#-----------------------------------------------------------------------------
def get_num_active_prompts():
    return Prompt.objects.filter(activity__gt = 0).count()
    
#-----------------------------------------------------------------------------
def get_recent_prompts(page_num=1, page_size=10):
    first = (page_num-1) * page_size
    last  = first + page_size
    return Prompt.objects.all().order_by('-ctime')[first:last]
    
#-----------------------------------------------------------------------------
def get_old_prompts(page_size=10):
    total = Prompt.objects.all().count()
    end = 0 if (total < page_size) else (total - page_size)
    first = randint(0, end)
    last  = first + page_size
    return Prompt.objects.all().order_by('ctime')[first:last]

#-----------------------------------------------------------------------------
def get_popular_challenges(page_num=1, page_size=10):
    db = getattr(settings, 'DB', 'mysql')
    if (db == 'mysql'):
        return Challenge.objects.raw(
        "SELECT c.id as id, " +
        "SUM(1/(TIMESTAMPDIFF(day, l.ctime, NOW())+1)) AS score " +
        "FROM castle_storylog AS l " +
        "LEFT JOIN castle_challenge AS c ON c.id=l.challenge_id " +
        "WHERE l.user_id != c.user_id " +
        "AND l.log_type = " + str(StoryLog.VIEW) + " "+
        "GROUP BY l.challenge_id ORDER BY score DESC LIMIT " +
        str((page_num-1) * page_size) + "," + str(page_size))
    elif (db == 'postgres'):
        return Challenge.objects.raw(
        "SELECT c.id as id, " +
        "SUM(1/(date_part('day', NOW() - l.ctime)+1)) AS score " +
        "FROM castle_storylog AS l " +
        "LEFT JOIN castle_challenge AS c ON c.id=l.challenge_id " +
        "WHERE l.user_id != c.user_id " +
        "AND l.log_type = " + str(StoryLog.VIEW) +" "+
        "GROUP BY c.id ORDER BY score DESC LIMIT " + str(page_size) +" "+
        "OFFSET " + str((page_num-1) * page_size))
    return Challenge.objects.all()
    
#-----------------------------------------------------------------------------
def get_active_challenges(page_num=1, page_size=10):
    first = (page_num-1) * page_size
    last  = first + page_size
    return Challenge.objects.filter(activity__isnull=False, activity__gt = 0).order_by('-activity')[first:last]
    
#-----------------------------------------------------------------------------
def get_num_active_challenges():
    return Challenge.objects.filter(activity__gt = 0).count()
    
#-----------------------------------------------------------------------------
def get_recent_challenges(page_num=1, page_size=10):
    first = (page_num-1) * page_size
    last  = first + page_size
    return Challenge.objects.all().order_by('-ctime')[first:last]

#-----------------------------------------------------------------------------
def get_recent_winners(page_num=1, page_size=10):
    first = (page_num-1) * page_size
    last  = first + page_size
    return Story.objects.filter(challenge__winner_id=F('id'), challenge__winner_id__isnull=False).order_by('-ctime')[first:last]

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
# Views
#-----------------------------------------------------------------------------
def home(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
        
    # Has the author's email been confirmed?
    email_conf = (profile.email_auth == 0)

    # Get featured story
    featured_id = Misc.objects.filter(key='featured')
    featured = None
    if (featured_id):
        featured_query = Story.objects.filter(id=featured_id[0].i_val)
        if (featured_query):
            featured = featured_query[0]
    
    # Get latest challenge
    challenge = Challenge.objects.all().order_by('-id')[0]
    
    # Get latest prompt
    prompt = Prompt.objects.all().order_by('-id')[0]

    # Suppress story if marked as mature and either the user is not logged in
    # or the user has not enabled viewing of mature stories
    suppressed = False
    if (featured.mature):
        if ( (not profile) or ((featured.user != profile) and (not profile.mature))):
            suppressed = True

    # Get latest blog
    try:
        blog = Blog.objects.all().order_by('-id')[:3]
    except IndexError:
        blog = None

    # Build context and render page
    context = { 'profile'       : profile,
                'blog_latest'   : blog,
                'featured'      : featured,
                'challenge'		: challenge,
                'prompt'		: prompt,
                'email_conf'	: email_conf,
                'popular'       : get_popular_stories(1,4),
                'active'        : get_active_stories(1,10),
                'recent'        : get_recent_stories(1,10),
                'old'           : get_old_stories(10),
                'random'		: get_random_story(),
                'activity_log'  : get_activity_log(profile, 10),
                'user_dashboard': 1,
                'suppressed'    : suppressed,
              }
    return render(request, 'castle/index.html', context)

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
# Story views
#-----------------------------------------------------------------------------
def story_view(request, story_id, comment_text=None, user_rating=None, error_title='', error_messages=None):
    story = get_object_or_404(Story, pk=story_id)

    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Is logged-in user the author?
    author = story.user
    owner = ((profile is not None) and (profile == author))

    # Is logged-in user the challenge owner?
    challenge = story.challenge
    ch_owner = None
    if story.challenge:
        ch_owner = ((profile is not None) and (profile == story.challenge.user))

    # Collect prequels and sequels
    prequels = []
    if (story.sequel_to):
        prequels.append(story.sequel_to)
    prequels.extend(story.prequels.filter(Q(draft=False) | Q(user=profile)))

    sequels = []
    if (story.prequel_to):
        sequels.append(story.prequel_to)
    sequels.extend(story.sequels.filter(Q(draft=False) | Q(user=profile)))

    # Get user rating in numeric and string forms
    rating = Rating.objects.filter(story=story).exclude(user=story.user).aggregate(avg=Avg('rating'))['avg']
    rating_str = u'{:.2f}'.format(rating) if (rating) else ''

    # Get comments
    page_num = safe_int(request.GET.get('page_num', 1))
    comments = story.comment_set.all().order_by('ctime')[(page_num-1)*PAGE_COMMENTS:page_num*PAGE_COMMENTS]

    # Log view
    if (profile):
        log = StoryLog(
            user = profile,
            story = story,
            log_type = StoryLog.VIEW
            )
        log.save()

    # Count how many times the story has been viewed and rated
    viewed = StoryLog.objects.filter(story = story).exclude(user = author).count()
    rated  = Rating.objects.filter(story = story).exclude(user=author).count()

    # Get current user's rating
    if ((profile) and (user_rating is None)):
        rating_set = Rating.objects.filter(story=story, user=profile)
        if (rating_set):
            user_rating = rating_set[0].rating

    # Suppress story if marked as mature and either the user is not logged in
    # or the user has not enabled viewing of mature stories
    suppressed = False
    if (story.mature):
        if ( (not profile) or ((story.user != profile) and (not profile.mature))):
            suppressed = True

    # Is user subscribed?
    subscribed = False
    if ((profile) and (Subscription.objects.filter(story=story, user=profile).count()>0)):
        subscribed = True

    # Build context and render page
    context = { 'profile'       : profile,
                'author'        : story.user,
                'story'         : story,
                'prequels'      : prequels,
                'sequels'       : sequels,
                'rating_str'    : rating_str,
                'rating_num'    : rating,
                'comments'      : comments,
                'subscribed'    : subscribed,
                'page_title'    : story.title,
                'page_url'      : u'/stories/'+unicode(story_id)+u'/',
                'pages'         : bs_pager(page_num, PAGE_COMMENTS, story.comment_set.count()),
                'story_sidepanel':1 ,
                'owner'         : owner,
                'challenge'     : challenge,
                'ch_owner'      : ch_owner,
                'viewed'        : viewed,
                'rated'         : rated,
                'comment_text'  : comment_text, # in case of failed comment submission
                'user_rating'   : user_rating,
                'suppressed'    : suppressed,
                'error_title'   : error_title,
                'error_messages': error_messages,
                }

    return render(request, 'castle/story.html', context)

#-----------------------------------------------------------------------------
@login_required
def new_story(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Get prequel, sequel and prompt data from the GET request
    prequel_to = get_foo(request.GET, Story,  'prequel_to')
    sequel_to  = get_foo(request.GET, Story,  'sequel_to')
    prompt     = get_foo(request.GET, Prompt, 'prid')
    challenge  = get_foo(request.GET, Challenge, 'chid')

    # Create a blank story to give the template some defaults
    story = Story(prequel_to = prequel_to,
                  sequel_to  = sequel_to,
                  prompt     = prompt,
                  prompt_text = u'',
                  challenge = challenge,
                  )

    # Build context and render page
    context = { 'profile'       : profile,
                'story'         : story,
                'page_title'    : u'Write new story',
                'tags'          : u'',
                'length_limit'  : 1024,
                'length_min'    : 60,
                'user_dashboard': 1,
            }

    return render(request, 'castle/edit_story.html', context)

#-----------------------------------------------------------------------------
@login_required
def edit_story(request, story_id):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Get story
    story = get_object_or_404(Story, pk=story_id)

    # User can only edit their own stories
    if (story.user != profile):
        raise Http404

    # Get tags
    tags = ", ".join(story.tag_set.values_list('tag', flat=True))

    # Build context and render page
    context = { 'profile'       : profile,
                'story'         : story,
                'page_title'    : u'Edit story '+story.title,
                'tags'          : tags,
                'length_limit'  : 1024,
                'length_min'    : 60,
                'user_dashboard': 1,
            }

    return render(request, 'castle/edit_story.html', context)

#-----------------------------------------------------------------------------
@login_required
def delete_story(request, story_id):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Get story
    story = get_object_or_404(Story, pk=story_id)

    # Only story's author can delete a story
    if (story.user != profile):
        raise Http404

    # Do deletion
    story.delete()

    # Indicate successful deletion
    return render(request, 'castle/status_message.html',
                    {'profile': profile,
                    'status_type': 'success',
                    'status_message': u'Story deleted',})

#-----------------------------------------------------------------------------
@login_required
@transaction.atomic
def submit_story(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Get bits and bobs
    errors     = []
    story      = get_foo(request.POST, Story,  'sid')
    prequel_to = get_foo(request.POST, Story,  'prequel_to')
    sequel_to  = get_foo(request.POST, Story,  'sequel_to')
    challenge  = get_foo(request.POST, Challenge, 'chid')
    prompt     = get_foo(request.POST, Prompt, 'prid')
    tags       = request.POST.get('tag_list', '')
    ptext      = request.POST.get('prompt_text', None)
    new_story  = (story is None)
    was_draft  = False
    if (not new_story):         # Remember if the story was draft
        was_draft = story.draft

    if (not profile.email_authenticated()):
        errors.append(u'You must have authenticated your e-mail address before posting a story')

    # Get story object, either existing or new
    if (story is None):
        story = Story(user       = profile,
                      prequel_to = prequel_to,
                      sequel_to  = sequel_to,
                      prompt     = prompt,
                      challenge  = challenge,
                      )

    # Populate story object with data from submitted form
    story.title  = request.POST.get('title', '')
    story.body   = request.POST.get('body', '')
    story.mature = request.POST.get('is_mature', False)
    story.draft  = request.POST.get('is_draft', False)
    story.prompt_text = ptext
    if challenge:
		    story.challenge_id = challenge.id

    # Condense all end-of-line markers into \n
    story.body = re_crlf.sub(u"\n", story.body)

    # Check for submission errors
    if (len(story.title) < 1):
        errors.append(u'Story title must be at least 1 character long')

    l = len(story.body)
    if ((not story.draft) and (l < 60)):
        errors.append(u'Story body must be at least 60 characters long')

    if ((not story.draft) and (l > 1024)):
        errors.append(u'Story is over 1024 characters (currently ' + unicode(l) + u')')

    if ((    story.draft) and (l > 1536)):
        errors.append(u'Draft is over 1536 characters (currently ' + unicode(l) + u')')

    # If there have been errors, re-display the page
    if (errors):
    # Build context and render page
        context = { 'profile'       : profile,
                    'story'         : story,
                    'page_title'    : u'Edit story '+story.title,
                    'tags'          : tags,
                    'length_limit'  : 1024,
                    'length_min'    : 60,
                    'user_dashboard': 1,
                    'error_title'   : 'Story submission unsuccessful',
                    'error_messages': errors,
                }

        return render(request, 'castle/edit_story.html', context)

    # Is the story being published?
    if (not story.draft and (was_draft or new_story)):
        story.ptime = timezone.now()

    # Set modification time
    story.mtime = timezone.now()

    # No problems, update the database and redirect
    story.save()

    # Populate tags list
    r = re.compile(r'\s*,\s*')
    tag_list = r.split(tags.upper())
    td = {}

    if (not new_story):
        # Remove old tags on current story before laying the new ones down
        story.tag_set.all().delete()
    for t in tag_list:
        if (len(t) > 1):
            if (t not in td):   # Strip out duplicates using dict 'td'
                td[t] = 1
                tag_object = Tag(story=story, tag=t)
                tag_object.save()

    # Auto-subscribe to e-mail notifications according to user's preferences
    if (new_story):
        if (profile.email_flags & Profile.AUTOSUBSCRIBE_ON_STORY):
            Subscription.objects.get_or_create(user=profile, story=story)

    # Make log entry
    log_type = StoryLog.WRITE
    quel = None
    chal = None
    if (sequel_to):
        log_type = StoryLog.SEQUEL
        quel = sequel_to
    elif (prequel_to):
        log_type = StoryLog.PREQUEL
        quel = prequel_to
    elif (challenge):
        log_type = StoryLog.CHALLENGE_ENT
        chal = Challenge.objects.get(id=int(request.POST.get('chid')))

    if (not new_story):
        log_type = StoryLog.STORY_MOD

    log = StoryLog(
        user = profile,
        story = story,
        quel = quel,
        log_type = log_type,
        prompt = prompt,
        challenge = chal
    )
    log.save()

    return HttpResponseRedirect(reverse('story', args=(story.id,)))

#-----------------------------------------------------------------------------
def browse_stories(request, dataset=0):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    page_num = safe_int(request.GET.get('page_num', 1))

    if (dataset == 1):
        stories = get_active_stories(page_num, PAGE_BROWSE)
        num_stories = get_num_active_stories()
        label = u'Active stories'
        url = u'/stories/active/'
    elif (dataset == 2):
        stories = get_popular_stories(page_num, PAGE_BROWSE)
        num_stories = Story.objects.exclude(draft = True).count()
        label = u'Popular stories'
        url = u'/stories/popular/'
    else:
        stories = get_recent_stories(page_num, PAGE_BROWSE)
        num_stories = Story.objects.exclude(draft = True).count()
        label = u'Recent stories'
        url = u'/stories/'

    # Build context and render page
    context = { 'profile'       : profile,
                'stories'       : stories,
                'page_title'    : u'Stories, page {}'.format(page_num),
                'page_url'      : url,
                'pages'         : bs_pager(page_num, PAGE_BROWSE, num_stories),
                'user_dashboard': 1,
                'label'         : label,
              }
    return render(request, 'castle/browse.html', context)

#-----------------------------------------------------------------------------
def active_stories(request):
    return browse_stories(request, 1)

#-----------------------------------------------------------------------------
def popular_stories(request):
    return browse_stories(request, 2)

#-----------------------------------------------------------------------------
# Prompt views
#-----------------------------------------------------------------------------
def browse_prompts(request, dataset=0):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    page_num = safe_int(request.GET.get('page_num', 1))

    if (dataset == 1):
        prompts = get_active_prompts(page_num, PAGE_BROWSE)
        num_prompts = get_num_active_prompts()
        label = u'Active prompts'
        url = u'/prompts/active/'
    elif (dataset == 2):
        prompts = get_popular_prompts(page_num, PAGE_BROWSE)
        num_prompts = Prompt.objects.all().count()
        label = u'Popular prompts'
        url = u'/prompts/popular/'
    else:
        prompts = get_recent_prompts(page_num, PAGE_BROWSE)
        num_prompts = Prompt.objects.all().count()
        label = u'Recent prompts'
        url = u'/prompts/recent/'

    # Build context and render page
    context = { 'profile'       : profile,
                'prompts'    	: prompts,
                'page_title'    : u'Prompts, page {}'.format(page_num),
                'page_url'      : url,
                'pages'         : bs_pager(page_num, PAGE_BROWSE, num_prompts),
                'user_dashboard': 1,
                'label'         : label,
              }
    return render(request, 'castle/prompts_recent.html', context)
    
#-----------------------------------------------------------------------------
def active_prompts(request):
    return browse_prompts(request, 1)

#-----------------------------------------------------------------------------
def popular_prompts(request):
    return browse_prompts(request, 2)

#-----------------------------------------------------------------------------
def prompts(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
        
    # Has the author's email been confirmed?
    email_conf = (profile.email_auth == 0)

    # Get featured prompt
    featured_id = Misc.objects.filter(key='featured_prompt')
    featured = None
    if (featured_id):
        featured_query = Prompt.objects.filter(id=featured_id[0].i_val)
        if (featured_query):
            featured = featured_query[0]

    # Build context and render page
    context = { 'profile'       : profile,
                'prompts'       : prompts,
                'featured'		: featured,
                'popular'		: get_popular_prompts(1,4),
                'active'		: get_active_prompts(1,10),
                'recent'		: get_recent_prompts(1,10),
                'old'			: get_old_prompts(10),
                'page_title'    : u'Prompts',
                'prompt_button' : (profile is not None),
                'email_conf'	: email_conf,
                'user_dashboard': (profile is not None),
                'page_url'      : u'/prompts/',
            }


    return render(request, 'castle/prompts.html', context)

#-----------------------------------------------------------------------------
def prompt_view(request, prompt_id):
    # Get prompt
	prompt = get_object_or_404(Prompt, pk=prompt_id)

    # Get user profile
	profile = None
	if (request.user.is_authenticated()):
		profile = request.user.profile
		
    # Has the author's email been confirmed
	email_conf = (profile.email_auth == 0)

    # Get stories inspired by prompt
	page_num = safe_int(request.GET.get('page_num', 1))
	stories = prompt.story_set.exclude(draft=True).order_by('ctime')[(page_num-1)*PAGE_STORIES:page_num*PAGE_STORIES]
	num_stories = prompt.story_set.exclude(draft=True).count()

    # Get comments
	page_num = safe_int(request.GET.get('page_num', 1))
	comments = prompt.comment_set.all().order_by('ctime')[(page_num-1)*PAGE_COMMENTS:page_num*PAGE_COMMENTS]

    # Prompt's owner gets an edit link
	owner = ((profile is not None) and (profile == prompt.user))
    
	# Log view
	if (profile):
		log = StoryLog(
			user = profile,
			prompt = prompt,
			log_type = StoryLog.VIEW
			)
		log.save()

    # Suppress challenge if marked as mature and either the user is not logged in
    # or the user has not enabled viewing of mature challenges
	suppressed = False
	if (prompt.mature):
		if ( (not profile) or ((prompt.user != profile) and (not profile.mature))):
			suppressed = True
			
    # Is user subscribed?
	subscribed = False
	if ((profile) and (Subscription.objects.filter(prompt=prompt, user=profile).count()>0)):
		subscribed = True

    # Build context and render page
	context = { 'profile'       : profile,
				'prompt'        : prompt,
				'stories'       : stories,
				'comments'		: comments,
				'owner'         : owner,
				'subscribed'	: subscribed,
				'page_title'    : u'Prompt '+prompt.title,
				'email_conf'	: email_conf,
				'prompt_sidepanel' : 1,
				'page_url'      : u'/prompts/'+unicode(prompt.id)+u'/',
				'pages'         : bs_pager(page_num, PAGE_STORIES, num_stories),
				'suppressed'    : suppressed,
			   }

	return render(request, 'castle/prompt.html', context)

#-----------------------------------------------------------------------------
@login_required
def new_prompt(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Create a blank prompt to give the template some defaults
    prompt = Prompt()

    # Build context and render page
    context = { 'profile'       : profile,
                'prompt'        : prompt,
                'page_title'    : u'Write new prompt',
                'length_limit'  : 256,
                'length_min'    : 30,
                'user_dashboard': 1,
            }

    return render(request, 'castle/edit_prompt.html', context)

#-----------------------------------------------------------------------------
@login_required
def edit_prompt(request, prompt_id):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Get prompt
    prompt = get_object_or_404(Prompt, pk=prompt_id)

    # User can only edit their own stories
    if (prompt.user != profile):
        raise Http404

    # Build context and render page
    context = { 'profile'       : profile,
                'prompt'        : prompt,
                'page_title'    : u'Edit prompt '+prompt.title,
                'length_limit'  : 256,
                'length_min'    : 30,
                'user_dashboard': 1,
            }

    return render(request, 'castle/edit_prompt.html', context)

#-----------------------------------------------------------------------------
@login_required
@transaction.atomic
def submit_prompt(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Get bits and bobs
    errors     = []
    prompt     = get_foo(request.POST, Prompt, 'prid')
    new_prompt = (prompt is None)

    if (not profile.email_authenticated()):
        errors.append(u'You must have authenticated your e-mail address before posting a prompt')
    else:
        # Get prompt object, either existing or new
        #new_prompt = False
        if (prompt is None):
            prompt = Prompt(user    =   profile)
            #new_prompt = True

        # Populate prompt object with data from submitted form
        prompt.title  = request.POST.get('title', '')
        prompt.body   = request.POST.get('body', '')
        prompt.mature = request.POST.get('is_mature', False)

        # Condense all end-of-line markers into \n
        prompt.body = re_crlf.sub(u"\n", prompt.body)

        # Check for submission errors
        if (len(prompt.title) < 1):
            errors.append(u'Prompt title must be at least 1 character long')

        l = len(prompt.body)
        if (l < 30):
            errors.append(u'Prompt body must be at least 30 characters long')

        if (l > 256):
            errors.append(u'Prompt is over 256 characters (currently ' + unicode(l) + u')')

    # If there have been errors, re-display the page
    if (errors):
    # Build context and render page
        context = { 'profile'       : profile,
                    'prompt'        : prompt,
                    'length_limit'  : 256,
                    'length_min'    : 30,
                    'page_title'    : u'Edit prompt '+prompt.title,
                    'user_dashboard': 1,
                    'error_title'   : 'Prompt submission unsuccessful',
                    'error_messages': errors,
                }

        return render(request, 'castle/edit_prompt.html', context)

    # Is the prompt new?
    if new_prompt is None:
        prompt.ctime = timezone.now()

    # Set modification time
    prompt.mtime = timezone.now()

    # No problems, update the database and redirect
    prompt.save()
    
        # Auto-subscribe to e-mail notifications according to user's preferences
    if (new_prompt):
        if (profile.email_flags & Profile.AUTOSUBSCRIBE_ON_PROMPT):
            Subscription.objects.get_or_create(user=profile, prompt=prompt)

    # Log entry
    log_type = StoryLog.PROMPT
    if (not new_prompt):
        log_type = StoryLog.PROMPT_MOD
    log = StoryLog(
        user = profile,
        log_type = log_type,
        prompt = prompt
    )
    log.save()

    return HttpResponseRedirect(reverse('prompt', args=(prompt.id,)))

#-----------------------------------------------------------------------------
# Challenge views
#-----------------------------------------------------------------------------
def browse_challenges(request, dataset=0):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    page_num = safe_int(request.GET.get('page_num', 1))

    if (dataset == 1):
        challenges = get_active_challenges(page_num, PAGE_BROWSE)
        num_challenges = get_num_active_challenges()
        label = u'Active challenges'
        url = u'/challenges/active/'
    elif (dataset == 2):
        challenges = get_popular_challenges(page_num, PAGE_BROWSE)
        num_challenges = Challenge.objects.all().count()
        label = u'Popular challenges'
        url = u'/challenges/popular/'
    else:
        challenges = get_recent_challenges(page_num, PAGE_BROWSE)
        num_challenges = Challenge.objects.all().count()
        label = u'Recent challenges'
        url = u'/challenges/recent/'

    # Build context and render page
    context = { 'profile'       : profile,
                'challenges'    : challenges,
                'page_title'    : u'Challenges, page {}'.format(page_num),
                'page_url'      : url,
                'pages'         : bs_pager(page_num, PAGE_BROWSE, num_challenges),
                'user_dashboard': 1,
                'label'         : label,
              }
    return render(request, 'castle/challenges_recent.html', context)
    
#-----------------------------------------------------------------------------
def active_challenges(request):
    return browse_challenges(request, 1)

#-----------------------------------------------------------------------------
def popular_challenges(request):
    return browse_challenges(request, 2)

#-----------------------------------------------------------------------------
def challenges(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
        
    # Has the author's email been confirmed?
    email_conf = (profile.email_auth == 0)
    
    # Get featured challenge
    featured_id = Misc.objects.filter(key='featured_challenge')
    featured = None
    if (featured_id):
        featured_query = Challenge.objects.filter(id=featured_id[0].i_val)
        if (featured_query):
            featured = featured_query[0]

    # Build context and render page
    context = { 'profile'           : profile,
                'challenges'        : challenges,
                'featured'			: featured,
                'popular'			: get_popular_challenges(1,4),
                'active'			: get_active_challenges(1,10),
                'recent'			: get_recent_challenges(1,10),
                'recent_winners'	: get_recent_winners(1,10),
                'page_title'        : u'Challenges',
                'challenge_button'  : (profile is not None),
                'email_conf'		: email_conf,
                'user_dashboard'    : (profile is not None),
                'page_url'          : u'/challenges/',
              }


    return render(request, 'castle/challenges.html', context)

#-----------------------------------------------------------------------------
def challenge_view(request, challenge_id, comment_text=None, error_title='', error_messages=None):
    # Get challenge
	challenge = get_object_or_404(Challenge, pk=challenge_id)

    # Get user profile
	profile = None
	if (request.user.is_authenticated()):
		profile = request.user.profile
		
    # Has the author's email been confirmed?
	email_conf = (profile.email_auth == 0)

    # Get stories inspired by challenge
	page_num = safe_int(request.GET.get('page_num', 1))
	stories = challenge.story_set.exclude(draft=True).order_by('ctime')[(page_num-1)*PAGE_STORIES:page_num*PAGE_STORIES]
	num_stories = challenge.story_set.exclude(draft=True).count()
    
    # Get list of participants
	participants_list = challenge.story_set.exclude(draft=True).values('user__pen_name').distinct()
	participants = Profile.objects.filter(pen_name__in=participants_list)

    # Get comments
	page_num = safe_int(request.GET.get('page_num', 1))
	comments = challenge.comment_set.all().order_by('ctime')[(page_num-1)*PAGE_COMMENTS:page_num*PAGE_COMMENTS]

    # Challenge's owner gets an edit link
	owner = ((profile is not None) and (profile == challenge.user))
    
	# Log view
	if (profile):
		log = StoryLog(
			user = profile,
			challenge = challenge,
			log_type = StoryLog.VIEW
			)
		log.save()

    # Suppress challenge if marked as mature and either the user is not logged in
    # or the user has not enabled viewing of mature challenges
	suppressed = False
	if (challenge.mature):
		if ( (not profile) or ((challenge.user != profile) and (not profile.mature))):
			suppressed = True
			
    # Is user subscribed?
	subscribed = False
	if ((profile) and (Subscription.objects.filter(challenge=challenge, user=profile).count()>0)):
		subscribed = True

    # Build context and render page
	context = { 'profile'             : profile,
				'challenge'           : challenge,
				'stories'             : stories,
				'owner'               : owner,
				'subscribed'		  : subscribed,
				'participants'		  : participants,
				'comments'            : comments,
				'page_title'          : u'Challenge '+challenge.title,
				'challenge_sidepanel' : 1,
				'page_url'            : u'/challenges/'+unicode(challenge.id)+u'/',
				'pages'               : bs_pager(page_num, PAGE_STORIES, num_stories),
				'comment_text'        : comment_text,
				'email_conf'		  : email_conf,
				'suppressed'          : suppressed,
				'error_title'         : error_title,
				'error_messages'      : error_messages,
			 }

	return render(request, 'castle/challenge.html', context)

#-----------------------------------------------------------------------------
@login_required
def new_challenge(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    if request.method == "POST":
        form = ChallengeDateForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.save()
            return redirect('challenge', pk=post.pk)
    else:
        form = ChallengeDateForm()  

    # Build context and render page
    context = { 'profile'       : profile,
                'challenge'     : Challenge(),      # Create blank challenge for default purposes
                'page_title'    : u'Create new challenge',
                'form'          : form,
                'stime'         : timezone.now,
                'etime'         : timezone.now,
                'tags'          : u'',
                'length_limit'  : 1024,
                'length_min'    : 30,
                'user_dashboard': 1,
            }

    return render(request, 'castle/edit_challenge.html', context)

#-----------------------------------------------------------------------------
@login_required
def edit_challenge(request, challenge_id):
    # Get challenge
    challenge = get_object_or_404(Challenge, pk=challenge_id)

    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # User can only edit their own challenges
    if (challenge.user != profile):
        raise Http404

    # Build context and render page
    context = { 'profile'       : profile,
                'challenge'     : challenge,
                'page_title'    : u'Edit challenge '+challenge.title,
                'stime'         : timezone.now,
                'etime'         : timezone.now,
                'length_limit'  : 1024,
                'length_min'    : 30,
                'user_dashboard': 1,
            }

    return render(request, 'castle/edit_challenge.html', context)

#-----------------------------------------------------------------------------
@login_required
@transaction.atomic
def submit_challenge(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Get bits and bobs
    errors     = []
    challenge  = get_foo(request.POST, Challenge,  'chid')
    new_challenge = (challenge is None)

    nowdate = datetime.now().strftime('%Y-%m-%d')

    if (not profile.email_authenticated()):
        errors.append(u'You must have authenticated your e-mail address before creating a challenge');
    else:
        # Get challenge object, either existing or new
        #new_challenge = False
        if (challenge is None):
            challenge = Challenge(user=profile)
            #new_challenge = True

        # Populate challenge object with data from submitted form
        challenge.title  = request.POST.get('title', '')
        challenge.body   = request.POST.get('body', '')
        challenge.mature = request.POST.get('is_mature', False)
        challenge.stime  = request.POST.get('stime', timezone.now)
        challenge.etime  = request.POST.get('etime', timezone.now)

        # Condense all end-of-line markers into \n
        challenge.body = re_crlf.sub(u"\n", challenge.body)

        # Check for submission errors
        if (len(challenge.title) < 1):
            errors.append(u'Challenge title must be at least 1 character long')

        l = len(challenge.body)
        if (l < 30):
            errors.append(u'Challenge body must be at least 30 characters long')

        if (l > 1024):
            errors.append(u'Challenge is over 1024 characters (currently ' + unicode(l) + u')')

        if (challenge.stime < nowdate):
            errors.append(u'Challenge start time cannot be set in the past')

        if (challenge.etime < challenge.stime):
            errors.append(u'Challenge end time cannot be before its start time')

    # If there have been errors, re-display the page
    if (errors):
    # Build context and render page
        context = { 'profile'           : profile,
                    'challenge'         : challenge,
                    'length_limit'      : 1024,
                    'length_min'        : 30,
                    'page_title'        : u'Edit challenge '+challenge.title,
                    'user_dashboard'    : 1,
                    'error_title'       : 'Challenge submission unsuccessful',
                    'error_messages'    : errors,
                }

        return render(request, 'castle/edit_challenge.html', context)

    # Is the prompt new?
    if new_challenge is None:
        challenge.ctime = timezone.now()

    # Set modification time
    challenge.mtime = timezone.now()

    # No problems, update the database and redirect
    challenge.save()
    
    # Auto-subscribe to e-mail notifications according to user's preferences
    if (new_challenge):
        if (profile.email_flags & Profile.AUTOSUBSCRIBE_ON_CHALLENGE):
            Subscription.objects.get_or_create(user=profile, challenge=challenge)

    # Log entry
    log_type = StoryLog.CHALLENGE
    if (not new_challenge):
        log_type = StoryLog.CHALLENGE_MOD
    log = StoryLog(
        user = profile,
        log_type = log_type,
        challenge = challenge,
    )
    log.save()

    return HttpResponseRedirect(reverse('challenge', args=(challenge.id,)))

#-----------------------------------------------------------------------------
@login_required
def challenge_winner(request, challenge_id, story_id):
    # Get challenge
    challenge = get_object_or_404(Challenge, pk=challenge_id)
    story = get_object_or_404(Story, pk=story_id)

    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Only challenge's author can select a winner
    if (challenge.user_id != profile.id):
        raise Http404
    else:
        challenge.winner_id = story_id
        
        # Get winning author
        user = get_object_or_404(Profile, pk=story.user_id)
        
        # Set story winner flag
        story.ch_winner = 1
        story.save()

        # Save winner
        challenge.save()

        # Log view
        log_type = StoryLog.CHALLENGE_WON
        log = StoryLog(
            user = user,
            story = story,
            log_type = log_type,
            challenge = challenge,
        )
        log.save()

    # Indicate successful choice
    return HttpResponseRedirect(reverse('challenge', args=(challenge.id,)))

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
        
    # Has the author's email been confirmed?
    email_conf = (profile.email_auth == 0)

    Subscription.objects.filter(user=profile, blog=blog).delete()

    context = { 'thing'         : blog,
                'thing_type'    : u'blog',
                'thing_url'     : reverse('blog', args=[blog.id]),
                'page_title'    : u'Unsubscribe blog '+blog.title,
                'error_title'   : error_title,
                'error_messages': error_messages,
                'email_conf'	: email_conf,
                'user_dashboard': True,
                'profile'       : profile,
        }

    return render(request, 'castle/unsubscribed.html', context)

#-----------------------------------------------------------------------------
@login_required
def story_unsubscribe(request, story_id, comment_text=None, error_title='', error_messages=None):
    story = get_object_or_404(Story, pk=story_id)
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
    if (profile is None):
        raise Http404
        
    # Has the author's email been confirmed?
    email_conf = (profile.email_auth == 0)

    Subscription.objects.filter(user=profile, story=story).delete()

    context = { 'thing'         : story,
                'thing_type'    : u'story',
                'thing_url'     : reverse('story', args=[story.id]),
                'page_title'    : u'Unsubscribe story '+story.title,
                'error_title'   : error_title,
                'error_messages': error_messages,
                'email_conf'	: email_conf,
                'user_dashboard': True,
                'profile'       : profile,
        }

    return render(request, 'castle/unsubscribed.html', context)

#-----------------------------------------------------------------------------
@login_required
def story_subscribe(request, story_id, comment_text=None, error_title='', error_messages=None):
    story = get_object_or_404(Story, pk=story_id)
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
    if (profile is None):
        raise Http404
        
    # Has the author's email been confirmed?
    email_conf = (profile.email_auth == 0)

    Subscription.objects.get_or_create(user=profile, story=story)

    context = { 'thing'         : story,
                'thing_type'    : u'story',
                'thing_url'     : reverse('story', args=[story.id]),
                'page_title'    : u'Unsubscribe story '+story.title,
                'error_title'   : error_title,
                'error_messages': error_messages,
                'email_conf'	: email_conf,
                'user_dashboard': True,
                'profile'       : profile,
        }

    return render(request, 'castle/subscribed.html', context)
    
#-----------------------------------------------------------------------------
@login_required
def prompt_unsubscribe(request, prompt_id, comment_text=None, error_title='', error_messages=None):
    prompt = get_object_or_404(Prompt, pk=prompt_id)
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
    if (profile is None):
        raise Http404
        
    # Has the author's email been confirmed?
    email_conf = (profile.email_auth == 0)

    Subscription.objects.filter(user=profile, prompt=prompt).delete()

    context = { 'thing'         : prompt,
                'thing_type'    : u'prompt',
                'thing_url'     : reverse('prompt', args=[prompt.id]),
                'page_title'    : u'Unsubscribe prompt '+prompt.title,
                'error_title'   : error_title,
                'error_messages': error_messages,
                'email_conf'	: email_conf,
                'user_dashboard': True,
                'profile'       : profile,
        }

    return render(request, 'castle/unsubscribed.html', context)

#-----------------------------------------------------------------------------
@login_required
def prompt_subscribe(request, prompt_id, comment_text=None, error_title='', error_messages=None):
    prompt = get_object_or_404(Prompt, pk=prompt_id)
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
    if (profile is None):
        raise Http404
        
    # Has the author's email been confirmed?
    email_conf = (profile.email_auth == 0)

    Subscription.objects.get_or_create(user=profile, prompt=prompt)

    context = { 'thing'         : prompt,
                'thing_type'    : u'prompt',
                'thing_url'     : reverse('prompt', args=[prompt.id]),
                'page_title'    : u'Unsubscribe prompt '+prompt.title,
                'error_title'   : error_title,
                'error_messages': error_messages,
                'email_conf'	: email_conf,
                'user_dashboard': True,
                'profile'       : profile,
        }

    return render(request, 'castle/subscribed.html', context)
    
#-----------------------------------------------------------------------------
@login_required
def challenge_unsubscribe(request, challenge_id, comment_text=None, error_title='', error_messages=None):
    challenge = get_object_or_404(Challenge, pk=challenge_id)
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
    if (profile is None):
        raise Http404
        
    # Has the author's email been confirmed?
    email_conf = (profile.email_auth == 0)

    Subscription.objects.filter(user=profile, challenge=challenge).delete()

    context = { 'thing'         : challenge,
                'thing_type'    : u'challenge',
                'thing_url'     : reverse('challenge', args=[challenge.id]),
                'page_title'    : u'Unsubscribe challenge '+challenge.title,
                'error_title'   : error_title,
                'error_messages': error_messages,
                'email_conf'	: email_conf,
                'user_dashboard': True,
                'profile'       : profile,
        }

    return render(request, 'castle/unsubscribed.html', context)

#-----------------------------------------------------------------------------
@login_required
def challenge_subscribe(request, challenge_id, comment_text=None, error_title='', error_messages=None):
    challenge = get_object_or_404(Challenge, pk=challenge_id)
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
    if (profile is None):
        raise Http404
        
    # Has the author's email been confirmed?
    email_conf = (profile.email_auth == 0)

    Subscription.objects.get_or_create(user=profile, challenge=challenge)

    context = { 'thing'         : challenge,
                'thing_type'    : u'challenge',
                'thing_url'     : reverse('challenge', args=[challenge.id]),
                'page_title'    : u'Unsubscribe challenge '+challenge.title,
                'error_title'   : error_title,
                'error_messages': error_messages,
                'email_conf'	: email_conf,
                'user_dashboard': True,
                'profile'       : profile,
        }

    return render(request, 'castle/subscribed.html', context)

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
