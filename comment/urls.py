from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^submit/$', 'comment.views.submit_comment', name='submit_comment'),
    url(r'^(?P<comment_id>\d+)/like/$', 'comment.views.like_comment', name='like_comment'),
    url(r'^(?P<comment_id>\d+)/unlike/$', 'comment.views.unlike_comment', name='unlike_comment'),
]
