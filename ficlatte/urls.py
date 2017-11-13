
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

import django.contrib.auth.views
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.core.urlresolvers import reverse_lazy

import castle.models
from castle.sitemap import *

# Define sitemaps
sitemaps = {
    'blog':	BlogSitemap,
    'stories': StorySitemap,
    'prompts': PromptSitemap,
    'challenges': ChallengeSitemap,
    'tags': TagSitemap,
    'authors': AuthorSitemap,
    'static': StaticViewSitemap,
}

urlpatterns = patterns('',
	# Admin
    url(r'^admin/', include(admin.site.urls)),

	# Apps
    url(r'^sitemap\.xml$', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'), # Sitemap
    url(r'^blog/', include('blog.urls')), # Blog
    url(r'^authors/', include('author.urls')), # Authors
    url(r'^stories/', include('story.urls')), # Stories
    url(r'^prompts/', include('prompt.urls')), # Prompts
    url(r'^challenges/', include('challenge.urls')), # Challenges
    url(r'^comment/', include('comment.urls')), # Comments
    url(r'^notes/', include('notes.urls')), # Notes
    
    # Registration and Authentication
    url(r'^$', 'story.views.home', name='home'),
    url(r'^login/$', django.contrib.auth.views.login, {'template_name': 'castle/login.html'}, name='login'),
    url(r'^logout/$', castle.views.signout, name='signout'),
    url(r'^signin/$',     'castle.views.signin',  name='signin'),       # Process log-in credentials
    url(r'^register/$', 'author.views.profile_view', name='register'),
    url(r'^confirmation/(?P<yesno>(?:yes|no))/(?P<uid>\d+)/(?P<token>\d+)/$', 'castle.views.confirmation', name='confirmation'),
    url(r'^resend_email_conf/$', 'castle.views.resend_email_conf', name='resend_email_conf'),
    url(r'^password_reset/$', django.contrib.auth.views.password_reset, {'post_reset_redirect': reverse_lazy('password_reset_done'), 'html_email_template_name': 'castle/registration/password_reset_email.html', 'template_name': 'castle/registration/password_reset_form.html'}, name='password_reset'),
    url(r'^password_reset/done/$', django.contrib.auth.views.password_reset_done, {'template_name': 'castle/registration/password_reset_done.html'}, name='password_reset_done'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', django.contrib.auth.views.password_reset_confirm, {'template_name': 'castle/registration/password_reset_confirm.html'}, name='password_reset_confirm'),
    url(r'^reset/done/$', django.contrib.auth.views.password_reset_complete, {'template_name': 'castle/registration/password_reset_complete.html'}, name='password_reset_complete'),
    
    # User Dashboard
    url(r'^dashboard/$',  'castle.views.dashboard', name='dashboard'),
    url(r'^friendship/add/(?P<user_id>\d+)/$', 'castle.views.add_friend', name='add_friend'),
    url(r'^friendship/del/(?P<user_id>\d+)/$', 'castle.views.del_friend', name='del_friend'), 
    url(r'^avatar_upload/', 'castle.views.avatar_upload', name='avatar_upload'),

	# Miscellaneous Story
    url(r'^tag/(?P<tag_name>[^/]+)/$', 'story.views.tags', name='tags'),
    url(r'^tags/$', 'story.views.tags_null', name='tags_null'),    
    
    # Static-ish pages
    url(r'^about/$', 'castle.views.static_view', {'template_name': 'about.html'}, name="about"),
    url(r'^rules/$', 'castle.views.static_view', {'template_name': 'rules.html'}, name="rules"),
    url(r'^privacy/$', 'castle.views.static_view', {'template_name': 'privacy.html'}, name="privacy"),
    url(r'^help/$', 'castle.views.static_view', {'template_name': 'help.html'}, name="help"),
    #url(r'^credits/$', 'castle.views.static_view', {'template_name': 'credits.html'}, name="credits"),
)
