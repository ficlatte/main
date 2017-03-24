from django.contrib import admin
from castle.models import Story
from castle.admin import CommentInLine, RatingInLine

# Register your models here.
class StoryAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields' : ['user', 'title', 'body', 'prompt_text']}),
        ('Links', {'fields': ['prequel_to', 'sequel_to', 'prompt'], 'classes': ['collapse']}),
        ('Bits', {'fields': ['mature', 'draft', 'ficly', 'activity', 'prompt_text'], 'classes': ['collapse']}),
        ('Dates', {'fields': ['ctime', 'mtime', 'ptime', 'ftime'], 'classes': ['collapse']}),
    ]
    inlines = [CommentInLine, RatingInLine]

admin.site.register(Story, StoryAdmin)