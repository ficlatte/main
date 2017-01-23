
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

from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.conf import settings
from .models import *

def send_conf_email(profile, token):
    url = getattr(settings, 'SITE_URL', 'http://www.example.com/')
    
    mail_message  = "Hi.\nThis is the Ficlatte server.  You, or someone claiming\n";
    mail_message += "to be you registered at https://ficlatte.com\n\n";
    mail_message += "If this really is you, please click on the following link:\n\n";
    mail_message += "{}/confirmation/yes/{}/{}\n\n".format(url, profile.id, token);
    mail_message += "If this is not you, click on the link below and we'll never\n";
    mail_message += "send you e-mail ever again:\n\n";
    mail_message += "{}/confirmation/no/{}/{}\n\n".format(url, profile.id, token);
    mail_message += "Best regards,\n\n";
    mail_message += "The ficlatte team\n";
    
    send_mail('Ficlatte e-mail confirmation',
              mail_message,
              'Ficlatte Team <noreply@ficlatte.com>',
              [profile.email_addr],
              fail_silently = False)

def send_notification_email(profile, subject, message):
    send_mail(subject,
              message,
              'Ficlatte Team <noreply@ficlatte.com>',
              [profile.email_addr],
              fail_silently = False)

def send_notification_email_comment(com):
    url = getattr(settings, 'SITE_URL', 'http://www.example.com/')

    # Is the comment on a story or a blog?
    if (com.story):
        parent = com.story
        parent_type = u'story'
        subs = Subscription.objects.filter(story=parent)
        url1 = u'{}{}'.format(url, reverse('story', args=[parent.id]))
        unsub_url = u'{}{}'.format(url, reverse('story-unsub', args=[parent.id]))

    elif (com.blog):
        parent = com.blog
        parent_type = u'blog'
        subs = Subscription.objects.filter(blog=parent)
        url1 = u'{}{}'.format(url, reverse('blog', args=[parent.id]))
        unsub_url = u'{}{}'.format(url, reverse('blog-unsub', args=[parent.id]))
        
    else:
        # Neither a blog nor a story, something weird is going on,
        # so just bug out here
        return None
    
    # Build e-mail text
    subject  = u'Ficlatte comment on '+parent.title+u' by '+com.user.pen_name
    
    message  = u"Hi.\nThis is the Ficlatte server.  You are currently subscribed to "
    message += u"receive notifications of new comments posted to Ficlatte "+parent_type+" "
    message += u'"'+parent.title+u'".\n\n'
    message += com.user.pen_name+u' just posted a comment:\n\n'
    message += com.body
    message += u'\n\nTo see the comment at Ficlatte, click here:\n'
    message += url1+u'\n'
    message += u'To stop receiving notifications of comments on this '+parent_type+u', click here:\n'
    message += unsub_url+u'\n'
    message += u'To adjust your e-mail preferences, update your profile here:\n'
    message += u'{}{}'.format(url, reverse('profile'))
    message += u'\n\nKeep writing!\n\nThe Ficlatte team\n'

    # Loop through everyone subscribed to this thread
    for s in subs:
        # But only send messages to people other than the comment author
        if (s.user != com.user):
            send_notification_email(s.user, subject, message)

def send_pass_reset_email(profile, token):
    url = getattr(settings, 'SITE_URL', 'http://www.example.com/')
    
    mail_message  = "To initiate the password reset process for your Ficlatte account,\n";
    mail_message += "click the link below:\n\n";
    mail_message += "{}/passwordreset/{}/{}\n\n".format(url, profile.id, token);
    mail_message += "If clicking the link above doesn't work, please copy and paste\n";
    mail_message += "the URL into a new browser window instead.\n\n";
    mail_message += "Best regards,\n\n";
    mail_message += "The Ficlatte team\n";
    
    send_mail('Ficlatte password reset',
              mail_message,
              'Ficlatte Team <noreply@ficlatte.com>',
              [profile.email_addr],
              fail_silently = False)
