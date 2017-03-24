
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
from models import *

# Register your models here.
admin.site.register(Profile)
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
