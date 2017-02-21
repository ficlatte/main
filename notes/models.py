from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, date
from castle.models import *


class NoteManager(models.Manager):
	
	def inbox_for(self, user):
		return self.filter(recipient = user, recipient_deleted_date__isnull=True)
	
	def outbox_for(self, user):
		return self.filter(sender = user, sender_deleted_date__isnull=True)
	
	def trash_for(self, user):
		return self.filter(recipient = user, recipient_deleted_date__isnull=False) | self.filter(sender = user, sender_deleted_date__isnull=False)

	def inbox_count_for(self, user):
		return self.filter(recipient = user, read_date__isnull=True, recipient_deleted_date__isnull=True).count()	

class Note(models.Model):
	user					= models.ForeignKey(Profile)
	subject 	 			= models.CharField(max_length=140)
	body		 			= models.CharField(max_length=2048)
	sender		 			= models.ForeignKey(Profile, related_name='sender')
	recipient	 			= models.ForeignKey(Profile, related_name='recipient')
	parent_msg	 			= models.ForeignKey('self', related_name='parent', blank=True, null=True)
	sent_date	 			= models.DateTimeField(blank=True, null=True)
	read_date				= models.DateTimeField(blank=True, null=True)
	replied_date 			= models.DateTimeField(blank=True, null=True)
	sender_deleted_date 	= models.DateTimeField(blank=True, null=True)
	recipient_deleted_date 	= models.DateTimeField(blank=True, null=True)
	
	objects = NoteManager()
	
	def new(self):
		if self.read_date is not None:
			return False
		else:
			return True
	
	def replied(self):
		if self.replied_date is not None:
			return False
		else:
			return True
	
	def __unicode__(self):
		return unicode(self.subject)
	
	class Meta:
		ordering = ['-sent_date']
