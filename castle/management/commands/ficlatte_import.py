from django.core.management.base import BaseCommand, CommandError
from castle.models import *
from django.db import transaction
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
import MySQLdb
import binascii

class Command(BaseCommand):
    help = 'Import old Ficlatte database into Django database'
    args =''
    
    @transaction.atomic
    def import_users(self):
        c = self.db.cursor()
        c.execute('SELECT uid, pen_name, site_url, site_name, biography, mature, email_addr, auth, salt, ctime, flags, prefs FROM user WHERE uid > 0 AND email_auth = 0');
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
                    username = 'user'+unicode(row[0]),
                    first_name = 'user',
                    last_name = unicode(row[0]),
                    email = row[6],
                    date_joined = row[9],
                )
                user.save()
            else:
                user=User.objects.get(pk=1)

            profile.user=user
            profile.save()

            self.stdout.write(u'uid '+unicode(row[0])+ u' is '+row[1]+u' Django uid is '+unicode(user.id))

    @transaction.atomic
    def import_friendships(self):
        c = self.db.cursor()
        c.execute('SELECT uid, fuid FROM friendship');
        while (1):
            row = c.fetchone()
            if (not row):
                break;
            self.stdout.write(unicode(row[0])+u' is following '+unicode(row[1]))
            prof = Profile.objects.get(pk=int(row[0]))
            prof.friends.add(Profile.objects.get(pk=row[1]))
            prof.save()
    
    @transaction.atomic
    def import_prompts(self):
        c = self.db.cursor()
        c.execute('SELECT prid, uid, title, body, mature, ctime, mtime FROM prompts');
        while (1):
            row = c.fetchone()
            if (not row):
                break;
            self.stdout.write(u'Prompt '+unicode(row[0]))
            prompt = Prompt(
                id = row[0],
                user = Profile.objects.get(pk=row[1]),
                title = row[2],
                body = row[3],
                mature = row[4],
                ctime = row[5],
                mtime = row[6],
            )
            prompt.save()
            
    @transaction.atomic
    def import_stories(self):
        c = self.db.cursor()
        c.execute('SELECT sid, uid, title, body, mature, draft, ctime, ftime, ptime, mtime, prequel_to, sequel_to, prid FROM stories');
        while (1):
            row = c.fetchone()
            if (not row):
                break;
            self.stdout.write(u'Story '+unicode(row[0]))#+u': '+unicode(row[2]))
            story = Story(
                id = row[0],
                user = Profile.objects.get(pk=row[1]),
                title = row[2],
                body = row[3],
                mature = not (not row[4]),
                draft = not (not row[5]),
                ctime = row[6],
                ftime = row[7],
                ptime = row[8],
                mtime = row[9],
            )
            story.save()
                
    @transaction.atomic
    def import_story_links(self):
        c = self.db.cursor()
        c.execute('SELECT sid, prequel_to, sequel_to, prid FROM stories');
        while (1):
            row = c.fetchone()
            if (not row):
                break;
            self.stdout.write(u'Story '+unicode(row[0])+u': '+unicode(row[2]))
            story = Story.objects.get(pk=row[0])
            try:
                if (row[1]):
                    story.prequel_to = Story.objects.get(pk=row[1])
                if (row[2]):
                    story.sequel_to = Story.objects.get(pk=row[2])
                if (row[3]):
                    story.prompt = Prompt.objects.get(pk=row[3])
                story.save()
            except ObjectDoesNotExist:
                self.stdout.write("Link to deleted story")
                
    @transaction.atomic
    def import_blog(self):
        c = self.db.cursor()
        c.execute('SELECT bid, uid, title, body, draft, ctime FROM blog');
        while (1):
            row = c.fetchone()
            if (not row):
                break;
            self.stdout.write(u'Blog '+unicode(row[0]))
            profile = Profile.objects.get(pk=row[1])
            blog = Blog(
                    id = row[0],
                    user = profile,
                    title = row[2],
                    body = row[3],
                    draft = not (not row[4]),
                    ctime = row[5],
                    mtime = row[5],
                    ptime = row[5],
                    )
            blog.save()

    @transaction.atomic
    def import_comments(self):
        c = self.db.cursor()
        c.execute('SELECT cid, uid, sid, bid, body, ctime FROM comments');
        while (1):
            row = c.fetchone()
            if (not row):
                break;
            self.stdout.write(u'Comment '+unicode(row[0]))
            profile = Profile.objects.get(pk=row[1])
            comment = Comment(
                    id = row[0],
                    user = profile,
                    body = row[4],
                    ctime = row[5]
                    )
            if (row[2]):
                comment.story = Story.objects.get(pk=row[2])
            if (row[3]):
                comment.blog = Blog.objects.get(pk=row[3])
            comment.save()

    @transaction.atomic
    def import_tags(self):
        c = self.db.cursor()
        c.execute('SELECT tag, sid FROM tags');
        while (1):
            row = c.fetchone()
            if (not row):
                break;
            self.stdout.write(u'Tag '+unicode(row[0])+u' on '+unicode(row[1]))
            story = Story.objects.get(pk=row[1])
            tag = Tag(
                tag = row[0],
                story = story,
                )
        tag.save()
    
    @transaction.atomic
    def import_ratings(self):
        c = self.db.cursor()
        c.execute('SELECT uid, sid, rating FROM ratings');
        while (1):
            row = c.fetchone()
            if (not row):
                break;
            self.stdout.write(u'Rating from '+unicode(row[0]))
            try:
                r = Rating(
                    user  = Profile.objects.get(pk=row[0]),
                    story = Story.objects.get(pk=row[1]),
                    rating = row[2],
                    )
                r.save()
            except ObjectDoesNotExist:
                self.stdout.write("Rating of non-existant story "+unicode(row[1]))

    @transaction.atomic
    def import_story_log(self):
        c = self.db.cursor()
        c.execute('SELECT uid, sid, type, mid, time FROM story_log');
        #c.execute('SELECT uid, sid, type, mid, time FROM story_log where type!=1');
        while (1):
            row = c.fetchone()
            if (not row):
                break;
            self.stdout.write(u'Story log user '+unicode(row[0])+u'; story='+unicode(row[1])+u'; type='+unicode(row[2]))
            try:
                l = StoryLog(
                    user  = Profile.objects.get(pk=row[0]),
                    log_type = row[2],
                    ctime = row[4],
                    )
                if (row[1]):
                    l.story = Story.objects.get(pk=row[1])
                if ((row[2] == 4) or (row[2] == 5)):
                    l.quel = Story.objects.get(pk=row[3])
                elif ((row[2] == 8) or (row[2] == 9)):
                    l.prompt = Prompt.objects.get(pk=row[3])
                l.save()
            except ObjectDoesNotExist:
                self.stdout.write("Story log with non-exitant link")

    @transaction.atomic
    def import_misc(self):
        c = self.db.cursor()
        c.execute('SELECT k, s, i FROM misc');
        while (1):
            row = c.fetchone()
            if (not row):
                break;
            self.stdout.write(u'misc '+row[0])
            m = Misc(
                key = row[0],
                s_val = row[1],
                i_val = row[2],
                )
            m.save()

            
    def handle(self, *args, **options):
        odb = getattr(settings, 'OLDDB_DB', 'ficlatte')
        odu = getattr(settings, 'OLDDB_USER', 'ficlatte')
        odp = getattr(settings, 'OLDDB_PASSWORD', '')

        self.db = MySQLdb.connect(db=odb,passwd=odp,user=odu)
        
        self.import_users()
        self.import_friendships()
        self.import_prompts()
        self.import_stories()
        self.import_story_links()
        self.import_blog()
        self.import_comments()
        self.import_tags()
        self.import_ratings()
        self.import_story_log()
        self.import_misc()
        
        self.stdout.write(u'Balls')
        