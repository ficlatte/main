from django.http import HttpResponse
from bbcode.settings import TAGS
from bbcode.util import to_html
def test_root(request):
    header = "<html><body>"
    footer = "</body</html>"
    html = r""
    for x in TAGS:
        t = TAGS[x]
        html += r"<div>"
        html += r"<span>%s:</span><br />" % t[2]
        html += r"<span>BBCode:</span><blockquote>"
        html += r"%s" % to_html(t[3], {}, True, 'enable')
        html += r"</blockquote><span>HTML:</span><blockquote>"
        html += r"%s" % to_html(to_html(t[3]), {}, True, 'enable')
        html += r"</blockquote><span>Result:</span><blockquote>"
        html += r"%s" % to_html(t[3])
        html += r"</div>"
    return HttpResponse(header + html + footer)
