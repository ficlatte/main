#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# django-bbcode: templatetags/bbcode.py
##

from django import template
from bbcode import util as bbcode

register = template.Library()

def render_bbcode(value):
    return bbcode.to_html(value)

register.filter('render_bbcode', render_bbcode)

##
# End of File
##
