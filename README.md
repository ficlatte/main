# Ficlatté
Ficlatté website main code

Site can be found at https://ficlatte.com

It's for writing micro-fiction.

# Getting started (on Linux)
You'll need to install MySQL, Python 2.7 and Django 1.8.4 (which is a bit behind the head for now)

$ sudo apt install python-pip python-dev mysql-server libmysqlclient-dev python-mysqldb

then

$ mysql -u root -p

and, at the mysql prompt:

mysql> CREATE DATABASE ficlatte CHARACTER SET UTF8;  
mysql> CREATE USER ficlatte@localhost IDENTIFIED BY 'password';  
mysql> GRANT ALL PRIVILEGES ON ficlatte.* TO ficlatte@localhost;  
mysql> exit

Install Django  
$ sudo -H pip install django==1.8.4
$ sudo -H pip install django-datetime-widget

Get Django started  
$ cd ficlatte_directory  
$ cd ficlatte  
$ cp settings-example.py settings.py  
$ vi/emacs/whatever settings.py  

and edit the settings file (see https://docs.djangoproject.com/en/1.8/ref/settings/ or see below for the current settings in use).  Under DATABASES, make sure that the NAME is set to the name of the database ('ficlatte' if you followed the instructions above), that USER is set to the database username (also 'ficlatte' if you followed the instructions) and that PASSWORD is set to the password, which really should not be 'password'.  It would be useful for you to set up the EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER and EMAIL_HOST_PASSWORD to settings provided by your e-mail provider.  This will allow the system to send you notification e-mails (handy for those pesky new-user verification e-mails).  If you want to fake e-mail verification, use the admin interface to edit the user's profile entry directly and set email_auth to 0.

Now, create all the database structures:

$ python manage.py makemigrations  
$ python manage.py migrate

After you've done that, create yourself a superuser account (useful).  Note that the admin account is not normally associated with a Ficlatté author profile.

$ python manage.py createsuperuser

and start the test server running

$ python manage.py runserver

You should now be able to connect to the test server (http://127.0.0.1:8000) using your superuser account, or create yourself an author using the 'register' link in the top right hand corner: just like if you were using the real site.

For your local development server, you can run an email simulator by running the following command in a new terminal window:

$ python -m smtpd -n -c DebuggingServer localhost:1025

The challenges module requires a datepicker package be installed:

$ pip install django-datetime-widget

Update settings.py:

INSTALLED_APPS = (  
    'django.contrib.admin',  
    'django.contrib.auth',  
    'django.contrib.contenttypes',  
    'django.contrib.sessions',  
    'django.contrib.messages',  
    'django.contrib.staticfiles',  
    'django.contrib.sitemaps',  
    'castle',  
    'blog',  
    'author',  
    'story',  
    'prompt',  
    'challenge',  
    'notes',  
    'comment',  
    'bbcode',  
    'datetimewidget',  
)   

MIDDLEWARE_CLASSES = (  
    'django.contrib.sessions.middleware.SessionMiddleware',  
    'django.middleware.locale.LocaleMiddleware',  
    'django.middleware.common.CommonMiddleware',  
    'django.middleware.csrf.CsrfViewMiddleware',  
    'django.contrib.auth.middleware.AuthenticationMiddleware',  
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',  
    'django.contrib.messages.middleware.MessageMiddleware',  
    'django.middleware.clickjacking.XFrameOptionsMiddleware',  
)  

