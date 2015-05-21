
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
from django.db.models import Sum, Avg, Q, Count
from django.utils.http import urlquote_plus, urlquote
from django.conf import settings
from django.utils import timezone
from castle.models import *
from castle.mail import *
from datetime import datetime, timedelta
from random import randint
from struct import unpack
from os import urandom
import math
import re
import hashlib

#-----------------------------------------------------------------------------
# Global symbols
#-----------------------------------------------------------------------------
PAGE_COMMENTS   = 15
PAGE_STORIES    = 15
PAGE_BROWSE     = 25
PAGE_PROMPTS    = 20
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
    return Tag.objects.values('tag').annotate(n=Count('tag')).order_by('-n','tag')[first:last]
    
#-----------------------------------------------------------------------------
def get_num_tags():
    return Tag.objects.values('tag').distinct().count()
    
#-----------------------------------------------------------------------------
def get_activity_log(profile, entries):
    log_entries = StoryLog.objects.exclude(log_type = StoryLog.VIEW).exclude(log_type = StoryLog.RATE).filter(Q(user = profile) | Q(story__user = profile)).order_by('-ctime')[:entries]
    
    return log_entries

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
    return unpack("!Q", urandom(8))[0]

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
    
    # Get featured story
    featured_id = Misc.objects.filter(key='featured')
    featured = None
    if (featured_id):
        featured_query = Story.objects.filter(id=featured_id[0].i_val)
        if (featured_query):
            featured = featured_query[0]
        
    # Build context and render page
    context = { 'profile'       : profile,
                'blog_latest'   : Blog.objects.all().order_by('-id')[0],
                'featured'      : featured,
                'popular'       : get_popular_stories(1,4),
                'active'        : get_active_stories(1,10),
                'recent'        : get_recent_stories(1,10),
                'old'           : get_old_stories(10),
                'activity_log'  : get_activity_log(profile, 10),
                'user_dashboard': 1,
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

    # Build story list (owner sees their drafts)
    page_num = safe_int(request.GET.get('page_num', 1))
    if (owner):
        num_stories = Story.objects.filter(user = author).count()
        story_list = Story.objects.filter(user = author).order_by('-draft','-ptime','-mtime')[(page_num-1)*PAGE_STORIES:page_num*PAGE_STORIES]
    else:
        num_stories=Story.objects.filter(user = author, draft = False).count()
        story_list=Story.objects.filter(user = author, draft = False).order_by('-ptime')[(page_num-1)*PAGE_STORIES:page_num*PAGE_STORIES]

    # Friendship?
    is_friend = False
    if (profile and author):
        is_friend = profile.is_friend(author)

    # Build context and render page
    context = { 'profile'       : profile,
                'author'        : author,
                'story_list'    : story_list,
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
    
    # Build story list (owner sees their drafts)
    page_num = safe_int(request.GET.get('page_num', 1))
    num_stories = Story.objects.filter(user = profile, draft=True).count()
    story_list = Story.objects.filter(user = profile, draft=True).order_by('-mtime')[(page_num-1)*PAGE_STORIES:page_num*PAGE_STORIES]

    # Build context and render page
    context = { 'profile'       : profile,
                'author'        : profile,
                'story_list'    : story_list,
                'page_url'      : u'/authors/'+urlquote(profile.pen_name)+u'/',
                'pages'         : bs_pager(page_num, PAGE_STORIES, num_stories),
                'drafts_page'   : True,
                'user_dashboard': True,
                'other_user_sidepanel' : False,
            }
    return render(request, 'castle/author.html', context)

#-----------------------------------------------------------------------------
@transaction.atomic
def signin(request):
    username = request.POST.get('username', None)
    password = request.POST.get('password', None)

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
    if (profile.old_salt is not None):
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
            
            return HttpResponseRedirect(reverse('home'))
        
    else:
        user = authenticate(username=profile.user.username, password=password)
    
    if user is not None:
        if user.is_active:
            login(request, user)
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

    # Build context and render page
    context = { 'profile'       : profile,
                'author'        : story.user,
                'story'         : story,
                'prequels'      : prequels,
                'sequels'       : sequels,
                'rating_str'    : rating_str,
                'rating_num'    : rating,
                'comments'      : comments,
                'page_url'      : u'/stories/'+unicode(story_id)+u'/',
                'pages'         : bs_pager(page_num, PAGE_COMMENTS, story.comment_set.count()),
                'story_sidepanel':1 ,
                'owner'         : owner,
                'viewed'        : viewed,
                'rated'         : rated,
                'comment_text'  : comment_text, # in case of failed comment submission
                'user_rating'   : user_rating,
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

    # Create a blank story to give the template some defaults
    story = Story(prequel_to = prequel_to,
                  sequel_to  = sequel_to,
                  prompt     = prompt)

    # Build context and render page
    context = { 'profile'       : profile,
                'story'         : story,
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
    prompt     = get_foo(request.POST, Prompt, 'prid')
    tags       = request.POST.get('tag_list', '')
    new_story  = (story is None)
    was_draft  = False
    if (not new_story):         # Remember if the story was draft
        was_draft = story.draft

    if (not profile.email_authenticated()):
        errors.append(u'You must have authenticated your e-mail address before posting a story');
    else:
        # Get story object, either existing or new
        if (story is None):
            story = Story(user       = profile,
                          prequel_to = prequel_to,
                          sequel_to  = sequel_to,
                          prompt     = prompt)

        # Populate story object with data from submitted form
        story.title  = request.POST.get('title', '')
        story.body   = request.POST.get('body', '')
        story.mature = request.POST.get('is_mature', False)
        story.draft  = request.POST.get('is_draft', False)
        
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

    # Make log entry
    log_type = StoryLog.WRITE
    quel = None
    if (sequel_to):
        log_type = StoryLog.SEQUEL
        quel = sequel_to
    elif (prequel_to):
        log_type = StoryLog.PREQUEL
        quel = prequel_to

    if (not new_story):
        log_type = StoryLog.STORY_MOD
        
    log = StoryLog(
        user = profile,
        story = story,
        quel = quel,
        log_type = log_type,
        prompt = prompt
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
def prompts(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Get prompts
    page_num = safe_int(request.GET.get('page_num', 1))
    prompts = Prompt.objects.all().order_by('-ctime')[(page_num-1)*PAGE_PROMPTS:page_num*PAGE_PROMPTS]
    num_prompts = Prompt.objects.all().count()

    # Build context and render page
    context = { 'profile'       : profile,
                'prompts'       : prompts,
                'prompt_button' : (profile is not None),
                'user_dashboard': (profile is not None),
                'page_url'      : u'/prompts/',
                'pages'         : bs_pager(page_num, PAGE_PROMPTS, num_prompts),
            }
    

    return render(request, 'castle/prompts.html', context)

#-----------------------------------------------------------------------------
def prompt(request, prompt_id):
    # Get story
    prompt = get_object_or_404(Prompt, pk=prompt_id)

    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Get stories inspired by prompt
    page_num = safe_int(request.GET.get('page_num', 1))
    stories = prompt.story_set.exclude(draft=True).order_by('ctime')[(page_num-1)*PAGE_STORIES:page_num*PAGE_STORIES]
    num_stories = prompt.story_set.exclude(draft=True).count()

    # Prompt's owner gets an edit link
    owner = ((profile is not None) and (profile == prompt.user))

    # Build context and render page
    context = { 'profile'       : profile,
                'prompt'        : prompt,
                'stories'       : stories,
                'owner'         : owner,
                'prompt_sidepanel' : 1,
                'page_url'      : u'/prompts/'+unicode(prompt.id)+u'/',
                'pages'         : bs_pager(page_num, PAGE_STORIES, num_stories),
            }

    return render(request, 'castle/prompt.html', context)

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
    prompt     = get_foo(request.POST, Prompt,  'prid')

    if (not profile.email_authenticated()):
        errors.append(u'You must have authenticated your e-mail address before posting a prompt');
    else:
        # Get prompt object, either existing or new
        new_prompt = False
        if (prompt is None):
            prompt = Prompt(user=profile)
            new_prompt = True

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
                    'user_dashboard': 1,
                    'error_title'   : 'Prompt submission unsuccessful',
                    'error_messages': errors,
                }

        return render(request, 'castle/edit_prompt.html', context)
    
    # Set modification time
    prompt.mtime = timezone.now()

    # No problems, update the database and redirect
    prompt.save()
    
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
@login_required
def new_prompt(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Build context and render page
    context = { 'profile'       : profile,
                'story'         : Prompt(),      # Create blank story for default purposes
                'tags'          : u'',
                'length_limit'  : 256,
                'length_min'    : 30,
                'user_dashboard': 1,
            }

    return render(request, 'castle/edit_prompt.html', context)

#-----------------------------------------------------------------------------
@login_required
def edit_prompt(request, prompt_id):
    # Get prompt
    prompt = get_object_or_404(Prompt, pk=prompt_id)
    
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # User can only edit their own stories
    if (prompt.user != profile):
        raise Http404
    
    # Build context and render page
    context = { 'profile'       : profile,
                'prompt'        : prompt,
                'length_limit'  : 1024,
                'length_min'    : 60,
                'user_dashboard': 1,
            }

    return render(request, 'castle/edit_prompt.html', context)

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

    # Build context and render page
    context = { 'profile'       : profile,
                'author'        : blog.user,
                'blog'          : blog,
                'comments'      : comments,
                'page_url'      : u'/stories/'+unicode(blog_id),
                'pages'         : bs_pager(page_num, PAGE_COMMENTS, blog.comment_set.count()),
                'owner'         : owner,
                'comment_text'  : comment_text,
                'error_title'   : error_title,
                'error_messages': error_messages,
            }
    return render(request, 'castle/blog.html', context)

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
    else:
        # Create comment object
        comment = Comment(user = profile,
                          blog = blog,
                          story = story)

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
        else:
            return story_view(request, story.id, comment.body, rating, u'Comment submission failed', errors)

    # Set modification time
    comment.mtime = timezone.now()
    
    # No problems, update the database and redirect
    if (l > 0):
        comment.save()
    
    # Update rating, if applicable
    if ((story is not None) and (rating is not None)):
        rating_set = Rating.objects.filter(story=story, user=profile)
        if (rating_set):
            rating_obj = rating_set[0]
        else:
            rating_obj = Rating(user=profile, story=story)
        rating_obj.rating = rating
        rating_obj.mtime = timezone.now()
        rating_obj.save()

    # Make log entries but only for story comments
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
            
    if (blog):
        return HttpResponseRedirect(reverse('blog', args=(blog.id,)))
    else:
        return HttpResponseRedirect(reverse('story', args=(story.id,)))
        
#-----------------------------------------------------------------------------
def profile_view(request, error_title=None, error_messages=None):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
    
    # Build context and render page
    context = { 'profile'       : profile,
                'length_limit'  : 1024,
                'length_min'    : 1,
                'error_title'   : error_title,
                'error_messages': error_messages,
            }

    return render(request, 'castle/profile.html', context)
        
#-----------------------------------------------------------------------------
@transaction.atomic
def submit_profile(request):
    # Get user profile
    new_registration = False
    if (request.user.is_authenticated()):
        profile = request.user.profile
    else:
        profile = Profile()
        new_registration = True
        
    # Get data from form
    pen_name        = request.POST.get('pen_name', '')
    password        = request.POST.get('password', '')
    new_password    = request.POST.get('new_password', '')
    password_again  = request.POST.get('password', '')
    site_url        = request.POST.get('site_url', '')
    site_name       = request.POST.get('site_name', '')
    biography       = request.POST.get('biography', '')
    mature          = request.POST.get('mature', '')
    email_addr      = request.POST.get('email_addr', '')
    rules           = request.POST.get('rules', False)
    
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

    if (site_url):
        profile.site_url = site_url
    if (site_name):
        profile.site_name = site_name
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

    # If user is changing e-mail address, they need their password too
    if (not new_registration and (
            (email_addr and email_addr != profile.email_addr) or
            (pen_name   and pen_name.upper() != profile.pen_name_uc))):
        if (not password):
            errors.append(u'When you change your pen name or e-mail address, you need to supply your password too.')
        elif (not request.user.check_password(password)):
            errors.append(u'Old password incorrect')

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
            email_addr = email_addr,
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
    if (new_registration or email_addr):
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
