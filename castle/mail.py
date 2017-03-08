
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

from string import Template
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.conf import settings
from .models import *

#-----------------------------------------------------------------------------
def send_conf_email(profile, token):
    url = getattr(settings, 'SITE_URL', 'http://www.example.com/')
    
    mail_template = Template("""Hi.
This is the Ficlatte server.  You, or someone claiming
to be you registered at https://ficlatte.com

If this really is you, please click on the following link:

$url/confirmation/yes/$profile_id/$token

If this is not you, click on the link below and we'll never
send you e-mail ever again:

$url/confirmation/no/$profile_id/$token

Best regards,

The Ficlatte team""")

    mail_message = mail_template.substitute(url=url, profile_id=profile.id, token=token)

    
    send_mail('Ficlatte e-mail confirmation',
              mail_message,
              'Ficlatte Team <noreply@ficlatte.com>',
              [profile.email_addr],
              fail_silently = False)

#-----------------------------------------------------------------------------
def send_notification_email(profile, subject, message):
    send_mail(subject,
              message,
              'Ficlatte Team <noreply@ficlatte.com>',
              [profile.email_addr],
              fail_silently = False)

#-----------------------------------------------------------------------------
def send_notification_email_comment(com):
	url = getattr(settings, 'SITE_URL', 'http://www.example.com/')

    # Is the comment on a story, prompt, challenge, or blog?
	if (com.story):
		parent = com.story
		parent_type = u'story'
		subs = Subscription.objects.filter(story=parent)
		parent_url = u'{}{}'.format(url, reverse('story', args=[parent.id]))
		unsub_url = u'{}{}'.format(url, reverse('story-unsub', args=[parent.id]))
        
	elif (com.prompt):
		parent = com.prompt
		parent_type = u'prompt'
		subs = Subscription.objects.filter(prompt=parent)
		parent_url = u'{}{}'.format(url, reverse('prompt', args=[parent.id]))
		unsub_url = u'{}{}'.format(url, reverse('prompt-unsub', args=[parent.id]))
        
	elif (com.challenge):
		parent = com.challenge
		parent_type = u'challenge'
		subs = Subscription.objects.filter(challenge=parent)
		parent_url = u'{}{}'.format(url, reverse('challenge', args=[parent.id]))
		unsub_url = u'{}{}'.format(url, reverse('challenge-unsub', args=[parent.id]))

	elif (com.blog):
		parent = com.blog
		parent_type = u'blog'
		subs = Subscription.objects.filter(blog=parent)
		parent_url = u'{}{}'.format(url, reverse('blog', args=[parent.id]))
		unsub_url = u'{}{}'.format(url, reverse('blog-unsub', args=[parent.id]))
        
	else:
        # Not a blog, prompt, challenge, or story, something weird is going on,
        # so just bug out here
		return None
    
    # Build e-mail text
	subject = Template('Ficlatte comment on $parent_title by $comment_user').substitute(parent_title=parent.title, comment_user=com.user.pen_name)

	message_template = Template("""Hi.
This is the Ficlatte server.  You are currently subscribed to receive notifications of new comments posted to Ficlatte $parent_type "$parent_title".

$comment_user just posted a comment:
	
$comment_body

To see the comment at Ficlatte, click here:
$parent_url
To stop receiving notifications of comments on this story, click here:
$parent_unsub_url
To adjust your e-mail preferences, update your profile here:
$user_profile_url

Keep writing!

The Ficlatte team""")

	message = message_template.substitute(
		parent_type=parent_type, parent_title=parent.title,
		comment_user=com.user.pen_name, comment_body=com.body,
		parent_url=parent_url, parent_unsub_url=unsub_url,
		user_profile_url=(url + reverse('profile')))

    # Loop through everyone subscribed to this thread
	for sub in subs:
        # But only send messages to people other than the comment author, and only if there is comment text
		if (sub.user != com.user and com.body):
			send_notification_email(sub.user, subject, message)

#-----------------------------------------------------------------------------
def send_notification_email_story(story, parent):
	url = getattr(settings, 'SITE_URL', 'http://www.example.com/')

	child_type = u''
	subs = Subscription.objects.filter(story=parent)
	child_url = u'{}{}'.format(url, reverse('story', args=[story.id]))
	unsub_url = u'{}{}'.format(url, reverse('story-unsub', args=[parent.id]))

    # Is the comment on a story or a blog?
	if story.prequel_to == parent:
		child_type = u'prequel'

	elif story.sequel_to == parent:
		child_type = u'sequel'

	else:
        # Neither a prequel or a sequel, something weird is going on,
        # so just bug out here
		return None

    # Build e-mail text
	subject = Template(
		'Ficlatte $child_type to "$parent_title" by $story_user').substitute(
			child_type=child_type, parent_title=parent.title, story_user=story.user.pen_name)

	message_template = Template("""Hi.
This is the Ficlatte server.  You are currently subscribed to receive notifications of new stories posted to Ficlatte story "$parent_title".

$child_user just posted a $child_type, "$child_title":

$child_body

To read the story at Ficlatte, click here:
$child_url

Keep writing!

The Ficlatte team""")

	message = message_template.substitute(
		parent_title=parent.title, child_title=story.title,
		child_user=story.user.pen_name, child_type=child_type, child_body=story.body,
		child_url=child_url, parent_unsub_url=unsub_url,
		user_profile_url=(url, reverse('profile')))

    # Loop through everyone subscribed to this story
	for sub in subs:
        # But only send messages to people other than the story author
		if sub.user != story.user:
			send_notification_email(sub.user, subject, message)
