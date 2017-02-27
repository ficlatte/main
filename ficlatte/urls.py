
#coding: utf-8
#This file is part of Ficlatté.
#Copyright (C) 2015 Paul Robertson
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

from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic import TemplateView
from django.core.urlresolvers import reverse_lazy
from django.contrib.sitemaps.views import sitemap
from castle.sitemap import *
import django.contrib.auth.views
import castle.views
import castle.models

# Define sitemaps
sitemaps = {
    'blog':	BlogSitemap,
    'stories': StorySitemap,
    'prompts': PromptSitemap,
    'tags': TagSitemap,
    'authors': AuthorSitemap,
    'static': StaticViewSitemap,
}

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'ficlatte.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    
    url(r'^sitemap\.xml$', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'), # Sitemap
    url(r'^notes/', include('notes.urls')), #Notes
    
    #Dynamic Pages
    url(r'^$',      'castle.views.home', name='home'),
    url(r'^login/$', django.contrib.auth.views.login, {'template_name': 'castle/login.html'}, name='login'),
    url(r'^logout/$', castle.views.signout, name='signout'),
#    url(r'^login/$',      TemplateView.as_view(template_name='castle/login.html'), name='signin'),
    url(r'^signin/$',     'castle.views.signin',  name='signin'),       # Process log-in credentials
#    url(r'^logout/$',     'castle.views.signout', name='signout'),
    url(r'^dashboard/$',  'castle.views.dashboard', name='dashboard'),
    url(r'^authors/(?P<pen_name>[^/]+)/$', 'castle.views.author', name='author'),
    url(r'^authors/u/drafts/$', 'castle.views.drafts', name='drafts'),
    url(r'^authors/u/prompts/$', 'castle.views.author_prompts', name='author_prompts'),
    url(r'^authors/u/challenges/$', 'castle.views.author_challenges', name='author_challenges'),
    url(r'^authors/u/profile/$', 'castle.views.profile_view', name='profile'),
    url(r'^authors/u/submit/$', 'castle.views.submit_profile', name='submit_profile'),
    url(r'^register/$', 'castle.views.profile_view', name='register'),
    url(r'^stories/(?P<story_id>\d+)/$', 'castle.views.story_view', name='story'),
    url(r'^stories/edit/(?P<story_id>\d+)/$', 'castle.views.edit_story', name='edit_story'),
    url(r'^stories/delete/(?P<story_id>\d+)/$', 'castle.views.delete_story', name='delete_story'),
    url(r'^stories/new/$', 'castle.views.new_story', name='new_story'),
    url(r'^stories/submit/$', 'castle.views.submit_story', name='submit_story'),
    url(r'^stories/unsubscribe/(?P<story_id>\d+)/$', 'castle.views.story_unsubscribe', name='story-unsub'),
    url(r'^stories/subscribe/(?P<story_id>\d+)/$', 'castle.views.story_subscribe', name='story-sub'),
    url(r'^stories/$', 'castle.views.browse_stories', name='recent_stories'),
    url(r'^stories/active/$', 'castle.views.active_stories', name='active_stories'),
    url(r'^stories/popular/$', 'castle.views.popular_stories', name='popular_stories'),
    url(r'^prompts/$', 'castle.views.prompts', name='prompts'),
    url(r'^prompts/(?P<prompt_id>\d+)/$', 'castle.views.prompt', name='prompt'),
    #url(r'^prompts/edit/(?P<prompt_id>\d+)/$', 'castle.views.edit_prompt', name='edit_prompt'),
    url(r'^prompts/new/$', 'castle.views.new_prompt', name='new_prompt'),
    url(r'^prompts/submit/$', 'castle.views.submit_prompt', name='submit_prompt'),
    url(r'^challenges/$', 'castle.views.challenges', name='challenges'),
    url(r'^challenges/recent/$', 'castle.views.browse_challenges', name='challenges_recent'),
    url(r'^challenges/active/$', 'castle.views.active_challenges', name='challenges_active'),
    url(r'^challenges/popular/$', 'castle.views.popular_challenges', name='challenges_popular'),
    url(r'^challenges/(?P<challenge_id>\d+)/$', 'castle.views.challenge_view', name='challenge'),
    url(r'^challenges/(?P<challenge_id>\d+)/winner/(?P<story_id>\d+)/$', 'castle.views.challenge_winner', name='challenge_winner'),
    #url(r'^challenges/edit/(?P<challenge_id>\d+)/$', 'castle.views.edit_challenge', name='edit_challenge'),
    url(r'^challenges/new/$', 'castle.views.new_challenge', name='new_challenge'),
    url(r'^challenges/submit/$', 'castle.views.submit_challenge', name='submit_challenge'),
    url(r'^blog/$', 'castle.views.blogs', name='blogs'),
    url(r'^blog/(?P<blog_id>\d+)/$', 'castle.views.blog_view', name='blog'),
    url(r'^blog/edit/(?P<blog_id>\d+)/$', 'castle.views.edit_blog', name='edit_blog'),
    url(r'^blog/new/$', 'castle.views.new_blog', name='new_blog'),
    url(r'^blog/submit/$', 'castle.views.submit_blog', name='submit_blog'),
    url(r'^blog/unsubscribe/(?P<blog_id>\d+)/$', 'castle.views.blog_unsubscribe', name='blog-unsub'),
    url(r'^comment/submit/$', 'castle.views.submit_comment', name='submit_comment'),
    url(r'^tags/(?P<tag_name>[^/]+)/$', 'castle.views.tags', name='tags'),
    url(r'^tags/$', 'castle.views.tags_null', name='tags_null'),
    url(r'^friendship/add/(?P<user_id>\d+)/$', 'castle.views.add_friend', name='add_friend'),
    url(r'^friendship/del/(?P<user_id>\d+)/$', 'castle.views.del_friend', name='del_friend'),    
    url(r'^admin/', include(admin.site.urls)),
    url(r'^confirmation/(?P<yesno>(?:yes|no))/(?P<uid>\d+)/(?P<token>\d+)/$', 'castle.views.confirmation', name='confirmation'),
    url(r'^avatar_upload/', 'castle.views.avatar_upload', name='avatar_upload'),
    url(r'^resend_email_conf/$', 'castle.views.resend_email_conf', name='resend_email_conf'),
    url(r'^password_reset/$', django.contrib.auth.views.password_reset, {'post_reset_redirect': reverse_lazy('password_reset_done'), 'html_email_template_name': 'castle/registration/password_reset_email.html', 'template_name': 'castle/registration/password_reset_form.html'}, name='password_reset'),
    url(r'^password_reset/done/$', django.contrib.auth.views.password_reset_done, {'template_name': 'castle/registration/password_reset_done.html'}, name='password_reset_done'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', django.contrib.auth.views.password_reset_confirm, {'template_name': 'castle/registration/password_reset_confirm.html'}, name='password_reset_confirm'),
    url(r'^reset/done/$', django.contrib.auth.views.password_reset_complete, {'template_name': 'castle/registration/password_reset_complete.html'}, name='password_reset_complete'),
    
    # Static-ish pages
    #url(r'^(?P<template>rules\.html)$', 'castle.views.static_view', name="rules"),
    #url(r'^(?P<template>privacy\.html)$', 'castle.views.static_view', name="privacy"),
    #url(r'^(?P<template>help\.html)$', 'castle.views.static_view', name="help"),
    url(r'^rules/$', 'castle.views.static_view', {'template_name': 'rules.html'}, name="rules"),
    url(r'^privacy/$', 'castle.views.static_view', {'template_name': 'privacy.html'}, name="privacy"),
    url(r'^help/$', 'castle.views.static_view', {'template_name': 'help.html'}, name="help"),
)
