from django.contrib import admin
from castle.models import Blog
from castle.admin import CommentInLine

# Register your models here.
class BlogAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields' : ['user', 'title', 'body']}),
        ('Bits', {'fields': ['draft'], 'classes': ['collapse']}),
        ('Dates', {'fields': ['ctime', 'mtime', 'ptime'], 'classes': ['collapse']}),
    ]
    inlines = [CommentInLine]

admin.site.register(Blog,  BlogAdmin)