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

from django.urls import path

from . import views

urlpatterns = [
    path('', views.challenges, name='challenges'),
    path('recent/', views.browse_challenges, name='challenges_recent'),
    path('active/', views.active_challenges, name='challenges_active'),
    path('popular/', views.popular_challenges, name='challenges_popular'),
    path('<int:challenge_id>/', views.challenge_view, name='challenge'),
    path('<int:challenge_id>/winner/<int:story_id>/', views.challenge_winner, name='challenge_winner'),
    #path('edit/<int:challenge_id>/', views.edit_challenge, name='edit_challenge'),
    path('new/', views.new_challenge, name='new_challenge'),
    path('submit/', views.submit_challenge, name='submit_challenge'),
    path('unsubscribe/<int:challenge_id>/', views.challenge_unsubscribe, name='challenge-unsub'),
    path('subscribe/<int:challenge_id>/', views.challenge_subscribe, name='challenge-sub'),
    path('entries/unsubscribe/<int:challenge_id>/', views.challenge_entry_unsubscribe, name='challenge-entry-unsub'),
    path('entries/subscribe/<int:challenge_id>/', views.challenge_entry_subscribe, name='challenge-entry-sub'),
]
