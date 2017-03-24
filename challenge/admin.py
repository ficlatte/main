from django.contrib import admin
from castle.models import Challenge
from castle.admin import CommentInLine

# Register your models here.

class ChallengeAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields' : ['user', 'title', 'body']}),
        ('Bits', {'fields': ['mature', 'activity'], 'classes': ['collapse']}),
        ('Dates', {'fields': ['ctime', 'mtime', 'stime', 'etime'], 'classes': ['collapse']}),
    ]
    inlines = [CommentInLine]
    
admin.site.register(Challenge, ChallengeAdmin)
