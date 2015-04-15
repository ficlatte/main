from django.conf.urls import patterns, include, url
from django.contrib import admin

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'ficlatte.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^$',      'castle.views.home', name='home'),
    url(r'^authors/(?P<pen_name>[^/]+)/$', 'castle.views.author', name='author'),
    url(r'^stories/(?P<story_id>\d+)/$', 'castle.views.story', name='story'),
    url(r'^stories/edit/(?P<story_id>\d+)/$', 'castle.views.edit_story', name='edit_story'),
    url(r'^stories/new/$', 'castle.views.new_story', name='new_story'),
    url(r'^prompts/$', 'castle.views.prompts', name='prompts'),
    url(r'^prompts/(?P<prompt_id>\d+)/$', 'castle.views.prompt', name='prompt'),
    url(r'^admin/', include(admin.site.urls)),
)
