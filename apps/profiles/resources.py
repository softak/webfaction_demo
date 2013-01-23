from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from tastypie import fields, http
from tastypie.authorization import Authorization

from friends.models import Friendship

from utils.tastypie_ import ModelResource


class UserResource(ModelResource):
    name = fields.CharField()
    avatar_small = fields.FileField(attribute='profile__avatar_small')
    avatar_xsmall = fields.FileField(attribute='profile__avatar_xsmall')
    is_friend = fields.BooleanField()
    friendship_request_url = fields.CharField()
    site_url = fields.CharField()
    
    def dehydrate_friendship_request_url(self, bundle):
        return reverse('friends.friendship_request', args=[bundle.obj.id])
    
    def dehydrate_site_url(self, bundle):
        return bundle.obj.profile.get_absolute_url()
    
    def dehydrate_is_friend(self, bundle):
        if bundle.request.user.is_authenticated():
            return Friendship.objects.are_friends(bundle.obj, bundle.request.user)
        else:
            return False

    def dehydrate_name(self, bundle):
        return bundle.obj.get_full_name()

    class Meta:
        resource_name = 'user'
        queryset = User.objects.all()

        list_allowed_methods = []
        detail_allowed_methods = ['get']

        authorization = Authorization()
        fields = ('name', 'avatar',)
