
#coding: utf-8
#This file is part of Ficlatté.
#Copyright (C) 2015-2017 Paul Robertson, Jim Stitzel, & Shu Sam Chen
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
    url(r'^directory/', views.member_directory, name='member_directory'),
    url(r'^(?P<pen_name>[^/]+)/', views.author, name='author'),
    url(r'^u/drafts/', views.drafts, name='drafts'),
    url(r'^u/prompts/', views.author_prompts, name='author_prompts'),
    url(r'^u/challenges/', views.author_challenges, name='author_challenges'),
    url(r'^u/profile/', views.profile_view, name='profile'),
    url(r'^u/submit/', views.submit_profile, name='submit_profile'),
]
