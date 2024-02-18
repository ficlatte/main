#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# django-bbcode: util.py
##

import re
import bbcode.settings

def to_html(text,
            tags_alternative_definition={},
            escape_html=True,
            method='disable',
            *tags):
    """
    Convert a string with BBCode markup into its corresponding HTML markup.

    Basic Usage
    -----------

    The first parameter is the string off BBCode markup to be processed

        >>> text = "[b]some bold text to markup[/b]"
        >>> output = bbcode.util.to_html(text)
        >>> print output
        <strong>some bold text to markup</strong>

    Custom BBCode translations
    --------------------------

    You can supply your own BBCode markup translations to create your own
    custom markup, or override the default BBRuby translations (parameter is a
    dictionary of custom translations).

    The dictionary takes the following format:

        'name': [regexp, replacement, description, example, enable_symbol]

    For example,

       custom_blockquote = {
           'Quote': [
               r"\[quote(:.*)?=(.*?)\](.*?)\[\/quote\1?\]",
               '<div class="quote"><p><cite>\\2</cite></p><blockquote>\\3</blockquote></div>',
               'Quote with citation',
               '[quote=mike]please quote me[/quote]',
               'quote' ],
       }

    Enable and Disable specific tags
    --------------------------------

    Django-bbcode will allow you to only enable certain BBCode tags, or to
    explicitly disable certain tags.  Pass in either 'disable' or 'enable' to
    set your method, followed by the comma-separated list of tags you wish to
    disable or enable.

        ##
        # Translate BBCode to HTML, enabling 'image', 'bold', and 'quote' tags
        # *only*.
        bbcode.util.to_html(text, {}, True,
                            'enable',  'image', 'bold',  'quote')

        ##
        # Translate BBCode to HTML, enabling all tags *except* 'image',
        # 'bold', and 'quote'.
        bbcode.util.to_html(text, {}, True,
                            'disable', 'image', 'video', 'color')
    """
    # escape <, >, and & to remove any html
    if escape_html:
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')

    # merge in the alternate definitions, if any.  Unfortunately there is no
    # Python 2.3 compatible efficient way to do this.
    tags_definition = bbcode.settings.TAGS
    for x in tags_alternative_definition:
        tags_definition[x] = tags_alternative_definition[x]

    # parse bbcode tags
    if method == 'enable':
        for x in tags_definition:
            t = tags_definition[x]
            if t[4] in tags:
                regex = re.compile(t[0], re.IGNORECASE|re.DOTALL)
                text = regex.sub(t[1], text)
    if method == 'disable':
        # this works nicely because the default is disable and the default set
        # of tags is [] (so none disabled) :)
        for x in tags_definition:
            t = tags_definition[x]
            if t[4] not in tags:
                regex = re.compile(t[0], re.IGNORECASE|re.DOTALL)
                text = regex.sub(t[1], text)

    # parse spacing
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"\n", "<br />", text)

    # return markup
    return text

##
# End of File
##
