
#coding: utf-8
#This file is part of Ficlatté.
#Copyright (C) 2015-2017 Paul Robertson, Jim Stitzel, & Shu Sam Chen
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
from django.shortcuts import render
import string
import random

# Create your views here.
def the_pit(request):
    
    # Provide a never-ending stack of random links
    refs = []
    for a in range(32):
        s = u''.join(random.SystemRandom().choice(string.ascii_lowercase+string.digits) for _ in range(32))
        refs.append(s)
    
    # Build context and render page
    context = {
        'refs'      : refs
    }

    return render(request, 'the_pit/the_pit.html', context)
