#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# django-bbcode: settings.py
##

VERSION = '0.8.4'

##
# Allowable image formats
PERMITTED_IMAGE_FORMATS = ['png','bmp','jpg','gif','jpeg']

##
# Built-in BBCode tags that will be processed
TAGS = {
    ##
    # tag_name: [regex, replace, description, example, enable/disable symbol]
    'Bold': [
        r"\[b(:.*)?\](.*?)\[\/b\1?\]",
        '<strong>\\2</strong>',
        'Embolden text',
        'Look [b]here[/b]',
        'bold'],
    'Italics': [
        r"\[i(:.+)?\](.*?)\[\/i\1?\]",
        '<em>\\2</em>',
        'Italicize or emphasize text',
        'Even my [i]cat[/i] was chasing the mailman!',
        'italics'],
    'Underline': [
        r"\[u(:.+)?\](.*?)\[\/u\1?\]",
        '<u>\\2</u>',
        'Underline',
        'Use it for [u]important[/u] things or something',
        'underline'],
    'Strikeout': [
        r"\[s(:.+)?\](.*?)\[\/s\1?\]",
        '<del>\\2</del>',
        'Strikeout',
        '[s]nevermind[/s]',
        'strikeout'],
    'Delete': [
        r"\[del(:.+)?\](.*?)\[\/del\1?\]",
        '<del>\\2</del>',
        'Deleted text',
        '[del]deleted text[/del]',
        'delete'],
    'Insert': [
        r"\[ins(:.+)?\](.*?)\[\/ins\1?\]",
        '<ins>\\2</ins>',
        'Inserted Text',
        '[ins]inserted text[/del]',
        'insert'],
    'Code': [
        r"\[code(:.+)?\](.*?)\[\/code\1?\]",
        '<code>\\2</code>',
        'Code Text',
        '[code]some code[/code]',
        'code'],
    'Size': [
        r"\[size=['\"]?(.*?)['\"]?\](.*?)\[\/size\]",
        '<span style="font-size: \\1px;">\\2</span>',
        'Change text size',
        '[size=20]Here is some larger text[/size]',
        'size'],
    'Color': [
        r"\[color=['\"]?(\w+|\#\w{6})['\"]?(:.+)?\](.*?)\[\/color\2?\]",
        '<span style="color: \\1;">\\3</span>',
        'Change text color',
        '[color=red]This is red text[/color]',
        'color'],
    'Ordered List': [
        r"\[ol\](.*?)\[\/ol\]",
        '<ol>\\1</ol>',
        'Ordered list',
        'My favorite people (alphabetical order): [ol][li]Jenny[/li][li]Alex[/li][li]Beth[/li][/ol]',
        'orderedlist'],
    'Unordered List': [
        r"\[ul\](.*?)\[\/ul\]",
        '<ul>\\1</ul>',
        'Unordered list',
        'My favorite people (order of importance): [ul][li]Jenny[/li][li]Alex[/li][li]Beth[/li][/ul]',
        'unorderedlist'],
    'List Item': [
        r"\[li\](.*?)\[\/li\]",
        '<li>\\1</li>',
        'List item',
        'See ol or ul',
        'listitem'],
    'List Item (alternative)': [
        r"\[\*(:[^\[]+)?\]([^(\[|\<)]+)",
        '<li>\\2</li>',
        'List item (alternative)',
        '[*]list item',
        'listitem'],
    'Unordered list (alternative)': [
        r"\[list(:.*)?\]((?:(?!list).)*)\[\/list(:.)?\1?\]",
        '<ul>\\2</ul>',
        'Unordered list item',
        '[list][*]item 1[*] item2[/list]',
        'list'],
    'Ordered list (numerical)': [
        r"\[list=1(:.*)?\](.+)\[\/list(:.)?\1?\]",
        '<ol>\\2</ol>',
        'Ordered list numerically',
        '[list=1][*]item 1[*] item2[/list]',
        'list'],
    'Ordered list (alphabetical)': [
        r"\[list=a(:.*)?\](.+)\[\/list(:.)?\1?\]",
        '<ol sytle="list-style-type: lower-alpha;">\\2</ol>',
        'Ordered list alphabetically',
        '[list=a][*]item 1[*] item2[/list]',
        'list'],
    'Definition List': [
        r"\[dl\](.*?)\[\/dl\]",
        '<dl>\\1</dl>',
        'List of terms/items and their definitions',
        '[dl][dt]Fusion Reactor[/dt][dd]Chamber that provides power to your... nerd stuff[/dd][dt]Mass Cannon[/dt][dd]A gun of some sort[/dd][/dl]',
        'definelist'],
    'Definition Term': [
        r"\[dt\](.*?)\[\/dt\]",
        '<dt>\\1</dt>',
        'List of definition terms',
        '[dt]definition term[/dt]',
        'defineterm'],
    'Definition Definition': [
        r"\[dd\](.*?)\[\/dd\]",
        '<dd>\\1</dd>',
        'Definition definitions',
        '[dd]my definition[/dd]',
        'definition'],
    'Quote': [
        r"\[quote(:.*)?=\"?(.*?)\"?\](.*?)\[\/quote\1?\]",
        '<fieldset><legend>\\2</legend><blockquote>\\3</blockquote></fieldset>',
        'Quote with citation',
        "[quote=mike]Now is the time...[/quote]",
        'quote'],
    'Quote (Sourceless)': [
        r"\[quote(:.*)?\](.*?)\[\/quote\1?\]",
        '<fieldset><blockquote>\\2</blockquote></fieldset>',
        'Quote (sourceclass)',
        "[quote]Now is the time...[/quote]",
        'quote'],
    'Link': [
        r"\[url=(.*?)\](.*?)\[\/url\]",
        '<a href="\\1">\\2</a>',
        'Hyperlink to somewhere else',
        'Maybe try looking on [url=http://google.com]Google[/url]?',
        'link'],
    'Link (Implied)': [
        r"\[url\](.*?)\[\/url\]",
        '<a href="\\1">\\1</a>',
        'Hyperlink (implied)',
        "Maybe try looking on [url]http://google.com[/url]",
        'link'],
    # 
    # TODO: fix automatic links
    #
    # 'Link (Automatic)': [
    #   r"http:\/\/(.*?)[^<\/a>]/,
    #   '<a href="\\1">\\1</a>',
    #   'Hyperlink (automatic)',
    #   nil,
    #   'link'],
    'Image (Resized)': [
        r"\[img(:.+)? size=(['\"]?)(\d+)x(\d+)\2\](.*?)\[\/img\1?\]",
        '<img src="\\5" style="width: \\3px; height: \\4px;" />',
        'Display an image with a set width and height', 
        '[img size=96x96]http://www.google.com/intl/en_ALL/images/logo.gif[/img]',
        'image'],
    'Image (Alternative)': [
        r"\[img=([^\[\]].*?)\.(" + "|".join(PERMITTED_IMAGE_FORMATS) + r")\]",
        '<img src="\\1.\\2" alt="" />',
        'Display an image (alternative format)', 
        '[img=http://myimage.com/logo.gif]',
        'image'],
    'Image': [
        r"\[img(:.+)?\]([^\[\]].*?)\.(" + "|".join(PERMITTED_IMAGE_FORMATS) + r")\[\/img\1?\]",
        '<img src="\\2.\\3" alt="" />',
        'Display an image',
        'Check out this crazy cat: [img]http://catsweekly.com/crazycat.jpg[/img]',
        'image'],   
    'YouTube': [
        r"\[youtube\](.*?)\?v=([\w\d\-]+).*\[\/youtube\]",
        # '<object width="400" height="330"><param name="movie" value="http://www.youtube.com/v/\\2"></param><param name="wmode" value="transparent"></param><embed src="http://www.youtube.com/v/\\2" type="application/x-shockwave-flash" wmode="transparent" width="400" height="330"></embed></object>',
        '<object width="320" height="265"><param name="movie" value="http://www.youtube.com/v/\\2"></param><param name="allowFullScreen" value="true"></param><param name="allowscriptaccess" value="always"></param><embed src="http://www.youtube.com/v/\\2" type="application/x-shockwave-flash" allowscriptaccess="always" allowfullscreen="true" width="320" height="265"></embed></object>',
        'Display a video from YouTube.com', 
        '[youtube]http://youtube.com/watch?v=E4Fbk52Mk1w[/youtube]',
        'video'],
    'YouTube (Alternative)': [
        r"\[youtube\](.*?)\/v\/([\w\d\-]+)\[\/youtube\]",
        # '<object width="400" height="330"><param name="movie" value="http://www.youtube.com/v/\\2"></param><param name="wmode" value="transparent"></param><embed src="http://www.youtube.com/v/\\2" type="application/x-shockwave-flash" wmode="transparent" width="400" height="330"></embed></object>',
        '<object width="320" height="265"><param name="movie" value="http://www.youtube.com/v/\\2"></param><param name="allowFullScreen" value="true"></param><param name="allowscriptaccess" value="always"></param><embed src="http://www.youtube.com/v/\\2" type="application/x-shockwave-flash" allowscriptaccess="always" allowfullscreen="true" width="320" height="265"></embed></object>',
        'Display a video from YouTube.com (alternative format)', 
        '[youtube]http://youtube.com/watch/v/E4Fbk52Mk1w[/youtube]',
        'video'],
    'Google Video': [
        r"\[gvideo\](.*?)\?docid=([-]{0,1}\d+).*\[\/gvideo\]",
        '<embed style="width:400px; height:326px;" id="VideoPlayback" type="application/x-shockwave-flash" src="http://video.google.com/googleplayer.swf?docId=\\2" flashvars=""> </embed>',
        'Display a video from Google Video', 
        '[gvideo]http://video.google.com/videoplay?docid=-2200109535941088987[/gvideo]',
        'video'],
    'Email': [
        r"\[email(:.+)?\](.+)\[\/email\1?\]",
        '<a href="mailto:\\2">\\2</a>',
        'Link to email address',
        '[email]wadus@wadus.com[/email]',
        'email'],
}

##
# End of File
##
