from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from castle.models import *
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Sum, Avg
from random import randint
from django.db.models import Q
from django.utils.http import urlquote_plus
import math

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
    return Story.objects.filter(draft = False).order_by('ptime')[first:last]
    
#-----------------------------------------------------------------------------
def get_old_stories(page_size=10):
    total = Story.objects.filter(draft = False).count()
    end = 0 if (total < page_size) else (total - page_size)
    first = randint(0, end)
    last  = first + page_size
    return Story.objects.filter(draft = False).order_by('ptime')[first:last]
    
#-----------------------------------------------------------------------------
def get_activity_log(profile, entries):
    log_entries = StoryLog.objects.exclude(log_type = StoryLog.VIEW).exclude(log_type = StoryLog.RATE).filter(Q(user = profile) | Q(story__user = profile)).order_by('ctime')[:entries]
    
    return log_entries

#-----------------------------------------------------------------------------
# Pager
#-----------------------------------------------------------------------------
def bs_pager(cur_page, page_size, num_items):
    
    num_pages = int(math.ceil(num_items / page_size))
    
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
    story_list = [] # FIXME: need to support paging
    if (owner):
        story_list.extend(Story.objects.filter(user = author, draft = True))
    story_list.extend(Story.objects.filter(user = author, draft = False))

    # Build context and render page
    context = { 'profile'       : profile,
                'author'        : author,
                'story_list'    : story_list,
                'page_url'      : u'/author/'+urlquote_plus(author.pen_name),
                'pages'         : bs_pager(1, 10, len(story_list)),
                'user_dashboard': owner,
                'other_user_sidepanel' : (not owner),
            }
    return render(request, 'castle/author.html', context)

#-----------------------------------------------------------------------------
def story(request, story_id):
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
    prequels.extend(story.prequels.all())

    sequels = []
    if (story.prequel_to):
        sequels.append(story.prequel_to)
    sequels.extend(story.sequels.all())

    # Get user rating in numeric and string forms
    rating = Rating.objects.filter(story=story).exclude(user=story.user).aggregate(avg=Avg('rating'))['avg']
    rating_str = u'{:.2f}'.format(rating) if (rating) else ''
    
    # Get comments # FIXME: need to support paging
    comments = story.comment_set.all().order_by('ctime')

    # Count how many times the story has been viewed and rated
    viewed = StoryLog.objects.filter(story = story).exclude(user = author).count()
    rated  = Rating.objects.filter(story = story).exclude(user=author).count()

    # Build context and render page
    context = { 'profile'       : profile,
                'author'        : story.user,
                'story'         : story,
                'prequels'      : prequels,
                'sequels'       : sequels,
                'rating_str'    : rating_str,
                'rating_num'    : rating,
                'comments'      : comments,
                'page_url'      : u'/stories/'+unicode(story_id),
                'pages'         : bs_pager(1, 10, story.comment_set.count()),
                'story_sidepanel':1 ,
                'owner'         : owner,
                'viewed'        : viewed,
                'rated'         : rated,
            }
    return render(request, 'castle/story.html', context)

#-----------------------------------------------------------------------------
@login_required
def new_story(request):

    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Build context and render page
    context = { 'profile'       : profile,
                'story'         : Story(),      # Create blank story for default purposes
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
def get_foo(request, foo, key):
    sid = request.POST.get(key, None)
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
@login_required
@transaction.atomic
def submit_story(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Get bits and bobs
    errors     = []
    story      = get_foo(request, Story,  'sid')
    prequel_to = get_foo(request, Story,  'prequel_to')
    sequel_to  = get_foo(request, Story,  'sequel_to')
    prompt     = get_foo(request, Prompt, 'prid')
    tags       = ''

    if (not profile.email_authenticated()):
        errors.append(u'You must have authenticated your e-mail address before posting a story');
    else:
        # Get story object, either existing or new
        if (story is None):
            story = Story(user=profile)

        # Populate story object with data from submitted form
        story.title  = request.POST.get('title', '')
        story.body   = request.POST.get('body', '')
        story.mature = request.POST.get('is_mature', False)
        story.draft  = request.POST.get('is_draft', False)
        
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
    
    # No problems, update the database and redirect
    story.save()
    return HttpResponseRedirect(reverse('story', args=(story.id,)))

#-----------------------------------------------------------------------------
def prompts(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Get prompts # FIXME: need to support paging
    prompts = Prompt.objects.all().order_by('ctime')

    # Build context and render page
    context = { 'profile'       : profile,
                'prompts'       : prompts,
                'prompt_button' : (profile is not None),
                'user_dashboard': (profile is not None),
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

    # Get stories inspired by prompt # FIXME: need to support paging
    stories = prompt.story_set.exclude(draft=True).order_by('ctime')

    # Prompt's owner gets an edit link
    owner = ((profile is not None) and (profile == prompt.user))

    # Build context and render page
    context = { 'profile'       : profile,
                'prompt'        : prompt,
                'stories'       : stories,
                'owner'         : owner,
                'prompt_sidepanel' : 1,
            }
    

    return render(request, 'castle/prompt.html', context)

#-----------------------------------------------------------------------------
def blogs(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Get blogs # FIXME: need to support paging
    blogs = Blog.objects.exclude(draft=True).order_by('ptime')

    # Build context and render page
    context = { 'profile'       : profile,
                'blogs'         : blogs,
                'page_url'      : u'/blog/',
                'pages'         : bs_pager(1, 10, blogs.count()),
            }
    return render(request, 'castle/blogs.html', context)

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
def blog(request, blog_id):
    blog = get_object_or_404(Blog, pk=blog_id)
    
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Is logged-in user the author?
    author = blog.user
    owner = ((profile is not None) and (profile == author))

    # Get comments # FIXME: need to support paging
    comments = blog.comment_set.all().order_by('ctime')

    # Build context and render page
    context = { 'profile'       : profile,
                'author'        : blog.user,
                'blog'          : blog,
                'comments'      : comments,
                'page_url'      : u'/stories/'+unicode(blog_id),
                'pages'         : bs_pager(1, 10, blog.comment_set.count()),
                'owner'         : owner,
            }
    return render(request, 'castle/blog.html', context)

#-----------------------------------------------------------------------------
@login_required
def new_blog(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

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
    
    # Build context and render page
    context = { 'profile'       : profile,
                'blog'          : blog,
                'length_limit'  : 20480,
                'length_min'    : 60,
                'user_dashboard': 1,
            }

    return render(request, 'castle/edit_blog.html', context)

#-----------------------------------------------------------------------------
