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
