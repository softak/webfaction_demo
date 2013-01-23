from django.conf.urls.defaults import *
from django.views.generic import TemplateView
from accounts import views


urlpatterns = patterns('',

    # Logging in/out
    url(r'^login/$', views.login,
        name='accounts.login'),
    url(r'^logout/$', views.logout,
        name='accounts.logout'),

    # Signup
    url(r'^signup/$', views.signup,
        name='accounts.signup'),
    url(r'^signup/done/$', TemplateView.as_view(
            template_name='accounts/signup_done.j.html'),
        name='accounts.signup_done'),

    # E-mail address confirmation
    url(r'^confirm/(?P<key>\w{40})/$', views.confirm_email,
        name='accounts.confirm_email'),
    url(r'resend/$', views.confirmation_resend,
        name='accounts.confirmation_resend'),
    url(r'^resend/done/$', TemplateView.as_view(
            template_name='accounts/confirmation_resend_done.j.html'),
        name='accounts.confirmation_resend_done'),

    # Password reset
    url(r'^password_reset/$', views.password_reset,
        name='accounts.password_reset'),
    url(r'^password_reset/sent/$', TemplateView.as_view(
            template_name='accounts/password_reset_sent.j.html'),
        name='accounts.password_reset_sent'),
    url(r'^password_reset/(?P<key>\w{40})/$', views.password_reset_confirm,
        name='accounts.password_reset_confirm'),
    url(r'^password_reset/done/$', TemplateView.as_view(
            template_name='accounts/password_reset_done.j.html'),
        name='accounts.password_reset_done'),

    # Password change
    url(r'^password_change/$', views.password_change,
        name='accounts.password_change'),
    url(r'password_change/done/$', views.password_change_done,
        name='accounts.password_change_done'),

    # Facebook auth
    url(r'^login/facebook/$', 'facebook.views.login',
        name='accounts.facebook_login'),
    url(r'^facebook/authentication_callback/$', 'facebook.views.authentication_callback'),
    url(r'^login/facebook/verification$', views.facebook_verification,
        # keep this name since it's reversed by Facebook app
        name='facebook_verification'),
)
