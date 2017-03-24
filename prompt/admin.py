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
from castle.models import Prompt
from castle.admin import CommentInLine


# Register your models here.

class PromptAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['user', 'title', 'body']}),
        ('Bits', {'fields': ['mature', 'activity'], 'classes': ['collapse']}),
        ('Dates', {'fields': ['ctime', 'mtime', 'stime', 'etime'], 'classes': ['collapse']}),
    ]
    inlines = [CommentInLine]


admin.site.register(Prompt, PromptAdmin)