from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^(?P<story_id>\d+)/$', 'story.views.story_view', name='story'),
    url(r'^edit/(?P<story_id>\d+)/$', 'story.views.edit_story', name='edit_story'),
    url(r'^delete/(?P<story_id>\d+)/$', 'story.views.delete_story', name='delete_story'),
    url(r'^new/$', 'story.views.new_story', name='new_story'),
    url(r'^submit/$', 'story.views.submit_story', name='submit_story'),
    url(r'^unsubscribe/(?P<story_id>\d+)/$', 'story.views.story_unsubscribe', name='story-unsub'),
    url(r'^subscribe/(?P<story_id>\d+)/$', 'story.views.story_subscribe', name='story-sub'),
    url(r'^prequels/unsubscribe/(?P<story_id>\d+)/$', 'story.views.prequel_unsubscribe', name='prequel-unsub'),
    url(r'^prequels/subscribe/(?P<story_id>\d+)/$', 'story.views.prequel_subscribe', name='prequel-sub'),
    url(r'^sequels/unsubscribe/(?P<story_id>\d+)/$', 'story.views.sequel_unsubscribe', name='sequel-unsub'),
    url(r'^sequels/subscribe/(?P<story_id>\d+)/$', 'story.views.sequel_subscribe', name='sequel-sub'),
    url(r'^$', 'story.views.browse_stories', name='recent_stories'),
    url(r'^active/$', 'story.views.active_stories', name='active_stories'),
    url(r'^popular/$', 'story.views.popular_stories', name='popular_stories'),
]
