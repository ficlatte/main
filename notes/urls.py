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
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    url(r'^$', RedirectView.as_view(permanent=True, url='inbox/'), name='notes_redirect'),
    url(r'^inbox/$', views.inbox, name='notes_inbox'),
    url(r'^outbox/$', views.outbox, name='notes_outbox'),
    url(r'^compose/$', views.new_note, name='notes_new'),
    url(r'^compose/submit/$', views.submit_note, name='notes_submit'),
    url(r'^reply/(?P<note_id>[\d]+)/$', views.reply, name='notes_reply'),
    url(r'^forward/(?P<note_id>[\d]+)/$', views.forward, name='notes_forward'),
    url(r'^view/(?P<note_id>[\d]+)/$', views.view, name='notes_detail'),
    url(r'^delete/(?P<note_id>[\d]+)/$', views.delete, name='notes_delete'),
    url(r'^undelete/(?P<note_id>[\d]+)/$', views.undelete, name='notes_undelete'),
    url(r'^trash/$', views.trash, name='notes_trash'),
]
