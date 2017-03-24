from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', 'prompt.views.prompts', name='prompts'),
    url(r'^(?P<prompt_id>\d+)/$', 'prompt.views.prompt_view', name='prompt'),
    #url(r'^edit/(?P<prompt_id>\d+)/$', 'prompt.views.edit_prompt', name='edit_prompt'),
    url(r'^new/$', 'prompt.views.new_prompt', name='new_prompt'),
    url(r'^submit/$', 'prompt.views.submit_prompt', name='submit_prompt'),
    url(r'^unsubscribe/(?P<prompt_id>\d+)/$', 'prompt.views.prompt_unsubscribe', name='prompt-unsub'),
    url(r'^subscribe/(?P<prompt_id>\d+)/$', 'prompt.views.prompt_subscribe', name='prompt-sub'),
    url(r'^recent/$', 'prompt.views.browse_prompts', name='prompts_recent'),
    url(r'^active/$', 'prompt.views.active_prompts', name='prompts_active'),
    url(r'^popular/$', 'prompt.views.popular_prompts', name='prompts_popular'),
]
