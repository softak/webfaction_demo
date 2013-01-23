import datetime
from django.db import models
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.conf import settings
import os

from facebook.models import FacebookProfile
# ImageField automatically deletes references to itself in the key value store and
# its thumbnail references and the thumbnail files when deleted 
from sorl.thumbnail import ImageField
from cart.models import Transaction

from utils import thumbnail

class Profile(models.Model):
    SEX_CHOICES = (
        ('F', 'Female'),
        ('M', 'Male'),
    )
    user = models.OneToOneField(User)
    sex = models.CharField(_('sex'),
        max_length=1,
        choices=SEX_CHOICES)
    birthday = models.DateField(_('birthday'))
    avatar = ImageField(_('avatar'),
        upload_to='avatars',
        blank=True,
        null=True)
    pending_transaction = models.OneToOneField(Transaction,
        null=True,
        blank=True,
        related_name='profile',
        on_delete=models.SET_NULL)

    @property
    def is_cart_locked(self):
        return (not self.pending_transaction is None) and (not self.pending_transaction.is_approved)
    
    @property
    def avatar_small(self):
        return self.get_avatar_thumb(size='40x40').url
    
    @property
    def avatar_xsmall(self):
        return self.get_avatar_thumb(size='28x28').url

    def get_avatar(self):
        return self.avatar or os.path.join(settings.MEDIA_ROOT, 'img/no-avatar.jpg')

    def get_avatar_thumb(self, size='40x40'):
        return thumbnail(self.get_avatar(), size, crop='center')

    def get_age(self):
        return int((datetime.date.today() - self.birthday).days / 365.25)

    @models.permalink
    def get_absolute_url(self):
        return ('profiles.profile', (), { 'pk': self.user.id })


def fill_profile_from_facebook_data(sender, instance, created, **kwargs):
    if created and not Profile.objects.filter(user=instance.user).exists():
        profile = Profile(user=instance.user)
        fb_data = instance.get_facebook_profile()
        
        instance.user.first_name = fb_data['first_name']
        instance.user.last_name = fb_data['last_name']
        profile.sex = fb_data['gender'][0].upper()
        profile.birthday = datetime.datetime.strptime(fb_data['birthday'], '%m/%d/%Y')

        profile.save()
        instance.user.save()
post_save.connect(fill_profile_from_facebook_data, sender=FacebookProfile)
