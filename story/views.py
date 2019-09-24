
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

from random import randint
from django.db.models import Avg, Q, Count
from django.utils.http import urlquote
from comment.views import *
from the_pit.views import the_pit

# -----------------------------------------------------------------------------
def home(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
        if (profile.spambot):
            return the_pit(request)

    # Get featured story
    featured_id = Misc.objects.filter(key='featured')
    featured = None
    if (featured_id):
        featured_query = Story.objects.filter(id=featured_id[0].i_val)
        if (featured_query):
            featured = featured_query[0]

    # Get latest challenge
    try:
        challenge = Challenge.objects.all().order_by('-id')[0]
    except IndexError:
        challenge = None

    # Get latest prompt
    try:
        prompt = Prompt.objects.all().order_by('-id')[0]
    except IndexError:
        prompt = None

    # Suppress story if marked as mature and either the user is not logged in
    # or the user has not enabled viewing of mature stories
    suppressed = False
    if (featured is not None) and (featured.mature):
        if ((not profile) or ((featured.user != profile) and (not profile.mature))):
            suppressed = True

    # Get latest blog
    try:
        blog = Blog.objects.all().order_by('-id')[:3]
    except IndexError:
        blog = None

    # Build context and render page
    context = {'profile'         : profile,
               'blog_latest'     : blog,
               'featured'        : featured,
               'challenge'       : challenge,
               'prompt'          : prompt,
               'popular'         : get_popular_stories(1, 5),
               'active'          : get_active_stories(1, 10),
               'recent'          : get_recent_stories(1, 10),
               'old'             : get_old_stories(10),
               'random'          : get_random_story(),
               'activity_log'    : get_activity_log(profile, 10),
               'user_dashboard'  : 1,
               'suppressed'      : suppressed,
               }

    return render(request, 'stories/index.html', context)


# -----------------------------------------------------------------------------
def get_popular_stories(page_num=1, page_size=10):
    db = getattr(settings, 'DB', 'mysql')
    if (db == 'mysql'):
        return Story.objects.raw(
            "SELECT s.id as id, " +
            "SUM(1/(TIMESTAMPDIFF(day, l.ctime, NOW())+1)) AS score " +
            "FROM castle_storylog AS l " +
            "LEFT JOIN castle_story AS s ON s.id=l.story_id " +
            "WHERE l.user_id != s.user_id " +
            "AND l.log_type = " + str(StoryLog.VIEW) + " " +
            "AND ((s.draft IS NULL) OR (NOT s.draft)) " +
            "GROUP BY l.story_id ORDER BY score DESC LIMIT " +
            str((page_num - 1) * page_size) + "," + str(page_size))
    elif (db == 'postgres'):
        return Story.objects.raw(
            "SELECT s.id as id, " +
            "SUM(1/(date_part('day', NOW() - l.ctime)+1)) AS score " +
            "FROM castle_storylog AS l " +
            "LEFT JOIN castle_story AS s ON s.id=l.story_id " +
            "WHERE l.user_id != s.user_id " +
            "AND l.log_type = " + str(StoryLog.VIEW) + " " +
            "AND ((s.draft IS NULL) OR (NOT s.draft)) " +
            "GROUP BY s.id ORDER BY score DESC LIMIT " + str(page_size) + " " +
            "OFFSET " + str((page_num - 1) * page_size))
    return Story.objects.all()


# -----------------------------------------------------------------------------
def get_active_stories(page_num=1, page_size=10):
    first = (page_num - 1) * page_size
    last = first + page_size
    return Story.objects.filter(activity__isnull=False, activity__gt=0).order_by('-activity')[first:last]


# -----------------------------------------------------------------------------
def get_num_active_stories():
    return Story.objects.filter(activity__gt=0).count()


# -----------------------------------------------------------------------------
def get_recent_stories(page_num=1, page_size=10):
    first = (page_num - 1) * page_size
    last = first + page_size
    return Story.objects.filter(draft=False).order_by('-ptime')[first:last]


# -----------------------------------------------------------------------------
def get_old_stories(page_size=10):
    total = Story.objects.filter(draft=False).count()
    end = 0 if (total < page_size) else (total - page_size)
    first = randint(0, end)
    last = first + page_size
    return Story.objects.filter(draft=False).order_by('ptime')[first:last]


# -----------------------------------------------------------------------------
def get_random_story(page_size=10):
    total = Story.objects.filter(draft=False).count()
    if (total < 1):
        return 0
    end = 0 if (total < page_size) else (total - page_size)
    first = randint(0, end)
    story = Story.objects.filter(draft=False).order_by('ptime')[first]
    return story.id


# -----------------------------------------------------------------------------
def get_tagged_stories(tag_name, page_num=1, page_size=10):
    num = Tag.objects.filter(tag=tag_name.upper()).count()
    if (num == 0):
        return 0, None

    first = (page_num - 1) * page_size
    last = first + page_size
    stories = Story.objects.filter(draft=False, tag__tag=tag_name.upper()).order_by('-ptime')[first:last]

    return num, stories


# -----------------------------------------------------------------------------
def get_all_tags(page_num=1, page_size=10):
    first = (page_num - 1) * page_size
    last = first + page_size
    return Tag.objects.values('tag').annotate(n=Count('tag')).order_by('tag')[first:last]


# -----------------------------------------------------------------------------
def get_num_tags():
    return Tag.objects.values('tag').distinct().count()


# -----------------------------------------------------------------------------
def get_activity_log(profile, entries):
    if (profile is None):
        return None
    log_entries = StoryLog.objects.exclude(log_type=StoryLog.VIEW).exclude(log_type=StoryLog.RATE).filter(
        Q(user=profile) | Q(story__user=profile)).order_by('-ctime')[:entries]

    return log_entries


# -----------------------------------------------------------------------------
# Story views
# -----------------------------------------------------------------------------
def story_view(request, story_id, comment_text=None, user_rating=None, error_title='', error_messages=None):
    story = get_object_or_404(Story, pk=story_id)

    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
        if (profile.spambot):
            return the_pit(request)

    # Is logged-in user the author?
    author = story.user
    owner = ((profile is not None) and (profile == author))

    # User can only see their own drafts
    if (story.user != profile and story.draft):
        raise Http404

    # Is logged-in user the challenge owner?
    challenge = story.challenge
    ch_owner = None
    if (story.challenge):
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
    rating_str = u'{:.2f}'.format(rating) if rating else ''

    # Get comments
    page_num = safe_int(request.GET.get('page_num', 1))
    comments = story.comment_set.filter(spam__lt=Comment.SPAM_QUARANTINE).order_by('ctime')[(page_num - 1) * PAGE_COMMENTS:page_num * PAGE_COMMENTS]

    # Log view
    if (profile) and (profile.email_authenticated()):
        log = StoryLog(
            user=profile,
            story=story,
            log_type=StoryLog.VIEW
        )
        log.save()

    # Count how many times the story has been viewed and rated
    viewed = StoryLog.objects.filter(story=story).exclude(user=author).count()
    rated = Rating.objects.filter(story=story).exclude(user=author).count()

    # Get current user's rating
    if profile and (user_rating is None):
        rating_set = Rating.objects.filter(story=story, user=profile)
        if rating_set:
            user_rating = rating_set[0].rating

    # Suppress story if marked as mature and either the user is not logged in
    # or the user has not enabled viewing of mature stories
    suppressed = False
    if (story.mature):
        if ((not profile) or ((story.user != profile) and (not profile.mature))):
            suppressed = True

    # Is user subscribed?
    subscribed = False
    if (profile and (Subscription.objects.filter(story=story, user=profile).count() > 0)):
        subscribed = True

    prequel_subscribed = False
    if (profile and (Subscription.objects.filter(prequel_to=story, user=profile).count() > 0)):
        prequel_subscribed = True

    sequel_subscribed = False
    if (profile and (Subscription.objects.filter(sequel_to=story, user=profile).count() > 0)):
        sequel_subscribed = True

    # Build context and render page
    context = {'profile'             : profile,
               'author'              : story.user,
               'story'               : story,
               'prequels'            : prequels,
               'sequels'             : sequels,
               'rating_str'          : rating_str,
               'rating_num'          : rating,
               'comments'            : comments,
               'subscribed'          : subscribed,
               'prequel_subscribed'  : prequel_subscribed,
               'sequel_subscribed'   : sequel_subscribed,
               'page_title'          : story.title,
               'page_url'            : u'/stories/' + unicode(story_id) + u'/',
               'pages'               : bs_pager(page_num, PAGE_COMMENTS, story.comment_set.filter(spam__lt=Comment.SPAM_QUARANTINE).count()),
               'story_sidepanel'     : 1,
               'owner'               : owner,
               'challenge'           : challenge,
               'ch_owner'            : ch_owner,
               'viewed'              : viewed,
               'rated'               : rated,
               'comment_text'        : comment_text,  # in case of failed comment submission
               'user_rating'         : user_rating,
               'suppressed'          : suppressed,
               'error_title'         : error_title,
               'error_messages'      : error_messages,
               }

    return render(request, 'stories/story.html', context)


# -----------------------------------------------------------------------------
@login_required
def new_story(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
        if (profile.spambot):
            return the_pit(request)

    # Get prequel, sequel and prompt data from the GET request
    prequel_to = get_foo(request.GET, Story, 'prequel_to')
    sequel_to = get_foo(request.GET, Story, 'sequel_to')
    prompt = get_foo(request.GET, Prompt, 'prid')
    challenge = get_foo(request.GET, Challenge, 'chid')

    # Create a blank story to give the template some defaults
    story = Story(prequel_to=prequel_to,
                  sequel_to=sequel_to,
                  prompt=prompt,
                  prompt_text=u'',
                  challenge=challenge,
                  )

    # Build context and render page
    context = {'profile'         : profile,
               'story'           : story,
               'page_title'      : u'Write new story',
               'tags'            : u'',
               'length_limit'    : 1024,
               'length_min'      : 60,
               'user_dashboard'  : 1,
               }

    return render(request, 'stories/edit_story.html', context)


# -----------------------------------------------------------------------------
@login_required
def edit_story(request, story_id):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
        if (profile.spambot):
            return the_pit(request)

    # Get story
    story = get_object_or_404(Story, pk=story_id)

    # User can only edit their own stories
    if (story.user != profile):
        raise Http404

    # Get tags
    tags = ", ".join(story.tag_set.values_list('tag', flat=True))

    # Build context and render page
    context = {'profile'         : profile,
               'story'           : story,
               'page_title'      : u'Edit story ' + story.title,
               'tags'            : tags,
               'length_limit'    : 1024,
               'length_min'      : 60,
               'user_dashboard'  : 1,
               }

    return render(request, 'stories/edit_story.html', context)


# -----------------------------------------------------------------------------
@login_required
def delete_story(request, story_id):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
        if (profile.spambot):
            return the_pit(request)

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
                   'status_message': u'Story deleted', })


# -----------------------------------------------------------------------------
@login_required
@transaction.atomic
def submit_story(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
        if (profile.spambot):
            return the_pit(request)

    # Has the author's email been confirmed?
    email_conf = (profile.email_auth == 0)

    # Get bits and bobs
    errors = []
    story = get_foo(request.POST, Story, 'sid')
    prequel_to = get_foo(request.POST, Story, 'prequel_to')
    sequel_to = get_foo(request.POST, Story, 'sequel_to')
    challenge = get_foo(request.POST, Challenge, 'chid')
    prompt = get_foo(request.POST, Prompt, 'prid')
    tags = request.POST.get('tag_list', '')
    ptext = request.POST.get('prompt_text', None)
    new_story = (story is None)
    was_draft = False
    if (not new_story):  # Remember if the story was draft
        was_draft = story.draft

    if (not profile.email_authenticated()):
        errors.append(u'You must have authenticated your e-mail address before posting a story')

    # Get story object, either existing or new
    if (story is None):
        story = Story(user=profile,
                      prequel_to=prequel_to,
                      sequel_to=sequel_to,
                      prompt=prompt,
                      challenge=challenge,
                      )

    # Populate story object with data from submitted form
    story.title = request.POST.get('title', '')
    story.body = request.POST.get('body', '')
    story.mature = request.POST.get('is_mature', False)
    story.draft = request.POST.get('is_draft', False)
    story.prompt_text = ptext
    if (challenge):
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

    if (story.draft and (l > 1536)):
        errors.append(u'Draft is over 1536 characters (currently ' + unicode(l) + u')')

    # If there have been errors, re-display the page
    if (errors):
        # Build context and render page
        context = {'profile'         : profile,
                   'story'           : story,
                   'page_title'      : u'Edit story ' + story.title,
                   'tags'            : tags,
                   'length_limit'    : 1024,
                   'length_min'      : 60,
                   'email_conf'      : email_conf,
                   'user_dashboard'  : 1,
                   'error_title'     : 'Story submission unsuccessful',
                   'error_messages'  : errors,
                   }

        return render(request, 'stories/edit_story.html', context)

    # Is the story being published?
    if (not story.draft and (was_draft or new_story)):
        # Set the publish time and send notifications to subscribed users of the prequel/sequel (if applicable)
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
            if (t not in td):  # Strip out duplicates using dict 'td'
                td[t] = 1
                tag_object = Tag(story=story, tag=t)
                tag_object.save()

    # Auto-subscribe to e-mail notifications according to user's preferences
    if (new_story):
        if (profile.email_flags & Profile.AUTOSUBSCRIBE_ON_STORY):
            Subscription.objects.get_or_create(user=profile, story=story)
        if (profile.email_flags & Profile.AUTOSUBSCRIBE_TO_PREQUEL):
            Subscription.objects.get_or_create(user=profile, prequel_to=story)
        if (profile.email_flags & Profile.AUTOSUBSCRIBE_TO_SEQUEL):
            Subscription.objects.get_or_create(user=profile, sequel_to=story)

    # Make log entry
    log_type = StoryLog.WRITE
    quel = None
    if (sequel_to):
        log_type = StoryLog.SEQUEL
        quel = sequel_to
    elif (prequel_to):
        log_type = StoryLog.PREQUEL
        quel = prequel_to
    elif (challenge):
        log_type = StoryLog.CHALLENGE_ENT
        challenge = challenge

    if (not new_story):
        log_type = StoryLog.STORY_MOD

    log = StoryLog(
        user=profile,
        story=story,
        quel=quel,
        log_type=log_type,
        prompt=prompt,
        challenge=challenge
    )
    log.save()

    if (not story.draft and prequel_to):
        send_notification_email_story(story, prequel_to, 1)
    elif (not story.draft and sequel_to):
        send_notification_email_story(story, sequel_to, 2)
    elif (not story.draft and challenge):
        send_notification_email_challenge_story(story, challenge)

    return HttpResponseRedirect(reverse('story', args=(story.id,)))


# -----------------------------------------------------------------------------
def browse_stories(request, dataset=0):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
        if (profile.spambot):
            return the_pit(request)

    page_num = safe_int(request.GET.get('page_num', 1))

    if (dataset == 1):
        stories = get_active_stories(page_num, PAGE_BROWSE)
        num_stories = get_num_active_stories()
        label = u'Active stories'
        url = u'/stories/active/'
    elif (dataset == 2):
        stories = get_popular_stories(page_num, PAGE_BROWSE)
        num_stories = Story.objects.exclude(draft=True).count()
        label = u'Popular stories'
        url = u'/stories/popular/'
    else:
        stories = get_recent_stories(page_num, PAGE_BROWSE)
        num_stories = Story.objects.exclude(draft=True).count()
        label = u'Recent stories'
        url = u'/stories/'

    # Build context and render page
    context = {'profile'         : profile,
               'stories'         : stories,
               'page_title'      : u'Stories, page {}'.format(page_num),
               'page_url'        : url,
               'pages'           : bs_pager(page_num, PAGE_BROWSE, num_stories),
               'user_dashboard'  : 1,
               'label'           : label,
               }

    return render(request, 'stories/browse.html', context)


# -----------------------------------------------------------------------------
def active_stories(request):
    return browse_stories(request, 1)


# -----------------------------------------------------------------------------
def popular_stories(request):
    return browse_stories(request, 2)


# -----------------------------------------------------------------------------
@login_required
def story_subscribe(request, story_id, error_title='', error_messages=None):
    story = get_object_or_404(Story, pk=story_id)
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
    if (profile is None):
        raise Http404
    if (profile.spambot):
        return the_pit(request)

    Subscription.objects.get_or_create(user=profile, story=story)

    context = {'thing'           : story,
               'thing_type'      : u'story',
               'thing_url'       : reverse('story', args=[story.id]),
               'page_title'      : u'Subscribe story ' + story.title,
               'error_title'     : error_title,
               'error_messages'  : error_messages,
               'user_dashboard'  : True,
               'profile'         : profile,
               }

    return render(request, 'castle/subscribed.html', context)


# -----------------------------------------------------------------------------
@login_required
def story_unsubscribe(request, story_id, error_title='', error_messages=None):
    story = get_object_or_404(Story, pk=story_id)
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
    if (profile is None):
        raise Http404
    if (profile.spambot):
        return the_pit(request)

    Subscription.objects.filter(user=profile, story=story).delete()

    context = {'thing'           : story,
               'thing_type'      : u'story',
               'thing_url'       : reverse('story', args=[story.id]),
               'page_title'      : u'Unsubscribe story ' + story.title,
               'error_title'     : error_title,
               'error_messages'  : error_messages,
               'user_dashboard'  : True,
               'profile'         : profile,
               }

    return render(request, 'castle/unsubscribed.html', context)


# -----------------------------------------------------------------------------
@login_required
def prequel_subscribe(request, story_id, error_title='', error_messages=None):
    story = get_object_or_404(Story, pk=story_id)
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
    if (profile is None):
        raise Http404
    if (profile.spambot):
        return the_pit(request)

    Subscription.objects.get_or_create(user=profile, prequel_to=story)

    context = {'thing'           : story,
               'thing_type'      : u'prequel',
               'thing_url'       : reverse('story', args=[story.id]),
               'page_title'      : u'Subscribe to prequels on story ' + story.title,
               'error_title'     : error_title,
               'error_messages'  : error_messages,
               'user_dashboard'  : True,
               'profile'         : profile,
               }

    return render(request, 'castle/subscribed.html', context)


# -----------------------------------------------------------------------------
@login_required
def prequel_unsubscribe(request, story_id, error_title='', error_messages=None):
    story = get_object_or_404(Story, pk=story_id)
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
    if (profile is None):
        raise Http404
    if (profile.spambot):
        return the_pit(request)

    Subscription.objects.filter(user=profile, prequel_to=story).delete()

    context = {'thing'           : story,
               'thing_type'      : u'prequel',
               'thing_url'       : reverse('story', args=[story.id]),
               'page_title'      : u'Unsubscribe to prequels on story ' + story.title,
               'error_title'     : error_title,
               'error_messages'  : error_messages,
               'user_dashboard'  : True,
               'profile'         : profile,
               }

    return render(request, 'castle/unsubscribed.html', context)


# -----------------------------------------------------------------------------
@login_required
def sequel_subscribe(request, story_id, error_title='', error_messages=None):
    story = get_object_or_404(Story, pk=story_id)
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
    if (profile is None):
        raise Http404
    if (profile.spambot):
        return the_pit(request)

    Subscription.objects.get_or_create(user=profile, sequel_to=story)

    context = {'thing'           : story,
               'thing_type'      : u'sequel',
               'thing_url'       : reverse('story', args=[story.id]),
               'page_title'      : u'Subscribe to sequels on story ' + story.title,
               'error_title'     : error_title,
               'error_messages'  : error_messages,
               'user_dashboard'  : True,
               'profile'         : profile,
               }

    return render(request, 'castle/subscribed.html', context)


# -----------------------------------------------------------------------------
@login_required
def sequel_unsubscribe(request, story_id, error_title='', error_messages=None):
    story = get_object_or_404(Story, pk=story_id)
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
    if (profile is None):
        raise Http404
    if (profile.spambot):
        return the_pit(request)

    Subscription.objects.filter(user=profile, sequel_to=story).delete()

    context = {'thing'           : story,
               'thing_type'      : u'sequel',
               'thing_url'       : reverse('story', args=[story.id]),
               'page_title'      : u'Unsubscribe to sequels on story ' + story.title,
               'error_title'     : error_title,
               'error_messages'  : error_messages,
               'user_dashboard'  : True,
               'profile'         : profile,
               }

    return render(request, 'castle/unsubscribed.html', context)


# -----------------------------------------------------------------------------
def tags(request, tag_name):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
        if (profile.spambot):
            return the_pit(request)

    page_num = safe_int(request.GET.get('page_num', 1))

    # Find stories with this tag name (forced to upper case)
    tag_name = tag_name.upper()
    (num_stories, stories) = get_tagged_stories(tag_name, page_num, PAGE_BROWSE)
    if (num_stories == 0):
        # No stories found, give the user
        return tags_null(request, u'No stories tagged ' + tag_name)

    label = u'Stories tagged “' + unicode(tag_name) + u'”'
    url = u'/tag/' + urlquote(tag_name) + u'/'

    # Build context and render page
    context = {'profile'         : profile,
               'stories'         : stories,
               'page_title'      : u'Tag ' + tag_name,
               'page_url'        : url,
               'pages'           : bs_pager(page_num, PAGE_BROWSE, num_stories),
               'user_dashboard'  : 1,
               'label'           : label,
               }
    return render(request, 'stories/browse.html', context)


# -----------------------------------------------------------------------------
def tags_null(request, error_msg=None):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
        if (profile.spambot):
            return the_pit(request)

    page_num = safe_int(request.GET.get('page_num', 1))

    # List all the tags
    num_tags = get_num_tags()
    tags = get_all_tags(page_num, PAGE_ALLTAGS)

    label = u'All tags'
    url = u'/tags/'

    error_title = u'Tag not found' if error_msg else None
    error_messages = [error_msg] if error_msg else None

    # Build context and render page
    context = {'profile'          : profile,
               'tags'             : tags,
               'num_tags'         : num_tags,
               'page_title'       : u'All tags',
               'page_url'         : url,
               'pages'            : bs_pager(page_num, PAGE_ALLTAGS, num_tags),
               'user_dashboard'   : 1,
               'error_title'      : error_title,
               'error_messages'   : error_messages,
               'label'            : label,
               }
    return render(request, 'stories/all_tags.html', context)

# -----------------------------------------------------------------------------
