from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from castle.models import *
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Sum
from random import randint

# Create your views here.
#-----------------------------------------------------------------------------
# Query functions
#-----------------------------------------------------------------------------
def get_popular_stories(page_num=1, page_size=10):
    # FIXME: this code is MySQL specific
    r = Story.objects.raw(
        "SELECT s.id as id, " +
        "SUM(1/(TIMESTAMPDIFF(day, l.ctime, NOW())+1)) AS score " +
        "FROM castle_storylog AS l " +
        "LEFT JOIN castle_story AS s ON s.id=l.story_id " +
        "WHERE l.user_id != s.user_id " +
        "AND l.log_type = " + str(StoryLog.VIEW) + " "+
        "AND ((s.draft IS NULL) OR (NOT s.draft)) " +
        "GROUP BY l.story_id ORDER BY score DESC LIMIT " +
        str((page_num-1) * page_size) + "," + str(page_size))
    return r

#-----------------------------------------------------------------------------
def get_active_stories(page_num=1, page_size=10):
    last = (page_num * page_size) - 1
    first = (last - page_size) + 1
    return Story.objects.filter(activity__gt = 0).order_by('activity')[first:last]
    
#-----------------------------------------------------------------------------
def get_recent_stories(page_num=1, page_size=10):
    last = (page_num * page_size) - 1
    first = (last - page_size) + 1
    return Story.objects.filter(draft = False).order_by('-ptime')[first:last]
    
#-----------------------------------------------------------------------------
def get_old_stories(page_size=10):
    total = Story.objects.filter(draft = False).count()
    end = 0 if (total < page_size) else (total - page_size)
    first = randint(0, end)
    last  = first + page_size
    return Story.objects.filter(draft = False).order_by('-ptime')[first:last]
    
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
              }
    return render(request, 'castle/index.html', context)
