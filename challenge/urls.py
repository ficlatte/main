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

from . import views

urlpatterns = [
    url(r'^$', 'challenge.views.challenges', name='challenges'),
    url(r'^recent/$', 'challenge.views.browse_challenges', name='challenges_recent'),
    url(r'^active/$', 'challenge.views.active_challenges', name='challenges_active'),
    url(r'^popular/$', 'challenge.views.popular_challenges', name='challenges_popular'),
    url(r'^(?P<challenge_id>\d+)/$', 'challenge.views.challenge_view', name='challenge'),
    url(r'^(?P<challenge_id>\d+)/winner/(?P<story_id>\d+)/$', 'challenge.views.challenge_winner', name='challenge_winner'),
    #url(r'^edit/(?P<challenge_id>\d+)/$', 'challenge.views.edit_challenge', name='edit_challenge'),
    url(r'^new/$', 'challenge.views.new_challenge', name='new_challenge'),
    url(r'^submit/$', 'challenge.views.submit_challenge', name='submit_challenge'),
    url(r'^unsubscribe/(?P<challenge_id>\d+)/$', 'challenge.views.challenge_unsubscribe', name='challenge-unsub'),
    url(r'^subscribe/(?P<challenge_id>\d+)/$', 'challenge.views.challenge_subscribe', name='challenge-sub'),
    url(r'^entries/unsubscribe/(?P<challenge_id>\d+)/$', 'challenge.views.challenge_entry_unsubscribe', name='challenge-entry-unsub'),
    url(r'^entries/subscribe/(?P<challenge_id>\d+)/$', 'challenge.views.challenge_entry_subscribe', name='challenge-entry-sub'),
]
