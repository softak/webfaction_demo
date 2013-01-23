import commonware
from session_csrf import anonymous_csrf
from django.core.urlresolvers import reverse
from django.conf import settings
from django.shortcuts import redirect, render
from django.db import transaction
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth import views as auth_views
from django.contrib import auth
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from facebook import views as facebook_views
from accounts.models import EmailConfirmation, PasswordReset
from accounts.forms import SignupForm, ConfirmationResendForm, LoginForm, \
                           PasswordResetForm, FacebookVerificationForm

log = commonware.log.getLogger('sd')


@anonymous_csrf
@csrf_protect
def facebook_verification(request):
    request.session.set_expiry(0)
    return facebook_views.verification(request,
            template_name='accounts/facebook_verification.j.html',
            authentication_form=FacebookVerificationForm,
            redirect_url=reverse('pages.home'))


@anonymous_csrf
@csrf_protect # TODO replace with "Not allowed for signed-in users"
def login(request):
    if request.method == 'POST':
        if request.POST.get('remember_me', None):
            request.session.set_expiry(None) # Resets to default
        else:
            request.session.set_expiry(0)
    return auth_views.login(request,
        template_name='accounts/login.j.html',
        authentication_form=LoginForm)


def logout(request):
    return auth_views.logout(request,
        next_page='/')


@anonymous_csrf
@csrf_protect # TODO replace with "Not allowed for signed-in users"
@transaction.commit_on_success
def signup(request):
    if request.method == 'POST':
        form = SignupForm(request, data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('accounts.signup_done')
    else:
        form = SignupForm(request)
    return render(request, 'accounts/signup.j.html', {
        'form': form
    })


@never_cache
@transaction.commit_on_success
def confirm_email(request, key):
    try:
        confirmation = EmailConfirmation.objects.get(key=key)
        user = confirmation.user
    except (EmailConfirmation.DoesNotExist):
        user = None

    if user is not None and confirmation.confirm(key):
        user.email = confirmation.email
        user.is_active = True
        user.save()
        user.backend = settings.AUTHENTICATION_BACKENDS[0]
        auth.login(request, user)
        return redirect('pages.home')
    else:
        return render(request, 'accounts/confirm_email_invalid.j.html')


@anonymous_csrf
@csrf_protect
@transaction.commit_on_success
def confirmation_resend(request):
    if request.method == 'POST':
        form = ConfirmationResendForm(request, request.POST)
        if form.is_valid():
            form.save()
            return redirect('accounts.confirmation_resend_done')
    else:
        form = ConfirmationResendForm(request)
    return render(request, 'accounts/confirmation_resend.j.html', {
        'form': form
    })


@anonymous_csrf
@csrf_protect
@transaction.commit_on_success
def password_reset(request):
    if request.method == 'POST':
        form = PasswordResetForm(request, request.POST)
        if form.is_valid():
            form.save()
            return redirect('accounts.password_reset_sent')
    else:
        form = PasswordResetForm(request)
    return render(request, 'accounts/password_reset.j.html', {
        'form': form
    })


@anonymous_csrf
@csrf_protect
@transaction.commit_on_success
def password_reset_confirm(request, key):
    try:
        reset = PasswordReset.objects.get(key=key)
        user = reset.user
    except PasswordReset.DoesNotExist:
        user = None

    if user is not None:
        validlink = True
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                reset.delete()
                return redirect('accounts.password_reset_done')
        else:
            form = SetPasswordForm(None)
    else:
        validlink = False
        form = None

    return render(request, 'accounts/password_reset_confirm.j.html', {
        'validlink': validlink,
        'form': form
    })


@csrf_protect
def password_change(request):
    return auth_views.password_change(request,
        template_name='accounts/password_change.j.html',
        post_change_redirect=reverse('accounts.password_change_done'))

def password_change_done(request):
    return auth_views.password_change_done(request,
        template_name='accounts/password_change_done.j.html')
