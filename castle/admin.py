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
        (None, {'fields' : ['user', 'title', 'body']}),
        ('Links', {'fields': ['prequel_to', 'sequel_to', 'prompt'], 'classes': ['collapse']}),
        ('Bits', {'fields': ['mature', 'draft', 'ficly', 'activity', 'prompt_text'], 'classes': ['collapse']}),
        ('Dates', {'fields': ['ctime', 'mtime', 'ptime', 'ftime'], 'classes': ['collapse']}),
    ]
    inlines = [CommentInLine, RatingInLine]

class BlogAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields' : ['user', 'title', 'body']}),
        ('Bits', {'fields': ['draft'], 'classes': ['collapse']}),
        ('Dates', {'fields': ['ctime', 'mtime'], 'classes': ['collapse']}),
    ]
    inlines = [CommentInLine]

admin.site.register(Story, StoryAdmin)
admin.site.register(Blog,  BlogAdmin)
