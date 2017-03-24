
#coding: utf-8
#This file is part of Ficlatté.
#Copyright © 2015-2017 Paul Robertson, Jim Stitzel and Shu Sam Chen
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of version 3 of the GNU Affero General Public
#    License as published by the Free Software Foundation
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django import forms
from django.core.exceptions import ValidationError
from castle.models import Challenge
from datetimewidget.widgets import DateWidget

class AvatarUploadForm(forms.Form):
    image_file = forms.FileField(label='image file')
    
class ChallengeDateForm(forms.ModelForm):
    
    class Meta:
        model = Challenge
        fields = ('title', 'stime', 'etime', 'body',)
        dateTimeOptions = {
            'format': 'YYYY-MM-DD',
            'autoclose': True
        }
        widgets = {
            'stime': DateWidget(attrs={'id':"challenge_stime"}, usel10n = True, bootstrap_version=3),
            'etime': DateWidget(attrs={'id':"challenge_etime"}, usel10n = True, bootstrap_version=3)
        }
