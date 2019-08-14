
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

from django.core.management.base import BaseCommand, CommandError
from castle.models import *
from django.db import transaction, connection
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
import time
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Run nightly magic to select featured story'
    args =''

    #-----------------------------------------------------------------------------
    def log(self, logfile, message):
        if (logfile is None):
            return
        ln = u'{:0.0f}: {}'.format(time.time(), message)

        f = open(logfile, 'a+')
        if (f):
            f.write(ln+u'\n')
            f.close()
    
    #-----------------------------------------------------------------------------
    @transaction.atomic
    def do_nightly(self):
        db      = getattr(settings, 'DB', 'mysql')
        logfile = getattr(settings, 'NIGHTLY_LOG', None)

        self.log(logfile, 'Running nightly')

        #---------------------------------------------------
        # Remove all unverified accounts older than 14 days
        #---------------------------------------------------
        # 14 days ago
        tt = timezone.now() - timedelta(days=14)
        unconfirmed_profiles = Profile.objects.exclude(email_auth=0).exclude(ctime__lte=tt)
        for up in unconfirmed_profiles:
            up.delete()

        #---------------------------------------------------
        # Activity-related things
        #---------------------------------------------------
        # Zero out all activity values
        Story.objects.all().update(activity=0)
        Prompt.objects.all().update(activity=0)
        Challenge.objects.all().update(activity=0)
        
        cursor = connection.cursor()

        #---------------------------------------------        
        # Featured Story
        #---------------------------------------------
        if (db == 'mysql'):
            cursor.execute(
                "UPDATE castle_story AS s SET activity = (SELECT "+
                "sum(l.log_type / (timestampdiff(day,l.ctime,now())+1)) "+
                "FROM castle_storylog AS l "+
                "WHERE l.story_id IS NOT NULL AND s.id=l.story_id "+
                "AND ((timestampdiff(day,l.ctime,now())) < 30) "+
                "AND (l.ignore_me != 1) "+
                "AND l.user_id != s.user_id )")
        elif (db == 'postgres'):
            cursor.execute(
                "UPDATE castle_story AS s SET activity = (SELECT "+
                "sum(l.log_type / (date_part('day', NOW() - l.ctime)+1)) "+
                "FROM castle_storylog AS l "+
                "WHERE l.story_id IS NOT NULL AND s.id=l.story_id "+
                "AND (l.ignore_me != TRUE) "+
                "AND ((date_part('day', NOW() - l.ctime)) < 30) "+
                "AND l.user_id != s.user_id )")

        # Find most active story
        mas = Story.objects.filter(activity__isnull = False).order_by('-activity')[0:1]
        if (mas and (mas[0])):
            # Find 'featured' object in Misc table and update with new most-active story
            ff = Misc.objects.filter(key='featured')
            if (ff):
                f = ff[0]
            else:
                f = Misc(key='featured')
            
            f.i_val = mas[0].id
            f.act_type = 1
            f.save()
            
            # Record featured story as having been featured
            if (mas[0].ftime is None):
                mas[0].ftime = timezone.now()
                mas[0].save()
            
            self.log(logfile, 'Featured story sid {} with score {}'.format(mas[0].id, mas[0].activity))
                
        #---------------------------------------------        
        # Featured Prompt
        #---------------------------------------------
        if (db == 'mysql'):
            cursor.execute(
                "UPDATE castle_prompt AS p SET activity = (SELECT "+
                "sum(l.log_type / (timestampdiff(day,l.ctime,now())+1)) "+
                "FROM castle_storylog AS l "+
                "WHERE l.prompt_id IS NOT NULL AND p.id=l.prompt_id "+
                "AND ((timestampdiff(day,l.ctime,now())) < 30) "+
                "AND (l.ignore_me != 1) "+
                "AND l.user_id != p.user_id )")
        elif (db == 'postgres'):
            cursor.execute(
                "UPDATE castle_prompt AS p SET activity = (SELECT "+
                "sum(l.log_type / (date_part('day', NOW() - l.ctime)+1)) "+
                "FROM castle_storylog AS l "+
                "WHERE l.prompt_id IS NOT NULL AND p.id=l.prompt_id "+
                "AND ((date_part('day', NOW() - l.ctime)) < 30) "+
                "AND (l.ignore_me != TRUE) "+
                "AND l.user_id != p.user_id )")

        # Find most active challenge
        mapr = Prompt.objects.filter(activity__isnull = False).order_by('-activity')[0:1]
        if (mapr and (mapr[0])):
            # Find 'featured' object in Misc table and update with new most-active challenge
            ff = Misc.objects.filter(key='featured_prompt')
            if (ff):
                f = ff[0]
            else:
                f = Misc(key='featured_prompt')
            
            f.i_val = mapr[0].id
            f.act_type = 2
            f.save()
            
            # Record featured story as having been featured
            if (mapr[0].ftime is None):
                mapr[0].ftime = timezone.now()
                mapr[0].save()
            
            self.log(logfile, 'Featured prompt id {} with score {}'.format(mapr[0].id, mapr[0].activity))
                
        #---------------------------------------------        
        # Featured Challenge
        #---------------------------------------------
        if (db == 'mysql'):
            cursor.execute(
                "UPDATE castle_challenge AS c SET activity = (SELECT "+
                "sum(l.log_type / (timestampdiff(day,l.ctime,now())+1)) "+
                "FROM castle_storylog AS l "+
                "WHERE l.challenge_id IS NOT NULL AND c.id=l.challenge_id "+
                "AND ((timestampdiff(day,l.ctime,now())) < 30) "+
                "AND (l.ignore_me != 1) "+
                "AND l.user_id != c.user_id )")
        elif (db == 'postgres'):
            cursor.execute(
                "UPDATE castle_challenge AS c SET activity = (SELECT "+
                "sum(l.log_type / (date_part('day', NOW() - l.ctime)+1)) "+
                "FROM castle_storylog AS l "+
                "WHERE l.challenge_id IS NOT NULL AND c.id=l.challenge_id "+
                "AND ((date_part('day', NOW() - l.ctime)) < 30) "+
                "AND (l.ignore_me != TRUE) "+
                "AND l.user_id != c.user_id )")

        # Find most active challenge
        mac = Challenge.objects.filter(activity__isnull = False).order_by('-activity')[0:1]
        if (mac and (mac[0])):
            # Find 'featured' object in Misc table and update with new most-active challenge
            ff = Misc.objects.filter(key='featured_challenge')
            if (ff):
                f = ff[0]
            else:
                f = Misc(key='featured_challenge')
            
            f.i_val = mac[0].id
            f.act_type = 3
            f.save()
            
            # Record featured story as having been featured
            if (mac[0].ftime is None):
                mac[0].ftime = timezone.now()
                mac[0].save()

            self.log(logfile, 'Featured challenge id {} with score {}'.format(mac[0].id, mac[0].activity))
        
        # Clear out unverified user accounts after 21 days
        pp = Profile.objects.exclude(email_auth=0).filter(email_time__lte=timezone.now()-timedelta(days=21))
        c = pp.count()
        if (c > 0):
            self.log(logfile, 'Deleting {} unconfirmed users older than 21 days'.format(pp.count()))
            pp.delete()

        return None

            
    #-----------------------------------------------------------------------------
    def handle(self, *args, **options):
        self.do_nightly()
        
