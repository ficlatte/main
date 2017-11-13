
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

from django.conf.urls import url

urlpatterns = [
    url(r'^(?P<story_id>\d+)/$', 'story.views.story_view', name='story'),
    url(r'^edit/(?P<story_id>\d+)/$', 'story.views.edit_story', name='edit_story'),
    url(r'^delete/(?P<story_id>\d+)/$', 'story.views.delete_story', name='delete_story'),
    url(r'^new/$', 'story.views.new_story', name='new_story'),
    url(r'^submit/$', 'story.views.submit_story', name='submit_story'),
    url(r'^unsubscribe/(?P<story_id>\d+)/$', 'story.views.story_unsubscribe', name='story-unsub'),
    url(r'^subscribe/(?P<story_id>\d+)/$', 'story.views.story_subscribe', name='story-sub'),
    url(r'^prequels/unsubscribe/(?P<story_id>\d+)/$', 'story.views.prequel_unsubscribe', name='prequel-unsub'),
    url(r'^prequels/subscribe/(?P<story_id>\d+)/$', 'story.views.prequel_subscribe', name='prequel-sub'),
    url(r'^sequels/unsubscribe/(?P<story_id>\d+)/$', 'story.views.sequel_unsubscribe', name='sequel-unsub'),
    url(r'^sequels/subscribe/(?P<story_id>\d+)/$', 'story.views.sequel_subscribe', name='sequel-sub'),
    url(r'^$', 'story.views.browse_stories', name='recent_stories'),
    url(r'^active/$', 'story.views.active_stories', name='active_stories'),
    url(r'^popular/$', 'story.views.popular_stories', name='popular_stories'),
]
