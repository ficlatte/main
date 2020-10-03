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
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path('', RedirectView.as_view(permanent=True, url='inbox/'), name='notes_redirect'),
    path('inbox/', views.inbox, name='notes_inbox'),
    path('outbox/', views.outbox, name='notes_outbox'),
    path('compose/', views.new_note, name='notes_new'),
    path('compose/submit/', views.submit_note, name='notes_submit'),
    path('reply/<int:note_id>/', views.reply, name='notes_reply'),
    path('forward/<int:note_id>/', views.forward, name='notes_forward'),
    path('view/<int:note_id>/', views.view, name='notes_detail'),
    path('delete/<int:note_id>/', views.delete, name='notes_delete'),
    path('undelete/<int:note_id>/', views.undelete, name='notes_undelete'),
    path('trash/', views.trash, name='notes_trash'),
]
