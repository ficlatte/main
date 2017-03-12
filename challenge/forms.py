from django import forms
from django.core.exceptions import ValidationError
from castle.models import Challenge
from datetimewidget.widgets import DateWidget

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
