from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.conf import settings
from .models import *

def send_note_email(note):
	url = getattr(settings, 'SITE_URL', 'http://www.example.com/')
	
	# Lookup user ID of recipient
	recipient_obj = Profile.objects.get(pk = note.recipient_id)
	recipient_email = recipient_obj.email_addr
    
	mail_message  = u"Hi.\nThis is the Ficlatte server. " + note.sender.pen_name + u" has sent\n";
	mail_message += u"you a note. You may view the message in your inbox:\n";
	mail_message += u"{}{}".format(url, reverse('notes_inbox')) + u"\n\n";
	mail_message += u"Best regards,\n\n";
	mail_message += u"The Ficlatte team\n";
    
	send_mail(u'Ficlatte note from ' + note.sender.pen_name,
				mail_message,
				'Ficlatte Team <noreply@ficlatte.com>',
				[recipient_email],
				fail_silently = False)
