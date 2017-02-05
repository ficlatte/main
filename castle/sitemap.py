from django.contrib.sitemaps import Sitemap
from django.core.urlresolvers import reverse
from castle.models import Blog, Story, Prompt, Tag, Profile

class StorySitemap(Sitemap):
    changefreq = "always"
    priority = 1.0
    protocol = "https"
        
    def items(self):
        return Story.objects.all()
        
    def lastmod(self, obj):
        return obj.mtime
        
    def location(self, obj): 
        return u'/stories/'+str(obj.id)

class BlogSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.7
    protocol = "https"
    
    def items(self):
        return Blog.objects.all()
        
    def lastmod(self, obj):
        return obj.mtime
        
    def location(self, obj): 
        return u'/blog/'+str(obj.id )
        
class AuthorSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.5
    protocol = "https"
        
    def items(self):
        return Profile.objects.all()
        
    def lastmod(self, obj):
        return obj.mtime
        
    def location(self, obj): 
        return u'/authors/'+obj.pen_name
        
class PromptSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.4
    protocol = "https"
    
    def items(self):
        return Prompt.objects.all()
        
    def lastmod(self, obj):
        return obj.mtime
        
    def location(self, obj): 
        return u'/prompts/'+str(obj.id)
        
class TagSitemap(Sitemap):
    changefreq = "always"
    priority = 0.2
    protocol = "https"
    
    def items(self):
        return Tag.objects.all()
        
    def location(self, obj): 
        return u'/tags/'+obj.tag

class StaticViewSitemap(Sitemap):
    priority = 1.0
    changefreq = 'always'
    protocol = "https"

    def items(self):
        return ['home', 'rules', 'privacy', 'help']

    def location(self, item):
        return reverse(item)
