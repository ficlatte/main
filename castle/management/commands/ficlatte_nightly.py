
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

from django.core.management.base import BaseCommand, CommandError
from castle.models import *
from django.db import transaction, connection
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

class Command(BaseCommand):
    help = 'Import old Ficlatte database into Django database'
    args =''
    
    @transaction.atomic
    def do_nightly(self):
        db = getattr(settings, 'DB', 'mysql')

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
                "AND l.user_id != s.user_id )")
        elif (db == 'postgres'):
            cursor.execute(
                "UPDATE castle_story AS s SET activity = (SELECT "+
                "sum(l.log_type / (date_part('day', NOW() - l.ctime)+1)) "+
                "FROM castle_storylog AS l "+
                "WHERE l.story_id IS NOT NULL AND s.id=l.story_id "+
                "AND ((date_part('day', NOW() - l.ctime)) < 30) "+
                "AND l.user_id != s.user_id )")

        # Find most active story
        mas = Story.objects.filter(activity__isnull = False).order_by('-activity')[0:1]
        if (mas and (mas[0])):
            # Find 'featured' object in Misc table and update with new most-active story
            ff = Misc.objects.filter(act_type=1)
            if (ff):
                f = ff[0]
            else:
                f = Misc(key='featured', act_type=1)
            
            f.i_val = mas[0].id
            f.act_type = 1
            f.save()
            
            # Record featured story as having been featured
            if (mas[0].ftime is None):
                mas[0].ftime = timezone.now()
                mas[0].save()
                
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
                "AND l.user_id != p.user_id )")
        elif (db == 'postgres'):
            cursor.execute(
                "UPDATE castle_prompt AS p SET activity = (SELECT "+
                "sum(l.log_type / (date_part('day', NOW() - l.ctime)+1)) "+
                "FROM castle_storylog AS l "+
                "WHERE l.prompt_id IS NOT NULL AND p.id=l.prompt_id "+
                "AND ((date_part('day', NOW() - l.ctime)) < 30) "+
                "AND l.user_id != p.user_id )")

        # Find most active challenge
        mapr = Prompt.objects.filter(activity__isnull = False).order_by('-activity')[0:1]
        if (mapr and (mapr[0])):
            # Find 'featured' object in Misc table and update with new most-active challenge
            ff = Misc.objects.filter(act_type=2)
            if (ff):
                f = ff[0]
            else:
                f = Misc(key='featured_prompt', act_type=2)
            
            f.i_val = mapr[0].id
            f.act_type = 2
            f.save()
            
            # Record featured story as having been featured
            if (mapr[0].ftime is None):
                mapr[0].ftime = timezone.now()
                mapr[0].save()
                
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
                "AND l.user_id != c.user_id )")
        elif (db == 'postgres'):
            cursor.execute(
                "UPDATE castle_challenge AS c SET activity = (SELECT "+
                "sum(l.log_type / (date_part('day', NOW() - l.ctime)+1)) "+
                "FROM castle_storylog AS l "+
                "WHERE l.challenge_id IS NOT NULL AND c.id=l.challenge_id "+
                "AND ((date_part('day', NOW() - l.ctime)) < 30) "+
                "AND l.user_id != c.user_id )")

        # Find most active challenge
        mac = Challenge.objects.filter(activity__isnull = False).order_by('-activity')[0:1]
        if (mac and (mac[0])):
            # Find 'featured' object in Misc table and update with new most-active challenge
            ff = Misc.objects.filter(act_type=3)
            if (ff):
                f = ff[0]
            else:
                f = Misc(key='featured_challenge', act_type=3)
            
            f.i_val = mac[0].id
            f.act_type = 3
            f.save()
            
            # Record featured story as having been featured
            if (mac[0].ftime is None):
                mac[0].ftime = timezone.now()
                mac[0].save()

        return None

            
    def handle(self, *args, **options):
        self.do_nightly()
        
