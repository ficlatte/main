
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
