
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
    path('<int:story_id>/', views.story_view, name='story'),
    path('edit/<int:story_id>/', views.edit_story, name='edit_story'),
    path('delete/<int:story_id>/', views.delete_story, name='delete_story'),
    path('new/', views.new_story, name='new_story'),
    path('submit/', views.submit_story, name='submit_story'),
    path('unsubscribe/<int:story_id>/', views.story_unsubscribe, name='story-unsub'),
    path('subscribe/<int:story_id>/', views.story_subscribe, name='story-sub'),
    path('prequels/unsubscribe/<int:story_id>/', views.prequel_unsubscribe, name='prequel-unsub'),
    path('prequels/subscribe/<int:story_id>/', views.prequel_subscribe, name='prequel-sub'),
    path('sequels/unsubscribe/<int:story_id>/', views.sequel_unsubscribe, name='sequel-unsub'),
    path('sequels/subscribe/<int:story_id>/', views.sequel_subscribe, name='sequel-sub'),
    path('', views.browse_stories, name='recent_stories'),
    path('active/', views.active_stories, name='active_stories'),
    path('popular/', views.popular_stories, name='popular_stories'),
]
