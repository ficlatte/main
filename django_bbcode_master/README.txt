::
: django-bbcode: README.txt
::

Django-bbcode
=============

* http://github.com/maaku/django-bbcode

DESCRIPTION
-----------

Django-bbcode is a BBCode (http://www.bbcode.org) implementation for Python/
Django.  It will convert strings with BBCode markup to their HTML equivalent.
It is based upon the BBRuby library, which provides similar functionality to
Ruby developers.

INSTALL
-------

Please see the file INSTALL.txt.

USAGE
-----

  # Add django-bbcode to the list of installed applications in settings.py,
  # then in a file which requires BBCode functionality:
  from bbcode import util as bbcode

All of the functionality of django-bbcode is implemented by a single helper
method, to_html:

  text = "[b]Here is some bold text[/b] followed by some [u]underlined text[/u]"
  output = bbcode.to_html(text)

Django-bbcode will auto-escape HTML tags.  To prevent this just pass False as
the third param:

  output = bbcode.to_html(text, {}, False)

To allow only certain tags:

  output = bbcode.to_html(text, {}, True, 'enable', 'image', 'bold', 'quote')

To disable certain tags, but leave everything else enabled::

  output = bbcode.to_html(text, {}, True, 'disable', 'image', 'bold', 'quote')

Define your own translation, in order to be more flexible:

    my_blockquote = {
      'Quote': [
        r"\[quote(:.*)?=(.*?)\](.*?)\[/quote\\1?\]",
        '<div class="quote"><p><cite>\\2</cite></p><blockquote>\\3</blockquote></div>',
        'Quote with citation',
        '[quote=mike]please quote me[/quote]',
        'quote'
      ],
    }
 
    bbcode.to_html(text, my_blockquote)

TAGS PROCESSED
--------------

The following is the list of BBCode tags processed by Django-bbcode and their
associated symbol for enabling/disabling them

* [b]               'bold'
* [i]               'italics'
* [u]               'underline'
* [s]               'strikeout'
* [del]             'delete'
* [ins]             'insert'
* [code]            'code'
* [size]            'size'
* [color]           'color'
* [ol]              'orderedlist'
* [ul]              'unorderedlist'
* [li]              'listitem'
* [*]               'listitem'
* [list]            'listitem'
* [list=1]          'listitem'
* [list=a]          'listitem'
* [dl]              'definelist'
* [dt]              'defineterm'
* [dd]              'definition'
* [quote]           'quote'
* [quote=source]    'quote'
* [url=link]        'link'
* [url]             'link'
* [img size=]       'image'
* [img=]            'image'
* [img]             'image'
* [youtube]         'video'
* [gvideo]          'video'
* [email]           'email'

::
: End of File
::
