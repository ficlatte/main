from django.core.management.base import BaseCommand, CommandError
from castle.models import *
from django.db import transaction
import MySQLdb
import binascii

class Command(BaseCommand):
    help = 'Import old Ficlatte database into Django database'
    args =''
    
    @transaction.atomic
    def import_users(self):
        c = self.db.cursor()
        c.execute('SELECT uid, pen_name, site_url, site_name, biography, mature, email_addr, auth, salt, ctime, flags, prefs FROM user WHERE uid != 1 AND email_auth = 0');
        while (1):
            row = c.fetchone()
            if (not row):
                break;
            
            salt = "{:16x}".format(row[8])
            auth = binascii.hexlify(row[7])
            
            profile = Profile(
                id = row[0],
                pen_name = row[1],
                pen_name_uc = row[1].upper(),
                site_url = row[2],
                site_name = row[3],
                biography = row[4],
                mature = (not (not row[5])),
                email_addr = row[6],
                old_auth = auth,
                old_salt = salt,
                ctime = row[9],
                flags = row[10],
                prefs = row[11],
            )
            
            if (row[0] != 1):
                user = User(
                    id = row[0],
                    username = 'user'+str(row[0]),
                    first_name = 'user',
                    last_name = str(row[0]),
                    email = row[6],
                    date_joined = row[9],
                )
                user.save()
            else:
                user=User.objects.get(pk=1)

            profile.user=user
            profile.save()

            self.stdout.write('uid '+str(row[0])+ ' is '+row[1]+' Django uid is '+str(user.id))

    @transaction.atomic
    def import_friendships(self):
        c = self.db.cursor()
        c.execute('SELECT uid, fuid FROM friendship');
        while (1):
            row = c.fetchone()
            if (not row):
                break;
            self.stdout.write(str(row[0])+' is following '+str(row[1]))
            prof = Profile.objects.get(pk=int(row[0]))
            prof.friends.add(Profile.objects.get(pk=row[1]))
            prof.save()
    
    def handle(self, *args, **options):
        self.db = MySQLdb.connect(db='ficlatte',passwd='MQvbCW9FFU6X3HVD',user='ficlatte')
        
        self.import_users()
        self.import_friendships()
        
        self.stdout.write('Balls')
        