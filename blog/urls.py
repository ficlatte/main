from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', 'blog.views.blogs', name='blogs'),
    url(r'^(?P<blog_id>\d+)/$', 'blog.views.blog_view', name='blog'),
    url(r'^edit/(?P<blog_id>\d+)/$', 'blog.views.edit_blog', name='edit_blog'),
    url(r'^new/$', 'blog.views.new_blog', name='new_blog'),
    url(r'^submit/$', 'blog.views.submit_blog', name='submit_blog'),
    url(r'^unsubscribe/(?P<blog_id>\d+)/$', 'blog.views.blog_unsubscribe', name='blog-unsub'),
]
