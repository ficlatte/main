from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^(?P<pen_name>[^/]+)/$', 'author.views.author', name='author'),
    url(r'^u/drafts/$', 'author.views.drafts', name='drafts'),
    url(r'^u/prompts/$', 'author.views.author_prompts', name='author_prompts'),
    url(r'^u/challenges/$', 'author.views.author_challenges', name='author_challenges'),
    url(r'^u/profile/$', 'author.views.profile_view', name='profile'),
    url(r'^u/submit/$', 'author.views.submit_profile', name='submit_profile'),
]
