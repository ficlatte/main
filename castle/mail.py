
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
from django.conf import settings
from castle.models import Profile

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
#              [profile.email_addr],
              [profile.email_addr],
              fail_silently = False)
