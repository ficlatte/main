from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from castle.models import *
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Sum

# Create your views here.
#-----------------------------------------------------------------------------
# Views
#-----------------------------------------------------------------------------
def home(request):
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
    context = { 'thing_list': 'moof',
                'profile'   : profile,
                'blog_latest' : Blog.objects.all().order_by('-id')[0]
              }
    return render(request, 'castle/index.html', context)
