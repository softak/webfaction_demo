import uuid
from datetime import datetime
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django import forms
from django.forms.extras.widgets import SelectDateWidget
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from accounts.models import EmailConfirmation, PasswordReset
from profiles.models import Profile


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label=_('E-mail'),
        max_length=75)
    password = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput,
        help_text=mark_safe(
            _('<a href="/password_reset/">Forgot your password?</a>')))
    remember_me = forms.BooleanField(
        label=_('Remember Me'),
        help_text=_('This keeps you logged in for 2 weeks.'),
        required=False)


class FacebookVerificationForm(LoginForm):
    remember_me = None

    def __init__(self, *args, **kwargs):
        anonymous_user = kwargs.pop('anonymous_user', False)
        if anonymous_user:
            initial = kwargs.pop('initial', {})
            initial['username'] = anonymous_user.email
            kwargs['initial'] = initial
        super(FacebookVerificationForm, self).__init__(*args, **kwargs)


class SignupForm(forms.ModelForm):
    first_name = forms.CharField(
        label=_('First name'),
        required=True)
    last_name = forms.CharField(
        label=_('Last name'),
        required=True)
    birthday = forms.DateField(
        label=_('Birthday'),
        widget=SelectDateWidget(years=range(datetime.now().year, 1899,-1)))
    email = forms.EmailField(
        label=_("E-mail"),
        max_length=75)
    password = forms.CharField(
        label=_("Password"), 
        widget=forms.PasswordInput)

    class Meta:
        model = Profile
        fields = ('first_name', 'last_name', 'birthday', 'sex', 'email', 'password')

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(SignupForm, self).__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data['email']
        if (User.objects.filter(email__iexact=email).exists() or
            EmailConfirmation.objects.filter(email__iexact=email).exists()):
            raise forms.ValidationError(
                _('This e-mail address is already in use.'))
        return email

    def save(self):
        user = User(
            username = str(uuid.uuid4())[:30],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            is_active=False)
        user.set_password(self.cleaned_data['password'])
        user.save()

        profile = super(SignupForm, self).save(commit=False)
        profile.user = user
        profile.save()

        confirmation = EmailConfirmation.objects.create(
            user=user,
            email=self.cleaned_data['email'])
        confirmation.send(self.request, update_timestamp=False)

        return user


def total_minutes(td):
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6 / 60


class ConfirmationResendForm(forms.Form):
    email = forms.EmailField(
        label=_('E-mail'),
        max_length=75,
        widget=forms.TextInput(attrs={'size': 30}))

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(ConfirmationResendForm, self).__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            self.confirmation = EmailConfirmation.objects.get(email__iexact=email)
        except EmailConfirmation.DoesNotExist:
            raise forms.ValidationError(_('There is no user with the given e-mail address.'))
        return email

    def clean(self):
        if 'email' in self.cleaned_data:
            confirmation = self.confirmation
            last_sent = confirmation.last_sent
            if (last_sent is not None and
                total_minutes(datetime.utcnow() - last_sent) <
                    settings.CONFIRMATION_RESEND_TIMEOUT):
                raise forms.ValidationError(_('You do that too often. Please try again later.'))
        return self.cleaned_data

    def save(self):
        self.confirmation.send(self.request)


class PasswordResetForm(forms.Form):
    email = forms.EmailField(
        label=_("E-mail"), 
        max_length=75, 
        widget=forms.TextInput(attrs={'size':30}))

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(PasswordResetForm, self).__init__(*args, **kwargs)

    def clean_email(self):
        """
        Validates that an active user exists with the given e-mail address.
        """
        email = self.cleaned_data["email"]
        try:
            self.user = User.objects.get(email__iexact=email, is_active=True)
        except User.DoesNotExist:
            raise forms.ValidationError(_("That e-mail address doesn't have an associated user account."))
        return email

    def clean(self):
        if 'email' in self.cleaned_data:
            user = self.user
            resets = user.password_resets.all()
            if resets.exists():
                last_reset = resets.order_by('-last_sent')[0]
                if total_minutes(datetime.utcnow() - last_reset.last_sent) < settings.EMAIL_RESEND_INTERVAL:
                    raise forms.ValidationError(_('You do that too often. Please try again later.'))
        return self.cleaned_data

    def save(self):
        user = self.user
        reset = PasswordReset.objects.create(user=user)
        reset.send(self.request)
        return reset
