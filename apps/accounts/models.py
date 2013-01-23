import random
import datetime
from hashlib import sha1
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.contrib.sites.models import get_current_site


class EmailConfirmation(models.Model):
    user = models.ForeignKey(User,
                             related_name='email_confirmations',
                             editable=False)
    email = models.EmailField(_('e-mail address'))
    key = models.CharField(_('confirmation key'),
                           max_length=40,
                           editable=False)
    last_sent = models.DateTimeField(_('last time confirmation was sent'),
                                     null=True)

    def __unicode__(self):
        return self.email

    def save(self, *args, **kwargs):
        if not self.key:
            salt = sha1(str(random.random())).hexdigest()[:5]
            self.key = sha1(salt+self.user.username).hexdigest()
        super(EmailConfirmation, self).save(*args, **kwargs)

    def send(self, request, update_timestamp=True):
        """
        Sends a confirmation message to the user optionally updating
        last_sent timestamp.
        """
        site = get_current_site(request)
        context = {
            'confirmation': self,
            'confirmation_url': '%s://%s%s' % (
                'https' if request.is_secure() else 'http',
                site.domain,
                reverse('accounts.confirm_email',
                        kwargs={'key': self.key})
            )
        }
        subject = render_to_string(
            'accounts/email_confirmation_subject.j.txt', context)
        message = render_to_string(
            'accounts/email_confirmation_message.j.txt', context)
        email = send_mail(subject, message,
                          settings.DEFAULT_FROM_EMAIL,
                          [self.email])
        if update_timestamp:
            self.last_sent = datetime.datetime.utcnow()
            self.save()
        return email

    def confirm(self, key):
        if self.key == key:
            self.delete()
            return True
        return False


class PasswordReset(models.Model):
    user = models.ForeignKey(User,
                             related_name='password_resets',
                             editable=False)
    key = models.CharField(_('reset key'),
                           max_length=40,
                           editable=False)
    last_sent = models.DateTimeField(_('last time reset email was sent'),
                                     null=True)

    def __unicode__(self):
        return self.key

    def save(self, *args, **kwargs):
        if not self.key:
            salt = sha1(str(random.random())).hexdigest()[:5]
            self.key = sha1(salt+self.user.username).hexdigest()
        super(PasswordReset, self).save(*args, **kwargs)

    def send(self, request, update_timestamp=True):
        """
        Sends a password reset message to the user optionally updating
        last_sent timestamp.
        """
        site = get_current_site(request)
        context = {
            'reset': self,
            'reset_url': '%s://%s%s' % (
                'https' if request.is_secure() else 'http',
                site.domain,
                reverse('accounts.password_reset_confirm', 
                        kwargs={'key': self.key})
            )
        }
        subject = render_to_string(
            'accounts/password_reset_subject.j.txt', context)
        message = render_to_string(
            'accounts/password_reset_message.j.txt', context)
        email = send_mail(subject, message,
                          settings.DEFAULT_FROM_EMAIL,
                          [self.user.email])
        if update_timestamp:
            self.last_sent = datetime.datetime.utcnow()
            self.save()
        return email

    def verify(self, key):
        return self.key == key
