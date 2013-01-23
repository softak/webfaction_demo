import commonware
import datetime
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.forms.extras.widgets import SelectDateWidget
from utils.widgets import BootstrapCheckboxSelectMultiple

from profiles.models import Profile

log = commonware.log.getLogger('sd')


class ProfileEditForm(forms.ModelForm):
    first_name = forms.CharField(
        label=_('First name'),
        required=True)
    last_name = forms.CharField(
        label=_('Last name'),
        required=True)
    birthday = forms.DateField(
        label=_('Birthday'),
        widget=SelectDateWidget(years=range(datetime.datetime.now().year, 1899,-1)))

    def __init__(self, *args, **kwargs):
        super(ProfileEditForm, self).__init__(*args, **kwargs)
        self.fields['avatar'].widget = forms.FileInput()

    class Meta:
        model = Profile
        fields = ('first_name', 'last_name', 'sex', 'birthday', 'avatar',)

class GeoLocationPointForm(forms.Form):
    lat = forms.FloatField(required=True, min_value=-90,  max_value=90)
    lng = forms.FloatField(required=True, min_value=-180, max_value=180)

    def getLat(self):
        return self.cleaned_data.get('lat')

    def getLng(self):
        return self.cleaned_data.get('lng')


class FacebookNotificationOptionsForm(forms.Form):

    EVENT_CREATE_PURCHASE = 1
    EVENT_JOIN_PURCHASE = 2

    EVENT_CHOICES = (
        (EVENT_CREATE_PURCHASE, _('I create new social purchase')),
        (EVENT_JOIN_PURCHASE, _('I join someone\'s social purchase'))
    )

    events = forms.MultipleChoiceField(label=_('Notify my friends when'),
        choices=EVENT_CHOICES,
        widget=BootstrapCheckboxSelectMultiple)
