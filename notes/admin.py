from django.contrib import admin
from notes.models import Note

# Register your models here.

class NoteAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields' : ['user', 'subject', 'body', 'sender', 'recipient']}),
        ('Bits', {'fields': ['parent_msg'], 'classes': ['collapse']}),
        ('Dates', {'fields': ['sent_date', 'read_date', 'replied_date', 'sender_deleted_date', 'recipient_deleted_date'], 'classes': ['collapse']}),
    ]

admin.site.register(Note, NoteAdmin)
