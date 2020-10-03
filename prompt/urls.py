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
    path('', views.prompts, name='prompts'),
    path('<int:prompt_id>/', views.prompt_view, name='prompt'),
    #path('edit/<int:prompt_id>/', views.edit_prompt, name='edit_prompt'),
    path('new/', views.new_prompt, name='new_prompt'),
    path('submit/', views.submit_prompt, name='submit_prompt'),
    path('unsubscribe/<int:prompt_id>/', views.prompt_unsubscribe, name='prompt-unsub'),
    path('subscribe/<int:prompt_id>/', views.prompt_subscribe, name='prompt-sub'),
    path('recent/', views.browse_prompts, name='prompts_recent'),
    path('active/', views.active_prompts, name='prompts_active'),
    path('popular/', views.popular_prompts, name='prompts_popular'),
]
