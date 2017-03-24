from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^submit/$', 'comment.views.submit_comment', name='submit_comment'),
]
