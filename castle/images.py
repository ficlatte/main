
#coding: utf-8
#This file is part of Ficlatté.
#Copyright (C) 2015 Paul Robertson
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of version 3 of the GNU Affero General Public
#    License as published by the Free Software Foundation
#    
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.conf import settings
from castle.models import *
import os
import sys
import subprocess

#-----------------------------------------------------------------------------
# 'resource' module doesn't exist on all platforms, so catch and ignore failure
try:
    import resource
except ImportError:
    pass

#-----------------------------------------------------------------------------
def setlimits():
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (1, 1))     # Limit CPU time
        #resource.setrlimit(resource.RLIMIT_NPROC, (10, 10)) # Limit child processes
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))    # Prevent core dump files
    except NameError:
        # Import of "resource" module failed
        # but we can get by without it
        pass

#-----------------------------------------------------------------------------
def run_convert_avatar(profile):
    id = str(profile.id)
    path = getattr(settings, 'AVATAR_PATH', None)
    src_fnm = path + '/tmp/' + id
    dst_fnm = path + '/avatar/' + id + '.png'

    p = subprocess.Popen(["/usr/bin/convert", src_fnm, '-resize', '113x113', '-limit', 'thread', '1', dst_fnm], preexec_fn=setlimits)
    p.wait()
    return p.returncode

#-----------------------------------------------------------------------------
def run_convert_icon(profile):
    id = str(profile.id)
    path = getattr(settings, 'AVATAR_PATH', None)
    src_fnm = path + '/tmp/' + id
    dst_fnm = path + '/icon/' + id + '.png'

    p = subprocess.Popen(["/usr/bin/convert", src_fnm, '-resize', '46x46', '-limit', 'thread', '1', dst_fnm], preexec_fn=setlimits)
    p.wait()
    print "return code is",p.returncode
    return p.returncode

#-----------------------------------------------------------------------------
def convert_avatars(profile):
    # non-zero return code indicates failure
    failure = run_convert_avatar(profile)
    if (not failure):
        failure = run_convert_icon(profile)
    return failure

#-----------------------------------------------------------------------------
