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

from django.contrib.sitemaps import Sitemap
from django.core.urlresolvers import reverse
from castle.models import *

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
        
class ChallengeSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.4
    protocol = "https"
    
    def items(self):
        return Challenge.objects.all()
        
    def lastmod(self, obj):
        return obj.mtime
        
    def location(self, obj): 
        return u'/challenges/'+str(obj.id)
        
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
