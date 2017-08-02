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
    url(r'^$', 'prompt.views.prompts', name='prompts'),
    url(r'^(?P<prompt_id>\d+)/$', 'prompt.views.prompt_view', name='prompt'),
    #url(r'^edit/(?P<prompt_id>\d+)/$', 'prompt.views.edit_prompt', name='edit_prompt'),
    url(r'^new/$', 'prompt.views.new_prompt', name='new_prompt'),
    url(r'^submit/$', 'prompt.views.submit_prompt', name='submit_prompt'),
    url(r'^unsubscribe/(?P<prompt_id>\d+)/$', 'prompt.views.prompt_unsubscribe', name='prompt-unsub'),
    url(r'^subscribe/(?P<prompt_id>\d+)/$', 'prompt.views.prompt_subscribe', name='prompt-sub'),
    url(r'^recent/$', 'prompt.views.browse_prompts', name='prompts_recent'),
    url(r'^active/$', 'prompt.views.active_prompts', name='prompts_active'),
    url(r'^popular/$', 'prompt.views.popular_prompts', name='prompts_popular'),
]
