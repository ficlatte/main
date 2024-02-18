#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# django-bbcode: test.py
##

import sys
sys.path.insert(0,'..')

from bbcode.settings import TAGS
from bbcode import util as bbcode
import unittest

class BBCodeTestCase(unittest.TestCase):
    def test_strong(self):
        self.assertEquals(
            '<strong>simple</strong>',
            bbcode.to_html('[b]simple[/b]'))
        self.assertEquals(
            '<strong>simple</strong>',
            bbcode.to_html('[b:7a9ca2c5c3]simple[/b:7a9ca2c5c3]'))
        self.assertEquals(
            "<strong>line 1<br />line 2</strong>",
            bbcode.to_html("[b:7a9ca2c5c3]line 1\nline 2[/b:7a9ca2c5c3]"))
        self.assertEquals(
            '<strong>1. text 1:</strong> text 2<br /><strong>2. text 3</strong>',
            bbcode.to_html("[b:post_uid0]1. text 1:[/b:post_uid0] text 2\n[b:post_uid0]2. text 3[/b:post_uid0]"))

    def test_em(self):
        self.assertEquals(
            '<em>simple</em>',
            bbcode.to_html('[i]simple[/i]'))
        self.assertEquals(
            '<em>simple</em>',
            bbcode.to_html('[i:7a9ca2c5c3]simple[/i:7a9ca2c5c3]'))
        self.assertEquals(
            "<em>line 1<br />line 2</em>",
            bbcode.to_html("[i:7a9ca2c5c3]line 1\nline 2[/i:7a9ca2c5c3]"))

    def test_u(self):
        self.assertEquals(
            '<u>simple</u>',
            bbcode.to_html('[u]simple[/u]'))
        self.assertEquals(
            '<u>simple</u>',
            bbcode.to_html('[u:7a9ca2c5c3]simple[/u:7a9ca2c5c3]'))
        self.assertEquals(
            "<u>line 1<br />line 2</u>",
            bbcode.to_html("[u:7a9ca2c5c3]line 1\nline 2[/u:7a9ca2c5c3]"))

    def test_del(self):
        self.assertEquals(
            '<del>simple</del>',
            bbcode.to_html('[del]simple[/del]'))
        self.assertEquals(
            '<del>simple</del>',
            bbcode.to_html('[del:7a9ca2c5c3]simple[/del:7a9ca2c5c3]'))
        self.assertEquals(
            '<del>simple</del>',
            bbcode.to_html('[s]simple[/s]'))
        self.assertEquals(
            '<del>simple</del>',
            bbcode.to_html('[s:7a9ca2c5c3]simple[/s:7a9ca2c5c3]'))

    def test_ins(self):
        self.assertEquals(
            '<ins>simple</ins>',
            bbcode.to_html('[ins]simple[/ins]'))
        self.assertEquals(
            '<ins>simple</ins>',
            bbcode.to_html('[ins:7a9ca2c5c3]simple[/ins:7a9ca2c5c3]'))

    def test_code(self):
        self.assertEquals(
            '<code>simple</code>',
            bbcode.to_html('[code]simple[/code]'))
        self.assertEquals(
            '<code>simple</code>',
            bbcode.to_html('[code:7a9ca2c5c3]simple[/code:7a9ca2c5c3]'))
        self.assertEquals(
            "<code>var bxi = 0;<br />//Holds current speed of scrolling menu</code>",
            bbcode.to_html("[code:1:91cbdd72b7]var bxi = 0;\n//Holds current speed of scrolling menu[/code:1:91cbdd72b7]"))

    def test_size(self):
        self.assertEquals(
            '<span style="font-size: 32px;">12px Text</span>',
            bbcode.to_html('[size=32]12px Text[/size]'))
  
    def test_color(self):
        self.assertEquals(
            '<span style="color: red;">Red Text</span>',
            bbcode.to_html('[color=red]Red Text[/color]'))
        self.assertEquals(
            '<span style="color: #ff0023;">Hex Color Text</span>',
            bbcode.to_html('[color=#ff0023]Hex Color Text[/color]'))
        self.assertEquals(
            '<span style="color: #B23803;">text</span>',
            bbcode.to_html('[color=#B23803:05d7c56429]text[/color:05d7c56429]'))

    def test_ordered_list(self):
        self.assertEquals(
            '<ol><li>item 1</li><li>item 2</li></ol>',
            bbcode.to_html('[ol][li]item 1[/li][li]item 2[/li][/ol]'))
        self.assertEquals(
            '<ol><li>item 1</li><li>item 2</li></ol>',
            bbcode.to_html('[ol][*]item 1[*]item 2[/ol]'))

    def test_unordered_list(self):
        self.assertEquals(
            '<ul><li>item 1</li><li>item 2</li></ul>',
            bbcode.to_html('[ul][li]item 1[/li][li]item 2[/li][/ul]'))
        self.assertEquals(
            '<ul><li>item 1</li><li>item 2</li></ul>',
            bbcode.to_html('[ul][*]item 1[*]item 2[/ul]'))

    def test_list_unordered(self):
        self.assertEquals(
            '<ul><li>item 1</li><li>item 2</li></ul>',
            bbcode.to_html('[list][li]item 1[/li][li]item 2[/li][/list]'))
        self.assertEquals(
            '<ul><li>item 1</li><li>item 2</li></ul>',
            bbcode.to_html('[list:7a9ca2c5c3][li]item 1[/li][li]item 2[/li][/list:o:7a9ca2c5c3]'))
        self.assertEquals(
            '<ul><li>item 1</li><li>item 2</li></ul><ul><li>item 3</li><li>item 4</li></ul>',
            bbcode.to_html('[list:7a9ca2c5c3][li]item 1[/li][li]item 2[/li][/list:o:7a9ca2c5c3][list:7a9ca2c5c3][li]item 3[/li][li]item 4[/li][/list:o:7a9ca2c5c3]'))
        self.assertEquals(
            '<ul><li>item 1</li><li>item 2</li></ul><ul><li>item 3</li><li>item 4</li></ul><ul><li>item 5</li><li>item 6</li></ul><ul><li>item 7</li><li>item 8</li></ul>',
            bbcode.to_html('[list:7a9ca2c5c3][li]item 1[/li][li]item 2[/li][/list:o:7a9ca2c5c3][list:7a9ca2c5c3][li]item 3[/li][li]item 4[/li][/list:o:7a9ca2c5c3][list:7a9ca2c5c3][li]item 5[/li][li]item 6[/li][/list:o:7a9ca2c5c3][list:7a9ca2c5c3][li]item 7[/li][li]item 8[/li][/list:o:7a9ca2c5c3]'))

    def test_list_unordered_alternative(self):
        self.assertEquals(
            '<li>item1</li><li>item2</li>',
            bbcode.to_html('[*:asdf]item1[*:asdf]item2'))
        self.assertEquals(
            '<ul><li>item1</li><li>item2</li></ul>',
            bbcode.to_html('[list:5d7cf5560a][*]item1[*]item2[/list:u:5d7cf5560a]'))
        self.assertEquals(
            '<ul><li>item1</li><li>item2</li></ul>',
            bbcode.to_html('[list:5d7cf5560a][*:5d7cf5560a]item1[*:5d7cf5560a]item2[/list:u:5d7cf5560a]'))

    def test_list_ordered_numerically(self):
        self.assertEquals(
            '<ol><li>item 1</li><li>item 2</li></ol>',
            bbcode.to_html('[list=1][li]item 1[/li][li]item 2[/li][/list]'))
        self.assertEquals(
            '<ol><li>item 1</li><li>item 2</li></ol>',
            bbcode.to_html('[list=1:7a9ca2c5c3][li]item 1[/li][li]item 2[/li][/list:7a9ca2c5c3]'))

    def test_list_ordered_alphabetically(self):
        self.assertEquals(
            '<ol sytle="list-style-type: lower-alpha;"><li>item 1</li><li>item 2</li></ol>',
            bbcode.to_html('[list=a][li]item 1[/li][li]item 2[/li][/list]'))
        self.assertEquals(
            '<ol sytle="list-style-type: lower-alpha;"><li>item 1</li><li>item 2</li></ol>',
            bbcode.to_html('[list=a:7a9ca2c5c3][li]item 1[/li][li]item 2[/li][/list:o:7a9ca2c5c3]'))

    def test_two_lists(self):
        self.assertEquals(
            '<ul><li>item1</li><li>item2</li></ul><ul><li>item1</li><li>item2</li></ul>',
            bbcode.to_html('[list:5d7cf5560a][*:5d7cf5560a]item1[*:5d7cf5560a]item2[/list:u:5d7cf5560a][list:5d7cf5560a][*:5d7cf5560a]item1[*:5d7cf5560a]item2[/list:u:5d7cf5560a]'))

    def test_definition_list_term_definition(self):
        self.assertEquals(
            '<dl><dt>term 1</dt><dd>definition 1</dd><dt>term 2</dt><dd>definition 2</dd></dl>',
            bbcode.to_html('[dl][dt]term 1[/dt][dd]definition 1[/dd][dt]term 2[/dt][dd]definition 2[/dd][/dl]'))

    def test_quote(self):
        self.assertEquals(
            '<fieldset><blockquote>quoting</blockquote></fieldset>',
            bbcode.to_html('[quote]quoting[/quote]'))
        self.assertEquals(
            '<fieldset><blockquote>quoting</blockquote></fieldset>',
            bbcode.to_html(bbcode.to_html('[quote]quoting[/quote]'), {}, False, 'disable'))
        self.assertEquals(
            '<fieldset><legend>black</legend><blockquote>si el niño hubiera sido de "penalty" le hubieran llamado <strong>system Error</strong>!!! :)</blockquote></fieldset>',
            bbcode.to_html("[quote:7a9ca2c5c3=\"black\"]si el niño hubiera sido de \"penalty\" le hubieran llamado [b:7a9ca2c5c3]system Error[/b:7a9ca2c5c3]!!! :)[/quote:7a9ca2c5c3]"))
        self.assertEquals(
            '<fieldset><legend>black</legend><blockquote>si el niño hubiera sido de "penalty" le hubieran llamado <strong>system Error</strong>!!! :)</blockquote></fieldset>',
            bbcode.to_html(bbcode.to_html("[quote:7a9ca2c5c3=\"black\"]si el niño hubiera sido de \"penalty\" le hubieran llamado [b:7a9ca2c5c3]system Error[/b:7a9ca2c5c3]!!! :)[/quote:7a9ca2c5c3]"), {}, False, 'disable'))
        self.assertEquals(
            '<fieldset><legend>Who</legend><blockquote>said that</blockquote></fieldset>',
            bbcode.to_html('[quote=Who]said that[/quote]'))
        self.assertEquals(
            '<fieldset><legend>Who</legend><blockquote>said that</blockquote></fieldset>',
            bbcode.to_html(bbcode.to_html('[quote=Who]said that[/quote]'), {}, False, 'disable'))

    def test_double_quote(self):
        self.assertEquals(
            '<fieldset><legend>Kitten</legend><blockquote><fieldset><legend>creatiu</legend><blockquote>f1</blockquote></fieldset>f2</blockquote></fieldset>',
            bbcode.to_html(bbcode.to_html('[quote:26fe26a6a9="Kitten"][quote:26fe26a6a9="creatiu"]f1[/quote:26fe26a6a9]f2[/quote:26fe26a6a9]'), {}, False, 'disable'))

    def test_link(self):
        self.assertEquals(
            '<a href="http://google.com">Google</a>',
            bbcode.to_html('[url=http://google.com]Google[/url]'))
        self.assertEquals(
            '<a href="http://google.com">http://google.com</a>',
            bbcode.to_html('[url]http://google.com[/url]'))
        self.assertEquals(
            '<a href="http://www.altctrlsupr.com/dmstk/kdd070803/00.html"> ABRIR ALBUM </a>',
            bbcode.to_html('[URL=http://www.altctrlsupr.com/dmstk/kdd070803/00.html] ABRIR ALBUM [/URL]'))
        self.assertEquals(
            '<a href="http://www.altctrlsupr.com/dmstk/kdd070803/00.html"> ABRIR<br />ALBUM </a>',
            bbcode.to_html("[URL=http://www.altctrlsupr.com/dmstk/kdd070803/00.html] ABRIR\nALBUM [/URL]"))
        self.assertEquals(
            '<a href="http://www.urimalet.com/cadaverex.mp3">aha</a>',
            bbcode.to_html("[URL=http://www.urimalet.com/cadaverex.mp3]aha[/URL]"))

    def test_image(self):
        self.assertEquals(
            '<img src="http://zoople/hochzeit.png" alt="" />',
            bbcode.to_html('[img]http://zoople/hochzeit.png[/img]'))
        self.assertEquals(
            '<img src="http://zoople/hochzeit.png" alt="" />',
            bbcode.to_html('[img=http://zoople/hochzeit.png]'))
        self.assertEquals(
            '<img src="http://zoople/hochzeit.png" style="width: 95px; height: 96px;" />',
            bbcode.to_html('[img size=95x96]http://zoople/hochzeit.png[/img]'))
        self.assertEquals(
            '<img src="http://zoople/hochzeit.png" alt="" />',
            bbcode.to_html('[img:7a9ca2c5c3]http://zoople/hochzeit.png[/img:7a9ca2c5c3]'))
        self.assertEquals(
            '<img src="http://zoople/hochzeit.png" style="width: 95px; height: 96px;" />',
            bbcode.to_html('[img:7a9ca2c5c3 size=95x96]http://zoople/hochzeit.png[/img:7a9ca2c5c3]'))
        self.assertEquals(
            '<img src="http://www.marcodigital.com/sitanddie/sitanddiepequeÃ±o.jpg" alt="" />',
            bbcode.to_html('[img:post_uid0]http://www.marcodigital.com/sitanddie/sitanddiepequeÃ±o.jpg[/img:post_uid0]'))

    def test_youtube(self):
        # Uncomment below if using 4:3 format youtube video embed
        # self.assertEquals(
        #     '<object width="320" height="265"><param name="movie" value="http://www.youtube.com/v/E4Fbk52Mk1w"></param><param name="wmode" value="transparent"></param><embed src="http://www.youtube.com/v/E4Fbk52Mk1w" type="application/x-shockwave-flash" wmode="transparent" width="320" height="265"></embed></object>',
        #     bbcode.to_html('[youtube]http://youtube.com/watch?v=E4Fbk52Mk1w[/youtube]'))
        self.assertEquals(
            '<object width="320" height="265"><param name="movie" value="http://www.youtube.com/v/E4Fbk52Mk1w"></param><param name="allowFullScreen" value="true"></param><param name="allowscriptaccess" value="always"></param><embed src="http://www.youtube.com/v/E4Fbk52Mk1w" type="application/x-shockwave-flash" allowscriptaccess="always" allowfullscreen="true" width="320" height="265"></embed></object>',
            bbcode.to_html('[youtube]http://youtube.com/watch?v=E4Fbk52Mk1w[/youtube]'))

    def test_google_video(self):
        self.assertEquals(
            '<embed style="width:400px; height:326px;" id="VideoPlayback" type="application/x-shockwave-flash" src="http://video.google.com/googleplayer.swf?docId=-2200109535941088987" flashvars=""> </embed>',
            bbcode.to_html('[gvideo]http://video.google.com/videoplay?docid=-2200109535941088987[/gvideo]'))

    def test_email(self):
        self.assertEquals(
            '<a href="mailto:wadus@wadus.com">wadus@wadus.com</a>',
            bbcode.to_html('[email]wadus@wadus.com[/email]'))

    def test_html_escaping(self):
        self.assertEquals(
            "<strong>&lt;i&gt;foobar&lt;/i&gt;</strong>",
            bbcode.to_html('[b]<i>foobar</i>[/b]'))
        self.assertEquals(
            "<strong><i>foobar</i></strong>",
            bbcode.to_html('[b]<i>foobar</i>[/b]', {}, False))
        self.assertEquals(
            "1 is &lt; 2",
            bbcode.to_html('1 is < 2'))
        self.assertEquals(
            "1 is < 2",
            bbcode.to_html('1 is < 2', {}, False))
        self.assertEquals(
            "2 is &gt; 1",
            bbcode.to_html('2 is > 1'))
        self.assertEquals(
            "2 is > 1",
            bbcode.to_html('2 is > 1', {}, False))

    def test_disable_tags(self):
        self.assertEquals(
            "[b]foobar[/b]",
            bbcode.to_html("[b]foobar[/b]", {}, True, 'disable', 'bold'))
        self.assertEquals(
            "[b]<em>foobar</em>[/b]",
            bbcode.to_html("[b][i]foobar[/i][/b]", {}, True, 'disable', 'bold'))
        self.assertEquals(
            "[b][i]foobar[/i][/b]",
            bbcode.to_html("[b][i]foobar[/i][/b]", {}, True, 'disable', 'bold', 'italics'))

    def test_enable_tags(self):
        self.assertEquals(
            "<strong>foobar</strong>",
            bbcode.to_html("[b]foobar[/b]", {}, True, 'enable', 'bold'))
        self.assertEquals(
            "<strong>[i]foobar[/i]</strong>",
            bbcode.to_html("[b][i]foobar[/i][/b]", {}, True, 'enable', 'bold'))
        self.assertEquals(
            "<strong><em>foobar</em></strong>",
            bbcode.to_html("[b][i]foobar[/i][/b]", {}, True, 'enable', 'bold', 'italics'))

#    def test_to_html_bang_method(self):
#        foo = "[b]foobar[/b]"
#        self.assertEquals("<strong>foobar</strong>", foo.bbcode_to_html!)
#        self.assertEquals("<strong>foobar</strong>", foo)

    def test_self_tag_list(self):
        self.assertEquals(30, len(TAGS))

    def test_redefinition_of_tag_html(self):
        mydef = {
            'Quote': [
                r"\[quote(:.*)?=\"?(.*?)\"?\](.*?)\[/quote\1?\]",
                '<div class="quote"><p><cite>\\2</cite></p><blockquote>\\3</blockquote></div>',
                'Quote with citation',
                None,
                'quote'],
            'Image (Resized)': [
                r"\[img(:.+)? size=(['\"]?)(\d+)x(\d+)\2\](.*?)\[/img\1?\]",
                '<div class="post_image"><img src="\\5" style="width: \\3px; height: \\4px;" /></div>',
                'Display an image with a set width and height', 
                '[img size=96x96]http://www.google.com/intl/en_ALL/images/logo.gif[/img]',
                'image'],
            'Image (Alternative)': [
                r"\[img=([^\[\]].*?)\.(png|bmp|jpg|gif|jpeg)\]",
                '<div class="post_image"><img src="\\1.\\2" alt="" /></div>',
                'Display an image (alternative format)', 
                '[img=http://myimage.com/logo.gif]',
                'image'],
            'Image': [
                r"\[img(:.+)?\]([^\[\]].*?)\.(png|bmp|jpg|gif|jpeg)\[/img\1?\]",
                '<div class="post_image"><img src="\\2.\\3" alt="" /></div>',
                'Display an image',
                'Check out this crazy cat: [img]http://catsweekly.com/crazycat.jpg[/img]',
                'image'],
        }
        self.assertEquals(
            '<div class="quote"><p><cite>Who</cite></p><blockquote>said that</blockquote></div>',
            bbcode.to_html('[quote=Who]said that[/quote]', mydef))
        self.assertEquals(
            '<div class="quote"><p><cite>flandepan</cite></p><blockquote>hola</blockquote></div>',
            bbcode.to_html('[quote:0fc8a224d2="flandepan"]hola[/quote:0fc8a224d2]', mydef))
        self.assertEquals(
            '<div class="post_image"><img src="http://zoople/hochzeit.png" alt="" /></div>',
            bbcode.to_html('[img]http://zoople/hochzeit.png[/img]', mydef))

    def test_multiple_tag_test(self):
        self.assertEquals(
            "<strong>bold</strong><em>italic</em><u>underline</u><fieldset><blockquote>quote</blockquote></fieldset><a href=\"foobar\">link</a>",
            bbcode.to_html("[b]bold[/b][i]italic[/i][u]underline[/u][quote]quote[/quote][url=foobar]link[/url]"))
        self.assertEquals(
            "<strong>bold</strong><em>italic</em><u>underline</u><fieldset><blockquote>quote</blockquote></fieldset><a href=\"foobar\">link</a>",
            bbcode.to_html("[b]bold[/b][i]italic[/i][u]underline[/u][quote]quote[/quote][url=foobar]link[/url]", {}, True, 'enable', 'bold', 'italics', 'underline', 'link', 'quote'))

    def test_no_ending_tag(self):
        self.assertEquals(
            "this [b]should not be bold",
            bbcode.to_html("this [b]should not be bold"))

    def test_no_start_tag(self):
        self.assertEquals(
            "this should not be bold[/b]",
            bbcode.to_html("this should not be bold[/b]"))

    def test_different_start_and_ending_tags(self):
        self.assertEquals(
            "this [b]should not do formatting[/i]",
            bbcode.to_html("this [b]should not do formatting[/i]"))

if __name__ == '__main__':
    unittest.main()

##
# End of File
##
