
#coding: utf-8
#This file is part of Ficlatté.
#Copyright © 2015-2017 Paul Robertson, Jim Stitzel and Shu Sam Chen
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

from random import randint
from comment.views import *
from the_pit.views import the_pit

# -----------------------------------------------------------------------------
def get_popular_prompts(page_num=1, page_size=10):
    db = getattr(settings, 'DB', 'mysql')
    if (db == 'mysql'):
        return Prompt.objects.raw(
            "SELECT p.id as id, " +
            "SUM(1/(TIMESTAMPDIFF(day, l.ctime, NOW())+1)) AS score " +
            "FROM castle_storylog AS l " +
            "LEFT JOIN castle_prompt AS p ON p.id=l.prompt_id " +
            "WHERE l.user_id != p.user_id " +
            "AND l.log_type = " + str(StoryLog.VIEW) + " " +
            "GROUP BY l.prompt_id ORDER BY score DESC LIMIT " +
            str((page_num - 1) * page_size) + "," + str(page_size))
    elif (db == 'postgres'):
        return Prompt.objects.raw(
            "SELECT p.id as id, " +
            "SUM(1/(date_part('day', NOW() - l.ctime)+1)) AS score " +
            "FROM castle_storylog AS l " +
            "LEFT JOIN castle_prompt AS p ON p.id=l.prompt_id " +
            "WHERE l.user_id != p.user_id " +
            "AND l.log_type = " + str(StoryLog.VIEW) + " " +
            "GROUP BY p.id ORDER BY score DESC LIMIT " + str(page_size) + " " +
            "OFFSET " + str((page_num - 1) * page_size))
    return Prompt.objects.all()


# -----------------------------------------------------------------------------
def get_active_prompts(page_num=1, page_size=10):
    first = (page_num - 1) * page_size
    last = first + page_size
    return Prompt.objects.filter(activity__isnull=False, activity__gt=0).order_by('-activity')[first:last]


# -----------------------------------------------------------------------------
def get_num_active_prompts():
    return Prompt.objects.filter(activity__gt=0).count()


# -----------------------------------------------------------------------------
def get_recent_prompts(page_num=1, page_size=10):
    first = (page_num - 1) * page_size
    last = first + page_size
    return Prompt.objects.all().order_by('-ctime')[first:last]


# -----------------------------------------------------------------------------
def get_old_prompts(page_size=10):
    total = Prompt.objects.all().count()
    end = 0 if (total < page_size) else (total - page_size)
    first = randint(0, end)
    last = first + page_size
    return Prompt.objects.all().order_by('ctime')[first:last]


# -----------------------------------------------------------------------------
# Prompt views
# -----------------------------------------------------------------------------
def browse_prompts(request, dataset=0):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
        if (profile.spambot):
            return the_pit(request)

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
    context = {'profile'         : profile,
               'prompts'         : prompts,
               'page_title'      : u'Prompts, page {}'.format(page_num),
               'page_url'        : url,
               'pages'           : bs_pager(page_num, PAGE_BROWSE, num_prompts),
               'user_dashboard'  : 1,
               'label'           : label,
               }

    return render(request, 'prompts/prompts_recent.html', context)


# -----------------------------------------------------------------------------
def active_prompts(request):
    return browse_prompts(request, 1)


# -----------------------------------------------------------------------------
def popular_prompts(request):
    return browse_prompts(request, 2)


# -----------------------------------------------------------------------------
def prompts(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Get featured prompt
    featured_id = Misc.objects.filter(key='featured_prompt')
    featured = None
    if (featured_id):
        featured_query = Prompt.objects.filter(id=featured_id[0].i_val)
        if (featured_query):
            featured = featured_query[0]

    # Build context and render page
    context = {'profile'         : profile,
               'prompts'         : prompts,
               'featured'        : featured,
               'popular'         : get_popular_prompts(1, 4),
               'active'          : get_active_prompts(1, 10),
               'recent'          : get_recent_prompts(1, 10),
               'old'             : get_old_prompts(10),
               'page_title'      : u'Prompts',
               'prompt_button'   : (profile is not None),
               'user_dashboard'  : (profile is not None),
               'page_url'        : u'/prompts/',
               }

    return render(request, 'prompts/prompts.html', context)


# -----------------------------------------------------------------------------
def prompt_view(request, prompt_id):
    # Get prompt
    prompt = get_object_or_404(Prompt, pk=prompt_id)

    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
        if (profile.spambot):
            return the_pit(request)

    # Get stories inspired by prompt
    page_num = safe_int(request.GET.get('page_num', 1))
    stories = prompt.story_set.exclude(draft=True).order_by('ctime')[(page_num - 1) * PAGE_STORIES:page_num * PAGE_STORIES]
    num_stories = prompt.story_set.exclude(draft=True).count()

    # Get comments
    page_num = safe_int(request.GET.get('page_num', 1))
    comments = prompt.comment_set.filter(spam__lt=Comment.SPAM_QUARANTINE).order_by('ctime')[(page_num - 1) * PAGE_COMMENTS:page_num * PAGE_COMMENTS]

    # Prompt's owner gets an edit link
    owner = ((profile is not None) and (profile == prompt.user))

    # Log view
    if (profile) and (profile.email_authenticated()):
        log = StoryLog(
            user=profile,
            prompt=prompt,
            log_type=StoryLog.VIEW
        )
        log.save()

        # Suppress challenge if marked as mature and either the user is not logged in
        # or the user has not enabled viewing of mature challenges
    suppressed = False
    if (prompt.mature):
        if ((not profile) or ((prompt.user != profile) and (not profile.mature))):
            suppressed = True

            # Is user subscribed?
    subscribed = False
    if (profile and (Subscription.objects.filter(prompt=prompt, user=profile).count() > 0)):
        subscribed = True

        # Build context and render page
    context = {'profile'           : profile,
               'prompt'            : prompt,
               'stories'           : stories,
               'comments'          : comments,
               'owner'             : owner,
               'subscribed'        : subscribed,
               'page_title'        : u'Prompt ' + prompt.title,
               'prompt_sidepanel'  : 1,
               'page_url'          : u'/prompts/' + unicode(prompt.id) + u'/',
               'pages'             : bs_pager(page_num, PAGE_STORIES, num_stories),
               'suppressed'        : suppressed,
               }

    return render(request, 'prompts/prompt.html', context)


# -----------------------------------------------------------------------------
@login_required
def new_prompt(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
        if (profile.spambot):
            return the_pit(request)

    # Create a blank prompt to give the template some defaults
    prompt = Prompt()

    # Build context and render page
    context = {'profile'         : profile,
               'prompt'          : prompt,
               'page_title'      : u'Write new prompt',
               'length_limit'    : 256,
               'length_min'      : 30,
               'user_dashboard'  : 1,
               }

    return render(request, 'prompts/edit_prompt.html', context)


# -----------------------------------------------------------------------------
@login_required
def edit_prompt(request, prompt_id):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
        if (profile.spambot):
            return the_pit(request)

    # Get prompt
    prompt = get_object_or_404(Prompt, pk=prompt_id)

    # User can only edit their own stories
    if (prompt.user != profile):
        raise Http404

    # Build context and render page
    context = {'profile'         : profile,
               'prompt'          : prompt,
               'page_title'      : u'Edit prompt ' + prompt.title,
               'length_limit'    : 256,
               'length_min'      : 30,
               'user_dashboard'  : 1,
               }

    return render(request, 'prompts/edit_prompt.html', context)


# -----------------------------------------------------------------------------
@login_required
@transaction.atomic
def submit_prompt(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
        if (profile.spambot):
            return the_pit(request)

    # Get bits and bobs
    errors = []
    prompt = get_foo(request.POST, Prompt, 'prid')
    new_prompt = (prompt is None)

    if (not profile.email_authenticated()):
        errors.append(u'You must have authenticated your e-mail address before posting a prompt')
    else:
        # Get prompt object, either existing or new
        # new_prompt = False
        if (prompt is None):
            prompt = Prompt(user=profile)
            # new_prompt = True

        # Populate prompt object with data from submitted form
        prompt.title = request.POST.get('title', '')
        prompt.body = request.POST.get('body', '')
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
        context = {'profile'         : profile,
                   'prompt'          : prompt,
                   'length_limit'    : 256,
                   'length_min'      : 30,
                   'page_title'      : u'Edit prompt ' + prompt.title,
                   'user_dashboard'  : 1,
                   'error_title'     : 'Prompt submission unsuccessful',
                   'error_messages'  : errors,
                   }

        return render(request, 'prompts/edit_prompt.html', context)

    # Is the prompt new?
    if (new_prompt is None):
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
    if (profile) and (profile.email_authenticated()):
        log_type = StoryLog.PROMPT
        if (not new_prompt):
            log_type = StoryLog.PROMPT_MOD
        log = StoryLog(
            user=profile,
            log_type=log_type,
            prompt=prompt
        )
        log.save()

    return HttpResponseRedirect(reverse('prompt', args=(prompt.id,)))


# -----------------------------------------------------------------------------
@login_required
def prompt_subscribe(request, prompt_id, error_title='', error_messages=None):
    prompt = get_object_or_404(Prompt, pk=prompt_id)
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
    if (profile is None):
        raise Http404
    if (profile.spambot):
        return the_pit(request)

    Subscription.objects.get_or_create(user=profile, prompt=prompt)

    context = {'thing'           : prompt,
               'thing_type'      : u'prompt',
               'thing_url'       : reverse('prompt', args=[prompt.id]),
               'page_title'      : u'Subscribe prompt ' + prompt.title,
               'error_title'     : error_title,
               'error_messages'  : error_messages,
               'user_dashboard'  : True,
               'profile'         : profile,
               }

    return render(request, 'castle/subscribed.html', context)


# -----------------------------------------------------------------------------
@login_required
def prompt_unsubscribe(request, prompt_id, error_title='', error_messages=None):
    prompt = get_object_or_404(Prompt, pk=prompt_id)
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
    if (profile is None):
        raise Http404
    if (profile.spambot):
        return the_pit(request)

    Subscription.objects.filter(user=profile, prompt=prompt).delete()

    context = {'thing'           : prompt,
               'thing_type'      : u'prompt',
               'thing_url'       : reverse('prompt', args=[prompt.id]),
               'page_title'      : u'Unsubscribe prompt ' + prompt.title,
               'error_title'     : error_title,
               'error_messages'  : error_messages,
               'user_dashboard'  : True,
               'profile'         : profile,
               }

    return render(request, 'castle/unsubscribed.html', context)

# -----------------------------------------------------------------------------
