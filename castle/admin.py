
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

from django.contrib import admin
from models import *

# Register your models here.
admin.site.register(Profile)
admin.site.register(Prompt)
#admin.site.register(Story)
admin.site.register(Tag)
#admin.site.register(Blog)
#admin.site.register(Rating)
admin.site.register(Comment)
admin.site.register(StoryLog)
admin.site.register(SiteLog)
admin.site.register(Misc)
admin.site.register(Subscription)

class RatingInLine(admin.TabularInline):
    model = Rating
    fieldsets = [
        (None, {'fields': ['user', 'rating']}),
    ]
    extra = 0

class CommentInLine(admin.TabularInline):
    model = Comment
    fieldsets = [
        (None, {'fields': ['user', 'body']}),
    ]
    extra = 0

class StoryAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields' : ['user', 'title', 'body', 'prompt_text']}),
        ('Links', {'fields': ['prequel_to', 'sequel_to', 'prompt'], 'classes': ['collapse']}),
        ('Bits', {'fields': ['mature', 'draft', 'ficly', 'activity', 'prompt_text'], 'classes': ['collapse']}),
        ('Dates', {'fields': ['ctime', 'mtime', 'ptime', 'ftime'], 'classes': ['collapse']}),
    ]
    inlines = [CommentInLine, RatingInLine]
    
class ChallengeAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields' : ['user', 'title', 'body']}),
        ('Bits', {'fields': ['mature', 'activity'], 'classes': ['collapse']}),
        ('Dates', {'fields': ['ctime', 'mtime', 'stime', 'etime'], 'classes': ['collapse']}),
    ]
    inlines = [CommentInLine]

class BlogAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields' : ['user', 'title', 'body']}),
        ('Bits', {'fields': ['draft'], 'classes': ['collapse']}),
        ('Dates', {'fields': ['ctime', 'mtime', 'ptime'], 'classes': ['collapse']}),
    ]
    inlines = [CommentInLine]

admin.site.register(Story, StoryAdmin)
admin.site.register(Challenge, ChallengeAdmin)  
admin.site.register(Blog,  BlogAdmin)
