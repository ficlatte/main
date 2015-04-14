from django.conf.urls import patterns, include, url
from django.contrib import admin

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'ficlatte.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^$',      'castle.views.home', name='home'),
    url(r'^authors/(?P<pen_name>[^/]+)/$', 'castle.views.author', name='author'),
    url(r'^stories/(?P<story_id>[^/]+)/$', 'castle.views.story', name='story'),
    url(r'^admin/', include(admin.site.urls)),
)
