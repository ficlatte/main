from django.core.management.base import BaseCommand, CommandError
from castle.models import *
from django.db import transaction, connection
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

class Command(BaseCommand):
    help = 'Import old Ficlatte database into Django database'
    args =''
    
    @transaction.atomic
    def do_nightly(self):
        db = getattr(settings, 'DB', 'mysql')

        # Zero out all activity values
        Story.objects.all().update(activity=0)
        
        cursor = connection.cursor()
        
        if (db == 'mysql'):
            cursor.execute(
                "UPDATE castle_story AS s SET activity = (SELECT "+
                "sum(l.log_type / (timestampdiff(day,l.time,now())+1)) "+
                "FROM castle_storylog AS l "+
                "WHERE s.sid=l.sid "+
                "AND ((timestampdiff(day,l.time,now())) < 30) "+
                "AND l.uid != l.tuid )")
        elif (db == 'postgres'):
            cursor.execute(
                "UPDATE castle_story AS s SET activity = (SELECT "+
                "sum(l.log_type / (date_part('day', NOW() - l.ctime)+1)) "+
                "FROM castle_storylog AS l "+
                "WHERE l.story_id IS NOT NULL AND s.id=l.story_id "+
                "AND ((date_part('day', NOW() - l.ctime)) < 30) "+
                "AND l.user_id != s.user_id )")

#    my $sth0 = $dbh->prepare("UPDATE $story_table SET activity = 0");
#    my $sth1 = $dbh->prepare("UPDATE $story_table AS s SET activity = (SELECT ".
#        "sum(l.type / (timestampdiff(day,l.time,now())+1)) ".
#        "FROM $log_table AS l ".
#        "WHERE s.sid=l.sid ".
#        "AND ((timestampdiff(day,l.time,now())) < 30) ".
#        "AND l.uid != l.tuid )");

        return None

            
    def handle(self, *args, **options):
        self.do_nightly()
        