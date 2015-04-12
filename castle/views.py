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
    context = { 'thing_list': 'moof' }
    return render(request, 'castle/index.html', context)
