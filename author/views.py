from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Sum, Avg, Q, Count, F
from django.utils.http import urlquote_plus, urlquote
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta, date
from random import randint
from struct import unpack
import os
import math
import re
import hashlib
from castle.models import *
from castle.views import *

#-----------------------------------------------------------------------------
def author(request, pen_name):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Get target author's information
    author = Profile.objects.filter(pen_name_uc = pen_name.upper())
    if (not author):
        raise Http404()
    author = author[0]          # Get single object from collection

    # Is logged-in user the author?
    owner = ((profile is not None) and (profile == author))

    # Has the author's email been confirmed?
    email_conf = True
    if (profile):
        email_conf = (profile.email_auth == 0)

    # Build story list (owner sees their drafts)
    page_num = safe_int(request.GET.get('page_num', 1))
    if (owner):
        num_stories = Story.objects.filter(user = author).count()
        story_list = Story.objects.filter(user = author).order_by('-draft','-ptime','-mtime')[(page_num-1)*PAGE_STORIES:page_num*PAGE_STORIES]
        num_prompts = Prompt.objects.filter(user = author).count()
        prompt_list = Prompt.objects.filter(user = author).order_by('-mtime')[(page_num-1)*PAGE_PROMPTS:page_num*PAGE_PROMPTS]
        num_challenges = Challenge.objects.filter(user = author).count()
        challenge_list = Challenge.objects.filter(user = author).order_by('-mtime')[(page_num-1)*PAGE_CHALLENGES:page_num*PAGE_CHALLENGES]
    else:
        num_stories = Story.objects.filter(user = author, draft = False).count()
        story_list = Story.objects.filter(user = author, draft = False).order_by('-ptime')[(page_num-1)*PAGE_STORIES:page_num*PAGE_STORIES]
        num_prompts = Prompt.objects.filter(user = author).count()
        prompt_list = Prompt.objects.filter(user = author).order_by('-mtime')[(page_num-1)*PAGE_PROMPTS:page_num*PAGE_PROMPTS]
        num_challenges = Challenge.objects.filter(user = author).count()
        challenge_list = Challenge.objects.filter(user = author).order_by('-mtime')[(page_num-1)*PAGE_CHALLENGES:page_num*PAGE_CHALLENGES]

    # Friendship?
    is_friend = False
    if (profile and author):
        is_friend = profile.is_friend(author)

    # Build context and render page
    context = { 'profile'       : profile,
                'author'        : author,
                'owner'			: owner,
                'story_list'    : story_list,
                'num_prompts'   : num_prompts,
                'prompt_list'   : prompt_list,
                'num_challenges' : num_challenges,
                'challenge_list' : challenge_list,
                'email_conf'    : email_conf,
                'page_title'    : author.pen_name,
                'page_url'      : u'/authors/'+urlquote(author.pen_name)+u'/',
                'pages'         : bs_pager(page_num, PAGE_STORIES, num_stories),
                'is_friend'     : is_friend,
                'user_dashboard': owner,
                'other_user_sidepanel' : (not owner),
            }
    return render(request, 'authors/author.html', context)

#-----------------------------------------------------------------------------
@login_required
def drafts(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
    
    # Has the author's email been confirmed?
    email_conf = (profile.email_auth == 0)

    # Build story list (owner sees their drafts)
    page_num = safe_int(request.GET.get('page_num', 1))
    num_stories = Story.objects.filter(user = profile, draft=True).count()
    story_list = Story.objects.filter(user = profile, draft=True).order_by('-mtime')[(page_num-1)*PAGE_STORIES:page_num*PAGE_STORIES]

    # Build context and render page
    context = { 'profile'       : profile,
                'author'        : profile,
                'story_list'    : story_list,
                'page_title'    : profile.pen_name,
                'email_conf'	: email_conf,
                'page_url'      : u'/authors/'+urlquote(profile.pen_name)+u'/',
                'pages'         : bs_pager(page_num, PAGE_STORIES, num_stories),
                'drafts_page'   : True,
                'user_dashboard': True,
                'other_user_sidepanel' : False,
            }
    return render(request, 'authors/author.html', context)

#-----------------------------------------------------------------------------
@login_required
def author_prompts(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Has the author's email been confirmed?
    email_conf = (profile.email_auth == 0)

    # Build story list (owner sees their drafts)
    page_num = safe_int(request.GET.get('page_num', 1))
    num_prompts = Prompt.objects.count()
    prompt_list = Prompt.objects.filter(user = profile).order_by('-mtime')[(page_num-1)*PAGE_STORIES:page_num*PAGE_STORIES]

    # Build context and render page
    context = { 'profile'       : profile,
                'author'        : profile,
                'prompt_list'   : prompt_list,
                'page_title'    : profile.pen_name,
                'email_conf'	: email_conf,
                'page_url'      : u'/authors/'+urlquote(profile.pen_name)+u'/',
                'pages'         : bs_pager(page_num, PAGE_STORIES, num_prompts),
                'prompts_page'  : True,
                'user_dashboard': True,
                'other_user_sidepanel' : False,
            }
    return render(request, 'authors/author.html', context)

#-----------------------------------------------------------------------------
@login_required
def author_challenges(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
        
    # Has the author's email been confirmed?
    email_conf = (profile.email_auth == 0)

    # Build story list (owner sees their drafts)
    page_num = safe_int(request.GET.get('page_num', 1))
    num_challenges = Challenge.objects.count()
    challenge_list = Challenge.objects.filter(user = profile).order_by('-mtime')[(page_num-1)*PAGE_STORIES:page_num*PAGE_STORIES]

    # Build context and render page
    context = { 'profile'       : profile,
                'author'        : profile,
                'challenge_list': challenge_list,
                'page_title'    : profile.pen_name,
                'email_conf'	: email_conf,
                'page_url'      : u'/authors/'+urlquote(profile.pen_name)+u'/',
                'pages'         : bs_pager(page_num, PAGE_STORIES, num_challenges),
                'challenges_page' : True,
                'user_dashboard': True,
                'other_user_sidepanel' : False,
            }
    return render(request, 'authors/author.html', context)
    
#-----------------------------------------------------------------------------
#@login_required
def profile_view(request, error_title=None, error_messages=None):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Do e-mail subscription bits
    email_flags = []

    new_email_flag_entry(request, email_flags, profile, Profile.AUTOSUBSCRIBE_ON_STORY, u'when you publish a story')
    new_email_flag_entry(request, email_flags, profile, Profile.AUTOSUBSCRIBE_ON_STORY_COMMENT, u'when you comment on a story')
    new_email_flag_entry(request, email_flags, profile, Profile.AUTOSUBSCRIBE_ON_BLOG, u'when you publish a blog post', 'castle.post_blog')
    new_email_flag_entry(request, email_flags, profile, Profile.AUTOSUBSCRIBE_ON_BLOG_COMMENT, u'when you comment on a blog post')
    new_email_flag_entry(request, email_flags, profile, Profile.AUTOSUBSCRIBE_ON_PROMPT, u'when you publish a prompt')
    new_email_flag_entry(request, email_flags, profile, Profile.AUTOSUBSCRIBE_ON_PROMPT_COMMENT, u'when you comment on a prompt')
    new_email_flag_entry(request, email_flags, profile, Profile.AUTOSUBSCRIBE_ON_CHALLENGE, u'when you publish a challenge')
    new_email_flag_entry(request, email_flags, profile, Profile.AUTOSUBSCRIBE_ON_CHALLENGE_COMMENT, u'when you comment on a challenge')
    new_email_flag_entry(request, email_flags, profile, Profile.AUTOSUBSCRIBE_TO_PREQUEL, u'when someone prequels a story you wrote')
    new_email_flag_entry(request, email_flags, profile, Profile.AUTOSUBSCRIBE_TO_SEQUEL, u'when someone sequels a story you wrote')
    new_email_flag_entry(request, email_flags, profile, Profile.AUTOSUBSCRIBE_TO_CHALLENGE_ENTRY, u'when someone enters a story in a challenge you created')

    # Page title
    if (profile):
        page_title = u'Profile of '+profile.pen_name
    else:
        page_title = u'Register new user'

    # Build context and render page
    context = { 'profile'       : profile,
                'length_limit'  : 1024,
                'length_min'    : 1,
                'page_title'    : page_title,
                'email_flags'   : email_flags,
                'error_title'   : error_title,
                'error_messages': error_messages,
            }

    return render(request, 'authors/profile.html', context)

#-----------------------------------------------------------------------------
@transaction.atomic
def submit_profile(request):
    # Get user profile
    new_registration = False
    new_email_addr = False
    if (request.user.is_authenticated()):
        profile = request.user.profile
    else:
        profile = Profile()
        new_registration = True

    # Get data from form
    pen_name        	= request.POST.get('pen_name', '')
    password        	= request.POST.get('password', '')
    new_password    	= request.POST.get('new_password', '')
    password_again  	= request.POST.get('password', '')
    site_url        	= request.POST.get('site_url', '')
    site_name       	= request.POST.get('site_name', '')
    facebook_username	= request.POST.get('facebook_username', '')
    twitter_username	= request.POST.get('twitter_username', '')
    wattpad_username	= request.POST.get('wattpad_username', '')
    biography       	= request.POST.get('biography', '')
    mature          	= request.POST.get('mature', '')
    email_addr      	= request.POST.get('email_addr', '')
    rules           	= request.POST.get('rules', False)

    # Update and verify profile object
    errors     = []
    if (pen_name and ((profile.pen_name_uc is None) or (pen_name.upper() != profile.pen_name_uc))):
        # Pen name is set and it is different from the stored value
        profile.pen_name = pen_name
        profile.pen_name_uc = pen_name.upper()
        if (Profile.objects.filter(pen_name_uc = pen_name.upper())):
            errors.append(u'Sorry, that pen-name is already taken')

    if (new_registration):
        # Password check for new user
        if (len(password) < 6):
            errors.append(u'Password must be at least 6 characters')
        if (password != password_again):
            errors.append(u'Password and password check did not match')
    elif (new_password):
        if (not request.user.check_password(password)):
            errors.append(u'Old password incorrect')
        if (len(new_password) < 6):
            errors.append(u'Password must be at least 6 characters')
        if (new_password != password_again):
            errors.append(u'Password and password check did not match')
    elif (password):
        if (not request.user.check_password(password)):
            errors.append(u'Old password incorrect')

    if (site_url == ''):
        profile.site_url = None
    else:
        profile.site_url = site_url
    
    if (site_name == ''):
        profile.site_name = None
    else:    
        profile.site_name = site_name
        
    if (facebook_username == ''):
        profile.facebook_username = None
    else:
        profile.facebook_username = facebook_username
        
    if (twitter_username == ''):
        profile.twitter_username = None
    else:
        profile.twitter_username = twitter_username
        
    if (wattpad_username == ''):
        profile.wattpad_username = None
    else:
        profile.wattpad_username = wattpad_username
    
    if (new_registration or biography):
        # Condense all end-of-line markers into \n
        profile.biography = re_crlf.sub(u"\n", biography)

        if (len(biography) < 2):
            errors.append(u'Biography must be at least 2 characters.  Tell us a bit about yourself')
    if (mature):
        profile.mature = True
    else:
        profile.mature = False
    if ((new_registration or email_addr) and not validate_email_addr(email_addr)):
        errors.append(u'Sorry, but we need an e-mail address')
    if (not rules):
        errors.append(u'You need to agree to the rules before you play')

    # E-mail preferences
    eflags = 0
    flag = 1
    for i in range(Profile.NUM_EMAIL_FLAGS):
        if 'ef_{}'.format(flag) in request.POST:
            eflags = eflags | flag
        flag *= 2
    profile.email_flags = eflags

    # If user is changing e-mail address, they need their password too
    if (not new_registration and (
            (email_addr and email_addr != profile.email_addr) or
            (pen_name   and pen_name.upper() != profile.pen_name_uc))):
        if (not password):
            errors.append(u'When you change your pen name or e-mail address, you need to supply your password too.')
        elif (not request.user.check_password(password)):
            errors.append(u'Old password incorrect')
        else:
            new_email_addr = True

    # Set modification time
    time_now = timezone.now()
    profile.mtime = time_now

    # If there have been errors, re-display the page
    if (errors):
        if (new_registration):
            return profile_view(request, 'Registration unsuccessful', errors)
        else:
            return profile_view(request, 'Profile update unsuccessful', errors)


    # If new registration, we should create a new Django user
    if (new_registration):
        # Create a temporary user name because we need to call the
        # user something whilst we create the profile entry
        # We then go back and update the Django user name to express clearly
        # the connection with the profile table
        un = u'{:016x}'.format(random64())
        user = User(
            username = u'user{}'+un,
            first_name = u'user',
            last_name = un,
            email = email_addr,
            )
        user.set_password(password)
        user.save()
        profile.user = user
        profile.save()
        un = unicode(profile.id)
        user.username = u'user'+un
        user.last_name = un;
        user.save()
        user = authenticate(username=profile.user.username, password=password)
        login(request, user)
    else:
        profile.save()

    # If this is a new user, or the e-mail address is changed, send a conf email
    if (new_registration or new_email_addr):
        # Get random 64 bit integer
        token = random64()
        token_s = to_signed64(token)
        profile.email_addr = email_addr
        profile.email_auth = token_s
        profile.email_time = time_now
        send_conf_email(profile, token)
        profile.save()

    return HttpResponseRedirect(reverse('author', args=(profile.pen_name,)))
    
#-----------------------------------------------------------------------------
