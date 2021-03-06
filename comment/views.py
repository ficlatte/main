
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


from django.core.exceptions import ObjectDoesNotExist
from castle.views import *
from the_pit.views import the_pit

# -----------------------------------------------------------------------------
# Comment Submission
# -----------------------------------------------------------------------------
@login_required
@transaction.atomic
def submit_comment(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated):
        profile = request.user.profile
    if (not profile):
        raise Http404
    if (profile.spambot):
        return the_pit(request)

    # Get bits and bobs
    errors = []
    old_rating = None
    blog       = get_foo(request.POST, Blog, 'bid')
    story      = get_foo(request.POST, Story, 'sid')
    prompt     = get_foo(request.POST, Prompt, 'pid')
    challenge  = get_foo(request.POST, Challenge, 'chid')

    if (story):
        try:
            r = Rating.objects.get(user=profile, story=story)
            old_rating = r.rating
        except ObjectDoesNotExist:
            old_rating = None

    rating = request.POST.get('rating', None)
    if (rating is not None):
        rating = int(rating)

    if (not profile.email_authenticated()):
        errors.append(u'You must have authenticated your e-mail address before posting a comment')

    # Create comment object
    comment = Comment(user      = profile,
                      blog      = blog,
                      story     = story,
                      prompt    = prompt,
                      challenge = challenge)

    # Populate comment object with data from submitted form
    comment.body = request.POST.get('body', '')

    # Condense all end-of-line markers into \n
    comment.body = re_crlf.sub(u"\n", comment.body)

    # Check for obvious spam indicators (but don't signal to spam bot that we're onto them)
    quarantine = False
    if (comment.body.find('<a href=') >= 0):
        comment.spam = Comment.SPAM_QUARANTINE
        quarantine = True

    # Check for submission errors
    l = len(comment.body)
    if ((l < 1) and (rating is None)):
        # Empty comments are allowed if the user is making a rating
        errors.append(u'Comment body must be at least 1 character long')

    if (l > 1024):
        errors.append(u'Comment is over 1024 characters (currently ' + str(l) + u')')

    # If there have been errors, re-display the page
    if (errors):
        # Build context and render page
        if (blog):
            from blog.views import blog_view
            return blog_view(request, blog.id, comment.body, u'Comment submission failed', errors)
        elif (story):
            from story.views import story_view
            return story_view(request, story.id, comment.body, rating, u'Comment submission failed', errors)
        elif (prompt):
            from prompt.views import prompt_view
            return prompt_view(request, prompt.id, comment.body, u'Comment submission failed', errors)
        else:
            from challenge.views import challenge_view
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
                user=profile,
                story=story,
                ignore_me=quarantine,
                comment=comment,
                log_type=StoryLog.COMMENT
            )
            log.save()
        # If there was no previous rating and there is a rating,
        # log that a rating has been made
        if ((rating is not None) and (old_rating is None)):
            log = StoryLog(
                user=profile,
                story=story,
                ignore_me=quarantine,
                log_type=StoryLog.RATE
            )
            log.save()
    elif (prompt):
        # If comment body is longer than 0, log that comment has been made
        if (l > 0):
            log = StoryLog(
                user=profile,
                prompt=prompt,
                comment=comment,
                ignore_me=quarantine,
                log_type=StoryLog.COMMENT
            )
            log.save()
    elif (challenge):
        # If comment body is longer than 0, log that comment has been made
        if (l > 0):
            log = StoryLog(
                user=profile,
                challenge=challenge,
                comment=comment,
                ignore_me=quarantine,
                log_type=StoryLog.COMMENT
            )
            log.save()

    # Send e-mail messages to subscribed users
    if not quarantine:
        send_notification_email_comment(comment)

    # Auto-subscribe to e-mail notifications according to user's preferences
    if (profile and not quarantine):
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


# -----------------------------------------------------------------------------
@login_required
def like_comment(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    # Get user profile
    profile = None
    if request.user.is_authenticated:
        profile = request.user.profile
    if profile is None:
        raise Http404
    if (profile.spambot):
        return the_pit(request)

    CommentLike.objects.get_or_create(user=profile, comment=comment)

    if comment.blog:
        return HttpResponseRedirect(reverse('blog', args=(comment.blog.id,)))
    elif comment.story:
        return HttpResponseRedirect(reverse('story', args=(comment.story.id,)))
    elif comment.prompt:
        return HttpResponseRedirect(reverse('prompt', args=(comment.prompt.id,)))
    elif comment.challenge:
        return HttpResponseRedirect(reverse('challenge', args=(comment.challenge.id,)))


# -----------------------------------------------------------------------------
@login_required
def unlike_comment(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    # Get user profile
    profile = None
    if request.user.is_authenticated:
        profile = request.user.profile
    if profile is None:
        raise Http404
    if (profile.spambot):
        return the_pit(request)

    CommentLike.objects.filter(user=profile, comment=comment).delete()

    if comment.blog:
        return HttpResponseRedirect(reverse('blog', args=(comment.blog.id,)))
    elif comment.story:
        return HttpResponseRedirect(reverse('story', args=(comment.story.id,)))
    elif comment.prompt:
        return HttpResponseRedirect(reverse('prompt', args=(comment.prompt.id,)))
    elif comment.challenge:
        return HttpResponseRedirect(reverse('challenge', args=(comment.challenge.id,)))

# -----------------------------------------------------------------------------
