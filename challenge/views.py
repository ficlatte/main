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

from django.db.models import F
from django.shortcuts import redirect
from datetime import datetime
from comment.views import *
from .forms import ChallengeDateForm
from the_pit.views import the_pit

# -----------------------------------------------------------------------------
def get_popular_challenges(page_num=1, page_size=10):
    db = getattr(settings, 'DB', 'mysql')
    if (db == 'mysql'):
        return Challenge.objects.raw(
            "SELECT c.id as id, " +
            "SUM(1/(TIMESTAMPDIFF(day, l.ctime, NOW())+1)) AS score " +
            "FROM castle_storylog AS l " +
            "LEFT JOIN castle_challenge AS c ON c.id=l.challenge_id " +
            "WHERE l.user_id != c.user_id " +
            "AND l.log_type = " + str(StoryLog.VIEW) + " " +
            "GROUP BY l.challenge_id ORDER BY score DESC LIMIT " +
            str((page_num - 1) * page_size) + "," + str(page_size))
    elif (db == 'postgres'):
        return Challenge.objects.raw(
            "SELECT c.id as id, " +
            "SUM(1/(date_part('day', NOW() - l.ctime)+1)) AS score " +
            "FROM castle_storylog AS l " +
            "LEFT JOIN castle_challenge AS c ON c.id=l.challenge_id " +
            "WHERE l.user_id != c.user_id " +
            "AND l.log_type = " + str(StoryLog.VIEW) + " " +
            "GROUP BY c.id ORDER BY score DESC LIMIT " + str(page_size) + " " +
            "OFFSET " + str((page_num - 1) * page_size))
    return Challenge.objects.all()


# -----------------------------------------------------------------------------
def get_active_challenges(page_num=1, page_size=10):
    first = (page_num - 1) * page_size
    last = first + page_size
    return Challenge.objects.filter(activity__isnull=False, activity__gt=0).order_by('-activity')[first:last]


# -----------------------------------------------------------------------------
def get_num_active_challenges():
    return Challenge.objects.filter(activity__gt=0).count()


# -----------------------------------------------------------------------------
def get_recent_challenges(page_num=1, page_size=10):
    first = (page_num - 1) * page_size
    last = first + page_size
    return Challenge.objects.all().order_by('-ctime')[first:last]


# -----------------------------------------------------------------------------
def get_recent_winners(page_num=1, page_size=10):
    first = (page_num - 1) * page_size
    last = first + page_size
    return Story.objects.filter(challenge__winner_id=F('id'), challenge__winner_id__isnull=False).order_by('-ctime')[first:last]


# -----------------------------------------------------------------------------
# Challenge views
# -----------------------------------------------------------------------------
def browse_challenges(request, dataset=0):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
        if (profile.spambot):
            return the_pit(request)

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
    context = {'profile'         : profile,
               'challenges'      : challenges,
               'page_title'      : u'Challenges, page {}'.format(page_num),
               'page_url'        : url,
               'pages'           : bs_pager(page_num, PAGE_BROWSE, num_challenges),
               'user_dashboard'  : 1,
               'label'           : label,
               }

    return render(request, 'challenges/challenges_recent.html', context)


# -----------------------------------------------------------------------------
def active_challenges(request):
    return browse_challenges(request, 1)


# -----------------------------------------------------------------------------
def popular_challenges(request):
    return browse_challenges(request, 2)


# -----------------------------------------------------------------------------
def challenges(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
        if (profile.spambot):
            return the_pit(request)

    # Get featured challenge
    featured_id = Misc.objects.filter(key='featured_challenge')
    featured = None
    if (featured_id):
        featured_query = Challenge.objects.filter(id=featured_id[0].i_val)
        if (featured_query):
            featured = featured_query[0]

    # Build context and render page
    context = {'profile'           : profile,
               'challenges'        : challenges,
               'featured'          : featured,
               'popular'           : get_popular_challenges(1, 4),
               'active'            : get_active_challenges(1, 10),
               'recent'            : get_recent_challenges(1, 10),
               'recent_winners'    : get_recent_winners(1, 10),
               'page_title'        : u'Challenges',
               'challenge_button'  : (profile is not None),
               'user_dashboard'    : (profile is not None),
               'page_url'          : u'/challenges/',
               }

    return render(request, 'challenges/challenges.html', context)


# -----------------------------------------------------------------------------
def challenge_view(request, challenge_id, comment_text=None, error_title='', error_messages=None):
    # Get challenge
    challenge = get_object_or_404(Challenge, pk=challenge_id)

    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
        if (profile.spambot):
            return the_pit(request)

    # Get stories inspired by challenge
    page_num = safe_int(request.GET.get('page_num', 1))
    stories = challenge.story_set.exclude(draft=True).order_by('ctime')[(page_num - 1) * PAGE_STORIES:page_num * PAGE_STORIES]
    num_stories = challenge.story_set.exclude(draft=True).count()

    # Get list of participants
    participants_list = challenge.story_set.exclude(draft=True).values('user__pen_name').distinct()
    participants = Profile.objects.filter(pen_name__in=participants_list)

    # Get comments
    page_num = safe_int(request.GET.get('page_num', 1))
    comments = challenge.comment_set.filter(spam__lt=Comment.SPAM_QUARANTINE).order_by('ctime')[(page_num - 1) * PAGE_COMMENTS:page_num * PAGE_COMMENTS]

    # Challenge's owner gets an edit link
    owner = ((profile is not None) and (profile == challenge.user))

    # Log view
    if (profile and profile.email_authenticated()):
        log = StoryLog(
            user=profile,
            challenge=challenge,
            log_type=StoryLog.VIEW
        )
        log.save()

        # Suppress challenge if marked as mature and either the user is not logged in
        # or the user has not enabled viewing of mature challenges
    suppressed = False
    if (challenge.mature):
        if ((not profile) or ((challenge.user != profile) and (not profile.mature))):
            suppressed = True

            # Is user subscribed?
    subscribed = False
    if (profile and (Subscription.objects.filter(challenge=challenge, user=profile).count() > 0)):
        subscribed = True

    entry_subscribed = False
    if (profile and (Subscription.objects.filter(ch_entry=challenge, user=profile).count() > 0)):
        entry_subscribed = True

        # Build context and render page
    context = {'profile'              : profile,
               'challenge'            : challenge,
               'stories'              : stories,
               'owner'                : owner,
               'subscribed'           : subscribed,
               'entry_subscribed'     : entry_subscribed,
               'participants'         : participants,
               'comments'             : comments,
               'page_title'           : u'Challenge ' + challenge.title,
               'challenge_sidepanel'  : 1,
               'page_url'             : u'/challenges/' + unicode(challenge.id) + u'/',
               'pages'                : bs_pager(page_num, PAGE_STORIES, num_stories),
               'comment_text'         : comment_text,
               'suppressed'           : suppressed,
               'error_title'          : error_title,
               'error_messages'       : error_messages,
               }

    return render(request, 'challenges/challenge.html', context)


# -----------------------------------------------------------------------------
@login_required
def new_challenge(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
        if (profile.spambot):
            return the_pit(request)

    if (request.method == "POST"):
        form = ChallengeDateForm(request.POST, instance=post)
        if (form.is_valid()):
            post = form.save(commit=False)
            post.save()
            return redirect('challenge', pk=post.pk)
    else:
        form = ChallengeDateForm()

        # Build context and render page
    context = {'profile'         : profile,
               'challenge'       : Challenge(),  # Create blank challenge for default purposes
               'page_title'      : u'Create new challenge',
               'form'            : form,
               'stime'           : timezone.now,
               'etime'           : timezone.now,
               'tags'            : u'',
               'length_limit'    : 1024,
               'length_min'      : 30,
               'user_dashboard'  : 1,
               }

    return render(request, 'challenges/edit_challenge.html', context)


# -----------------------------------------------------------------------------
@login_required
def edit_challenge(request, challenge_id):
    # Get challenge
    challenge = get_object_or_404(Challenge, pk=challenge_id)

    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
        if (profile.spambot):
            return the_pit(request)

    # User can only edit their own challenges
    if (challenge.user != profile):
        raise Http404

    # Build context and render page
    context = {'profile'         : profile,
               'challenge'       : challenge,
               'page_title'      : u'Edit challenge ' + challenge.title,
               'stime'           : timezone.now,
               'etime'           : timezone.now,
               'length_limit'    : 1024,
               'length_min'      : 30,
               'user_dashboard'  : 1,
               }

    return render(request, 'challenges/edit_challenge.html', context)


# -----------------------------------------------------------------------------
@login_required
@transaction.atomic
def submit_challenge(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
        if (profile.spambot):
            return the_pit(request)

    # Get bits and bobs
    errors = []
    challenge = get_foo(request.POST, Challenge, 'chid')
    new_challenge = (challenge is None)

    nowdate = datetime.now().strftime('%Y-%m-%d')

    if (not profile.email_authenticated()):
        errors.append(u'You must have authenticated your e-mail address before creating a challenge')
    else:
        # Get challenge object, either existing or new
        # new_challenge = False
        if (challenge is None):
            challenge = Challenge(user=profile)
            # new_challenge = True

        # Populate challenge object with data from submitted form
        challenge.title = request.POST.get('title', '')
        challenge.body = request.POST.get('body', '')
        challenge.mature = request.POST.get('is_mature', False)
        challenge.stime = request.POST.get('stime', timezone.now)
        challenge.etime = request.POST.get('etime', timezone.now)

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
        context = {'profile'         : profile,
                   'challenge'       : challenge,
                   'length_limit'    : 1024,
                   'length_min'      : 30,
                   'page_title'      : u'Edit challenge ' + challenge.title,
                   'user_dashboard'  : 1,
                   'error_title'     : 'Challenge submission unsuccessful',
                   'error_messages'  : errors,
                   }

        return render(request, 'challenges/edit_challenge.html', context)

    # Is the prompt new?
    if (new_challenge is None):
        challenge.ctime = timezone.now()

    # Set modification time
    challenge.mtime = timezone.now()

    # No problems, update the database and redirect
    challenge.save()

    # Auto-subscribe to e-mail notifications according to user's preferences
    if (new_challenge):
        if (profile.email_flags & Profile.AUTOSUBSCRIBE_ON_CHALLENGE):
            Subscription.objects.get_or_create(user=profile, challenge=challenge)
        if (profile.email_flags & Profile.AUTOSUBSCRIBE_TO_CHALLENGE_ENTRY):
            Subscription.objects.get_or_create(user=profile, ch_entry=challenge)

    # Log entry
    if (profile) and (profile.email_authenticated()):
        log_type = StoryLog.CHALLENGE
        if (not new_challenge):
            log_type = StoryLog.CHALLENGE_MOD
        log = StoryLog(
            user=profile,
            log_type=log_type,
            challenge=challenge,
        )
        log.save()

    return HttpResponseRedirect(reverse('challenge', args=(challenge.id,)))


# -----------------------------------------------------------------------------
@login_required
def challenge_winner(request, challenge_id, story_id):
    # Get challenge
    challenge = get_object_or_404(Challenge, pk=challenge_id)
    story = get_object_or_404(Story, pk=story_id)

    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
        if (profile.spambot):
            return the_pit(request)

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
            user=user,
            story=story,
            log_type=log_type,
            challenge=challenge,
        )
        log.save()

    # Indicate successful choice
    return HttpResponseRedirect(reverse('challenge', args=(challenge.id,)))


# -----------------------------------------------------------------------------
@login_required
def challenge_subscribe(request, challenge_id, error_title='', error_messages=None):
    challenge = get_object_or_404(Challenge, pk=challenge_id)
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
    if (profile is None):
        raise Http404
    if (profile.spambot):
        return the_pit(request)

    Subscription.objects.get_or_create(user=profile, challenge=challenge)

    context = {'thing'           : challenge,
               'thing_type'      : u'challenge',
               'thing_url'       : reverse('challenge', args=[challenge.id]),
               'page_title'      : u'Subscribe challenge ' + challenge.title,
               'error_title'     : error_title,
               'error_messages'  : error_messages,
               'user_dashboard'  : True,
               'profile'         : profile,
               }

    return render(request, 'castle/subscribed.html', context)


# -----------------------------------------------------------------------------
@login_required
def challenge_unsubscribe(request, challenge_id, error_title='', error_messages=None):
    challenge = get_object_or_404(Challenge, pk=challenge_id)
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
    if (profile is None):
        raise Http404
    if (profile.spambot):
        return the_pit(request)

    Subscription.objects.filter(user=profile, challenge=challenge).delete()

    context = {'thing'           : challenge,
               'thing_type'      : u'challenge',
               'thing_url'       : reverse('challenge', args=[challenge.id]),
               'page_title'      : u'Unsubscribe challenge ' + challenge.title,
               'error_title'     : error_title,
               'error_messages'  : error_messages,
               'user_dashboard'  : True,
               'profile'         : profile,
               }

    return render(request, 'castle/unsubscribed.html', context)


# -----------------------------------------------------------------------------
@login_required
def challenge_entry_subscribe(request, challenge_id, error_title='', error_messages=None):
    challenge = get_object_or_404(Challenge, pk=challenge_id)
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
    if (profile is None):
        raise Http404
    if (profile.spambot):
        return the_pit(request)

    Subscription.objects.get_or_create(user=profile, ch_entry=challenge)

    context = {'thing'           : challenge,
               'thing_type'      : u'challenge entry',
               'thing_url'       : reverse('challenge', args=[challenge.id]),
               'page_title'      : u'Subscribe to entries on challenge ' + challenge.title,
               'error_title'     : error_title,
               'error_messages'  : error_messages,
               'user_dashboard'  : True,
               'profile'         : profile,
               }

    return render(request, 'castle/subscribed.html', context)


# -----------------------------------------------------------------------------
@login_required
def challenge_entry_unsubscribe(request, challenge_id, error_title='', error_messages=None):
    challenge = get_object_or_404(Challenge, pk=challenge_id)
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
    if (profile is None):
        raise Http404
    if (profile.spambot):
        return the_pit(request)

    Subscription.objects.filter(user=profile, ch_entry=challenge).delete()

    context = {'thing'           : challenge,
               'thing_type'      : u'challenge entry',
               'thing_url'       : reverse('challenge', args=[challenge.id]),
               'page_title'      : u'Unsubscribe to entries on challenge ' + challenge.title,
               'error_title'     : error_title,
               'error_messages'  : error_messages,
               'user_dashboard'  : True,
               'profile'         : profile,
               }

    return render(request, 'castle/unsubscribed.html', context)

# -----------------------------------------------------------------------------
