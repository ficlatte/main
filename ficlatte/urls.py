
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

from django.urls import include, path, re_path, reverse, reverse_lazy
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
#from django.core.urlresolvers import reverse_lazy
from django.contrib.auth import views as auth_views

import castle.models
from castle.sitemap import *
import story
import castle
import author

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

urlpatterns = [
	# Admin
    path('admin/', admin.site.urls),

	# Apps
    path('sitemap\.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'), # Sitemap
    path('blog/', include('blog.urls')), # Blog
    path('authors/', include('author.urls')), # Authors
    path('stories/', include('story.urls')), # Stories
    path('prompts/', include('prompt.urls')), # Prompts
    path('challenges/', include('challenge.urls')), # Challenges
    path('comment/', include('comment.urls')), # Comments
    path('notes/', include('notes.urls')), # Notes
    path('the_pit/', include('the_pit.urls')), # Spambot purgatory
    
    # Registration and Authentication
    path('', story.views.home, name='home'),

    #FIXME: fix log in/out
    #path('login/', django.contrib.auth.views.login, {'template_name': 'castle/login.html'}, name='login'),
    #path('logout/', castle.views.signout, name='signout'),
    path('login/',  auth_views.LoginView.as_view (template_name='castle/login.html'),  name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    path('signin/',     castle.views.signin,  name='signin'),       # Process log-in credentials
    path('register/', author.views.profile_view, name='register'),
    re_path(r'^confirmation/(?P<yesno>(?:yes|no))/(?P<uid>\d+)/(?P<token>\d+)/$', castle.views.confirmation, name='confirmation'),
    path('resend_email_conf/', castle.views.resend_email_conf, name='resend_email_conf'),
    
    path('password_reset/', story.views.home, name='password_reset'),
    
    #path('password_reset/', django.contrib.auth.views.password_reset, {'post_reset_redirect': reverse_lazy('password_reset_done'), 'html_email_template_name': 'castle/registration/password_reset_email.html', 'template_name': 'castle/registration/password_reset_form.html'}, name='password_reset'),
    #path('password_reset/done/', django.contrib.auth.views.password_reset_done, {'template_name': 'castle/registration/password_reset_done.html'}, name='password_reset_done'),
    #path('reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/', django.contrib.auth.views.password_reset_confirm, {'template_name': 'castle/registration/password_reset_confirm.html'}, name='password_reset_confirm'),
    #path('reset/done/', django.contrib.auth.views.password_reset_complete, {'template_name': 'castle/registration/password_reset_complete.html'}, name='password_reset_complete'),
    
    # User Dashboard
    path('dashboard/',  castle.views.dashboard, name='dashboard'),
    path('friendship/add/<int:user_id>/', castle.views.add_friend, name='add_friend'),
    path('friendship/del/<int:user_id>/', castle.views.del_friend, name='del_friend'), 
    path('avatar_upload/', castle.views.avatar_upload, name='avatar_upload'),

	# Miscellaneous Story
    path('tag/<str:tag_name>/', story.views.tags, name='tags'),
    path('tags/', story.views.tags_null, name='tags_null'),    
    
    # Static-ish pages
    path('about/',castle.views.static_view, {'template_name': 'about.html'}, name="about"),
    path('rules/', castle.views.static_view, {'template_name': 'rules.html'}, name="rules"),
    path('privacy/', castle.views.static_view, {'template_name': 'privacy.html'}, name="privacy"),
    path('help/', castle.views.static_view, {'template_name': 'help.html'}, name="help"),
    #path('credits/$', castle.views.static_view, {'template_name': 'credits.html'}, name="credits"),
]
