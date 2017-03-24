# coding: utf-8
from comment.views import *


# -----------------------------------------------------------------------------
def blogs(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Get blogs
    page_num = safe_int(request.GET.get('page_num', 1))
    blogs = Blog.objects.exclude(draft=True).order_by('-ptime')[(page_num - 1) * PAGE_BLOG:page_num * PAGE_BLOG]
    num_blogs = Blog.objects.exclude(draft=True).count()

    # Build context and render page
    context = {'profile'     : profile,
               'blogs'       : blogs,
               'page_title'  : u'Blog page {}'.format(page_num),
               'page_url'    : u'/blog/',
               'pages'       : bs_pager(1, 10, blogs.count()),
               }

    return render(request, 'blogs/blogs.html', context)


# -----------------------------------------------------------------------------
def blog_view(request, blog_id, comment_text=None, error_title='', error_messages=None):
    blog = get_object_or_404(Blog, pk=blog_id)

    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    # Is logged-in user the author?
    author = blog.user
    owner = ((profile is not None) and (profile == author))

    # Get comments
    page_num = safe_int(request.GET.get('page_num', 1))
    comments = blog.comment_set.all().order_by('ctime')[(page_num - 1) * PAGE_COMMENTS:page_num * PAGE_COMMENTS]

    # Is user subscribed?
    subscribed = False
    if (profile is not None):
        subscribed = (blog.subscriptions.filter(user=profile).count() > 0)

    # Build context and render page
    context = {'profile'         : profile,
               'author'          : blog.user,
               'blog'            : blog,
               'comments'        : comments,
               'page_url'        : u'/stories/' + unicode(blog_id),
               'pages'           : bs_pager(page_num, PAGE_COMMENTS, blog.comment_set.count()),
               'owner'           : owner,
               'comment_text'    : comment_text,
               'subscribed'      : subscribed,
               'error_title'     : error_title,
               'error_messages'  : error_messages,
               'page_title'      : u'Blog ' + blog.title,
               }

    return render(request, 'blogs/blog.html', context)


# -----------------------------------------------------------------------------
@login_required
def blog_unsubscribe(request, blog_id, error_title='', error_messages=None):
    blog = get_object_or_404(Blog, pk=blog_id)
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile
    if (profile is None):
        raise Http404

    Subscription.objects.filter(user=profile, blog=blog).delete()

    context = {'thing'            : blog,
               'thing_type'       : u'blog',
               'thing_url'        : reverse('blog', args=[blog.id]),
               'page_title'       : u'Unsubscribe blog ' + blog.title,
               'error_title'      : error_title,
               'error_messages'   : error_messages,
               'user_dashboard'   : True,
               'profile'          : profile,
               }

    return render(request, 'blogs/unsubscribed.html', context)


# -----------------------------------------------------------------------------
@login_required
def new_blog(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    if ((profile is None) or (not request.user.has_perm("castle.post_blog"))):
        raise Http404

    # Build context and render page
    context = {'profile'          : profile,
               'blog'             : Blog(),  # Create blank blog for default purposes
               'page_title'       : u'Write new blog',
               'length_limit'     : 20480,
               'length_min'       : 60,
               'user_dashboard'   : 1,
               }

    return render(request, 'blogs/edit_blog.html', context)


# -----------------------------------------------------------------------------
@login_required
def edit_blog(request, blog_id):
    # Get blog
    blog = get_object_or_404(Blog, pk=blog_id)

    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    if ((profile is None) or (not request.user.has_perm("castle.post_blog"))):
        raise Http404

    # Build context and render page
    context = {'profile'          : profile,
               'blog'             : blog,
               'page_title'       : u'Edit blog ' + blog.title,
               'length_limit'     : 20480,
               'length_min'       : 60,
               'user_dashboard'   : 1,
               }

    return render(request, 'castle/edit_blog.html', context)


# -----------------------------------------------------------------------------
@login_required
@transaction.atomic
def submit_blog(request):
    # Get user profile
    profile = None
    if (request.user.is_authenticated()):
        profile = request.user.profile

    if ((profile is None) or (not request.user.has_perm("castle.post_blog"))):
        raise Http404

    # Get bits and bobs
    errors = []
    blog = get_foo(request.POST, Blog, 'bid')
    new_blog = (blog is None)
    was_draft = False
    if (not new_blog):  # Remember if the blog was draft
        was_draft = blog.draft
    draft = request.POST.get('is_draft', False)
    bbcode = request.POST.get('is_bbcode', False)

    if (not profile.email_authenticated()):
        errors.append(u'You must have authenticated your e-mail address before posting a blog')
    else:
        # Get blog object, either existing or new
        if (blog is None):
            blog = Blog(user=profile)

        # Populate blog object with data from submitted form
        blog.title = request.POST.get('title', '')
        blog.body = request.POST.get('body', '')
        blog.draft = draft
        blog.bbcode = bbcode

        # Condense all end-of-line markers into \n
        blog.body = re_crlf.sub(u"\n", blog.body)

        # Check for submission errors
        if (len(blog.title) < 1):
            errors.append(u'Blog title must be at least 1 character long')

        l = len(blog.body)
        if ((not blog.draft) and (l < 60)):
            errors.append(u'Blog body must be at least 60 characters long')

        if (l > 20480):
            errors.append(u'Blog is over 20480 characters (currently ' + unicode(l) + u')')

    # If there have been errors, re-display the page
    if errors:
        # Build context and render page
        context = {'profile'         : profile,
                   'blog'            : blog,
                   'page_title'      : u'Edit blog ' + blog.title,
                   'length_limit'    : 20480,
                   'length_min'      : 60,
                   'user_dashboard'  : 1,
                   'error_title'     : 'Blog submission unsuccessful',
                   'error_messages'  : errors,
                   }

        return render(request, 'blogs/edit_blog.html', context)

    # Is the blog being published?
    if (not draft and (was_draft or new_blog)):
        blog.ptime = timezone.now()

    # Set modification time
    blog.mtime = timezone.now()

    # No problems, update the database and redirect
    blog.save()

    # Auto-subscribe to e-mail notifications according to user's preferences
    if (new_blog):
        if (profile.email_flags & Profile.AUTOSUBSCRIBE_ON_BLOG):
            Subscription.objects.get_or_create(user=profile, blog=blog)

    return HttpResponseRedirect(reverse('blog', args=(blog.id,)))

# -----------------------------------------------------------------------------
