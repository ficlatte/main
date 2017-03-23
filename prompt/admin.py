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