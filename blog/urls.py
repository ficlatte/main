from django.urls import path
from . import views

urlpatterns = [
    path('', views.blogs, name='blogs'),
    path('<int:blog_id>/', views.blog_view, name='blog'),
    path('edit/<int:blog_id>/', views.edit_blog, name='edit_blog'),
    path('new/', views.new_blog, name='new_blog'),
    path('submit/', views.submit_blog, name='submit_blog'),
    path('unsubscribe/<int:blog_id>/', views.blog_unsubscribe, name='blog-unsub'),
]
