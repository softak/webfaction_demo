from django.db import transaction
from django.conf.urls.defaults import url
from django.contrib.auth.models import User
from django.core.urlresolvers import NoReverseMatch
from django.core.exceptions import ObjectDoesNotExist
from django.utils.decorators import method_decorator

from tastypie import fields, http
from tastypie.authorization import Authorization
from tastypie.exceptions import NotFound
from tastypie.utils import trailing_slash

from utils.tastypie_ import ModelResource, ModelFormValidation,\
                            CustomToOneField
from profiles.resources import UserResource
from profiles.models import Profile
from stores.resources import ItemResource
from stores.models import Store
from cart.models import PersonalTag, SocialTag, SocialBuy,\
                        ShippingRequest, PickupRequest
from cart.forms import PersonalTagForm, SocialTagForm, SocialBuyForm

from utils import thumbnail, round_money


class AbstractCartResource(ModelResource):

    def get_uri(self, name, **kwargs):
        lookup_kwargs = { 'resource_name': self._meta.resource_name }
        if self._meta.api_name is not None:
            lookup_kwargs['api_name'] = self._meta.api_name
        lookup_kwargs.update(kwargs)
        try:
            return self._build_reverse_url(name, kwargs=lookup_kwargs)
        except NoReverseMatch:
            return None

    def get_shipping_request_uri(self, **kwargs):
        return self.get_uri('api_shipping_request_resource', **kwargs)

    def get_pickup_request_uri(self, **kwargs):
        return self.get_uri('api_pickup_request_resource', **kwargs)

    def override_urls(self):
        return [
            url(r"^(?P<resource_name>%s)%s$" % (
                    self._meta.resource_name,
                    trailing_slash()),
                self.wrap_view('dispatch_detail'),
                name='api_dispatch_detail'),
            url(r"^(?P<resource_name>%s)/"
                 r"buys/(?P<buy_pk>\w[\w/-]*)/"
                 r"shipping_request%s$" % (
                     self._meta.resource_name,
                     trailing_slash()),
                self.wrap_view('create_shipping_request'),
                name='api_create_shipping_request'),
            url(r"^(?P<resource_name>%s)/"
                 r"buys/(?P<buy_pk>\w[\w/-]*)/"
                 r"pickup_request%s$" % (
                     self._meta.resource_name,
                     trailing_slash()),
                self.wrap_view('create_pickup_request'),
                name='api_create_pickup_request'),
            url(r"^(?P<resource_name>%s)/"
                 r"buys/(?P<buy_pk>\w[\w/-]*)%s$" % (
                     self._meta.resource_name,
                     trailing_slash()),
                self.wrap_view('get_buy'),
                name='api_get_buy'),
            url(r"^(?P<resource_name>%s)/shipping_requests/"
                 r"(?P<shipping_request_pk>\w[\w/-]*)%s$" % (
                     self._meta.resource_name,
                     trailing_slash()),
                self.wrap_view('shipping_request'),
                name='api_shipping_request_resource'),
            url(r"^(?P<resource_name>%s)/pickup_requests/"
                 r"(?P<pickup_request_pk>\w[\w/-]*)%s$" % (
                     self._meta.resource_name,
                     trailing_slash()),
                self.wrap_view('pickup_request'),
                name='api_pickup_request_resource')
        ]

    def _get_child_buy_resource(self):
        raise NotImplementedError
    def _get_child_shipping_request_resource(self):
        raise NotImplementedError
    def _get_child_pickup_request_resource(self):
        raise NotImplementedError
    def _create_shipping_request(self, request, lookup_kwargs):
        raise NotImplementedError
    def _create_pickup_request(self, request, lookup_kwargs):
        raise NotImplementedError

    def create_shipping_request(self, request, **kwargs):
        lookup_kwargs = self.remove_api_resource_names(kwargs)
        return self._create_shipping_request(request, lookup_kwargs)

    def shipping_request(self, request, **kwargs):
        child_resource = self._get_child_shipping_request_resource()
        lookup_kwargs = self.remove_api_resource_names(kwargs)
        return child_resource.dispatch_detail(
            request,
            pk=lookup_kwargs['shipping_request_pk'])

    def create_pickup_request(self, request, **kwargs):
        lookup_kwargs = self.remove_api_resource_names(kwargs)
        return self._create_pickup_request(request, lookup_kwargs)

    def pickup_request(self, request, **kwargs):
        child_resource = self._get_child_pickup_request_resource()
        lookup_kwargs = self.remove_api_resource_names(kwargs)
        return child_resource.dispatch_detail(
            request,
            pk=lookup_kwargs['pickup_request_pk'])

    def get_buy(self, request, **kwargs):
        child_resource = self._get_child_buy_resource()
        lookup_kwargs = self.remove_api_resource_names(kwargs)
        return child_resource.get_detail(
            request,
            pk=lookup_kwargs['buy_pk'])

    def get_detail(self, request, **kwargs):
        kwargs.update({ 'pk': request.user.id })
        return super(AbstractCartResource, self).get_detail(
            request,
            **kwargs)


# PersonalCart resource

class PersonalCartTagResource(ModelResource):
    item = fields.ForeignKey(ItemResource, 'item')
    item_name = fields.CharField(attribute='item__name')
    item_site_url = fields.CharField()
    item_thumb = fields.FileField()
    quantity = fields.IntegerField(attribute='quantity')
    price = fields.DecimalField(attribute='original_price')
    discounted_price = fields.DecimalField(attribute='price')

    class Meta:
        queryset = PersonalTag.objects.unapproved()
        fields = ('item', 'item_name', 'item_site_url', 'item_thumb',
                  'quantity',
                  'price', 'discounted_price')
        include_resource_uri = False

    def dehydrate_item_site_url(self, bundle):
        return bundle.obj.item.get_absolute_url()

    def dehydrate_item_thumb(self, bundle):
        default_image = bundle.obj.item.get_default_image()
        if not default_image is None:
            return thumbnail(default_image, '80x80', crop='center').url


class PersonalCartStoreResource(ModelResource):
    store_name = fields.CharField(attribute='name')
    store_site_url = fields.CharField()
    tags = fields.ToManyField(PersonalCartTagResource,
        full=True,
        null=True,
        attribute=lambda bundle:
            PersonalTag.objects.unapproved().filter(
                item__store=bundle.obj,
                user=bundle.request.user))

    class Meta:
        queryset = Store.objects.filter(is_active=True)
        fields = ('store_name', 'store_site_url', 'tags', 'id')
        include_resource_uri = False

    def dehydrate_store_site_url(self, bundle):
        return bundle.obj.get_absolute_url()


class PersonalCartResource(AbstractCartResource):
    buys = fields.ToManyField(PersonalCartStoreResource,
        full=True,
        null=True,
        attribute=lambda bundle: PersonalCartResource.get_stores(bundle))
 
    class Meta:
        resource_name = 'personal_cart'
        queryset = User.objects.filter(is_active=True)
        fields = ('buys')
        list_allowed_methods = []
        detail_allowed_methods = ['get', 'post']
        authorization = Authorization()

    @staticmethod
    def get_stores(bundle):
        user = bundle.request.user
        store_ids = PersonalTag.objects.filter(user=user).unapproved()\
            .values_list('item__store', flat=True).distinct()
        return Store.objects.filter(id__in=store_ids)

    def _get_child_buy_resource(self):
        return PersonalCartStoreResource()

    def post_detail(self, request, **kwargs):
        # Lock on profile
        deserialized = self.deserialize(request, request.raw_post_data)

        if not deserialized.has_key('buys'):
            self.raise_bad_request_error({
                'buys': ['This field is required.']
            })

        updated_buys = []

        for buy_data in deserialized['buys']:
            buy_data['id'] = ModelFormValidation.uri_to_pk(buy_data['id'])
            store = Store.objects.get(id=buy_data['id'])

            if not buy_data.has_key('tags'):
                self.raise_bad_request_error({
                    'tags': ['This field is required.']
                })

            for tag_data in buy_data['tags']:
                tag_data = ModelFormValidation.convert_uris_to_pk(
                    tag_data,
                    PersonalTagForm)
                tag_data['user'] = request.user.id

                form = PersonalTagForm(tag_data)
                if form.is_valid():
                    form.save()
                else:
                    self.raise_bad_request_error(form.errors)

            updated_buys.append({ 'id': store.id })

        return self.create_response(request, { 'buys': updated_buys },
            response_class=http.HttpCreated)
# / PersonalCart resource


# SocialCart resource

class SocialCartTagResource(ModelResource):
    item = fields.ForeignKey(ItemResource, attribute='item')
    item_name = fields.CharField(attribute='item__name')
    item_discounted_price = fields.CharField(attribute='item_discounted_price')
    item_site_url = fields.CharField()
    item_thumb = fields.FileField()
    quantity = fields.IntegerField(attribute='quantity')
    price = fields.DecimalField(attribute='original_price')
    discounted_price = fields.DecimalField(attribute='price')

    class Meta:
        queryset = SocialTag.objects.unapproved()
        fields = ('item', 'item_name', 'item_site_url', 'item_thumb',
                  'quantity',
                  'price', 'discounted_price')
        include_resource_uri = False

    def dehydrate_item_site_url(self, bundle):
        return bundle.obj.item.get_absolute_url()

    def dehydrate_item_thumb(self, bundle):
        default_image = bundle.obj.item.get_default_image()
        if not default_image is None:
            return thumbnail(default_image, '80x80', crop='center').url


class SocialCartBuyResource(ModelResource):
    id = fields.IntegerField(attribute='id', readonly=True)
    creator = fields.ForeignKey(UserResource, 'user',
        full=True,
        readonly=True)
    store_name = fields.CharField(readonly=True)
    store_site_url = fields.CharField(readonly=True)
    finish_date = fields.DateTimeField(
        attribute='finish_date',
        readonly=True)
    tags = fields.ToManyField(SocialCartTagResource,
        full=True,
        null=True,
        attribute=lambda bundle: SocialCartBuyResource.get_tags(bundle))

    class Meta:
        queryset = SocialBuy.objects.all()
        fields = ('id', 'creator',
                  'store_name', 'store_site_url',
                  'finish_date', 'tags')
        include_resource_uri = False

    @staticmethod
    def get_tags(bundle):
        # If bundle.parent_obj specified and is request,
        # get_tags will return it's tags. Otherwise get_tags 
        # will return all tags of this Social Buy.
        if not hasattr(bundle, 'parent_obj'):
            return SocialTag.objects.draft().filter(
                buy=bundle.obj,
                user=bundle.request.user)

        elif isinstance(bundle.parent_obj, ShippingRequest):
            return SocialTag.objects.unapproved().filter(
                buy=bundle.obj,
                shipping_request=bundle.parent_obj)

        elif isinstance(bundle.parent_obj, PickupRequest):
            return SocialTag.objects.unapproved().filter(
                buy=bundle.obj,
                pickup_request=bundle.parent_obj)

    def dehydrate_store_site_url(self, bundle):
        return bundle.obj.store.get_absolute_url()

    def dehydrate_store_name(self, bundle):
        return bundle.obj.store.name


class SocialCartPostageRequestResource(ModelResource):
    buy = CustomToOneField(SocialCartBuyResource,
        full=True,
        readonly=True,
        attribute='buy')

    @method_decorator(transaction.commit_on_success)
    def obj_delete(self, request=None, **kwargs):
        Profile.objects.select_for_update().get(user=request.user)
        shipping_request = kwargs.pop('_obj', None)

        if not hasattr(shipping_request, 'delete'):
            try:
                shipping_request = self.obj_get(request, **kwargs)
            except ObjectDoesNotExist:
                raise NotFound('A model instance matching the provided'
                               'arguments could not be found.')

        buy = shipping_request.buy
        shipping_request.delete()
        buy.merge_draft_tags(request.user)

    class Meta:
        queryset = ShippingRequest.objects.unapproved()
        fields = ('address', 'id', 'price', 'buy')
        include_resource_uri = False
        detail_allowed_methods = ['get', 'delete']
        authorization = Authorization()


class SocialCartPickupRequestResource(ModelResource):
    buy = CustomToOneField(SocialCartBuyResource,
        full=True,
        readonly=True,
        attribute='buy')

    @method_decorator(transaction.commit_on_success)
    def obj_delete(self, request=None, **kwargs):
        Profile.objects.select_for_update().get(user=request.user)
        pickup_request = kwargs.pop('_obj', None)

        if not hasattr(pickup_request, 'delete'):
            try:
                pickup_request = self.obj_get(request, **kwargs)
            except ObjectDoesNotExist:
                raise NotFound('A model instance matching the provided'
                               'arguments could not be found.')

        buy = pickup_request.buy
        pickup_request.delete()
        buy.merge_draft_tags(request.user)

    class Meta:
        queryset = PickupRequest.objects.unapproved()
        fields = ('id', 'buy')
        include_resource_uri = False
        detail_allowed_methods = ['get', 'delete']
        authorization = Authorization()


class SocialCartResource(AbstractCartResource):
    buys = fields.ToManyField(SocialCartBuyResource,
        full=True,
        null=True,
        attribute=lambda bundle:
            SocialBuy.objects.for_user(bundle.request.user)\
                             .unexpired()\
                             .contains_draft_tags())
    pending_shipping_requests = fields.ToManyField(
        SocialCartPostageRequestResource,
        full=True,
        null=True,
        attribute=lambda bundle:
            ShippingRequest.objects.unapproved().not_responded()\
                                   .filter(user=bundle.request.user))
    shipping_requests = fields.ToManyField(
        SocialCartPostageRequestResource,
        full=True,
        null=True,
        attribute=lambda bundle:
            ShippingRequest.objects.unapproved().responded()\
                                   .filter(user=bundle.request.user))
    pickup_requests = fields.ToManyField(SocialCartPickupRequestResource,
        full=True,
        null=True,
        attribute=lambda bundle:
            PickupRequest.objects.unapproved()\
                                 .filter(user=bundle.request.user))
    total = fields.DecimalField(
        null=False,
        readonly=True)

    class Meta:
        resource_name = 'social_cart'
        queryset = User.objects.filter(is_active=True)
        fields = ('buys', 'pending_shipping_requests', 'shipping_requests', 'total')
        list_allowed_methods = []
        detail_allowed_methods = ['get', 'post']
        authorization = Authorization()
    
    def dehydrate(self, bundle):
        total = 0
        for shipping_request_bundle in bundle.data['shipping_requests']:
            for tag_bundle in shipping_request_bundle.data['buy'].data['tags']:
                total += tag_bundle.data['discounted_price']
            total += shipping_request_bundle.data['price']

        for pickup_request_bundle in bundle.data['pickup_requests']:
            for tag_bundle in pickup_request_bundle.data['buy'].data['tags']:
                total += tag_bundle.data['discounted_price']
        
        bundle.data['total'] = round_money(total)
        return bundle

    def _get_child_shipping_request_resource(self):
        return SocialCartPostageRequestResource()

    def _get_child_pickup_request_resource(self):
        return SocialCartPickupRequestResource()

    def _get_child_buy_resource(self):
        return SocialCartBuyResource()

    def _create_shipping_request(self, request, lookup_kwargs):
        child_resource = self._get_child_buy_resource()
        buy = child_resource.obj_get(request=request,
                                     pk=lookup_kwargs['buy_pk'])

        if request.method == 'POST':
            deserialized = self.deserialize(request, request.raw_post_data)

            if not deserialized.has_key('address') or \
               deserialized['address'] == '':
                self.raise_bad_request_error({
                    'address': ['This field is required.']
                })

            with transaction.commit_on_success():
                Profile.objects.select_for_update().get(user=request.user)
                shipping_request = ShippingRequest.objects.create(
                    address=deserialized['address'],
                    user=request.user,
                    buy=buy)

                SocialTag.objects.filter(buy=buy).draft()\
                                 .update(shipping_request=shipping_request)
                return self.create_response(request, {
                    'resource_uri': self.get_shipping_request_uri(
                        shipping_request_pk=shipping_request.id)
                }, response_class=http.HttpCreated)
        else:
            pass # TODO Raise smth.

    def _create_pickup_request(self, request, lookup_kwargs):
        # TODO Lock on profile
        child_resource = self._get_child_buy_resource()
        buy = child_resource.obj_get(request=request,
                                     pk=lookup_kwargs['buy_pk'])

        if request.method == 'POST':
            with transaction.commit_on_success():
                Profile.objects.select_for_update().get(user=request.user)
                pickup_request = PickupRequest.objects.create(
                    user=request.user,
                    buy=buy)

                SocialTag.objects.filter(buy=buy).draft() \
                                 .update(pickup_request=pickup_request)

                return self.create_response(
                    request,
                    {
                        'resource_uri': self.get_pickup_request_uri(
                            pickup_request_pk=pickup_request.id)
                    },
                    response_class=http.HttpCreated)
        else:
            pass # TODO Raise smth.

    def post_detail(self, request, **kwargs):
        # TODO Lock on profile
        deserialized = self.deserialize(request, request.raw_post_data)

        if not deserialized.has_key('buys'):
            self.raise_bad_request_error(request, {
                'buys': ['This field is required.']
            })

        updated_buys = []

        for buy_data in deserialized['buys']:
            buy_data = ModelFormValidation.convert_uris_to_pk(
                buy_data,
                SocialBuyForm)
            buy_data['user'] = request.user.id

            form = SocialBuyForm(buy_data)
            if form.is_valid():
                buy = form.save()
            else:
                self.raise_bad_request_error(request, form.errors)

            if not buy_data.has_key('tags'):
                self.raise_bad_request_error({
                    'tags': ['This field is required.']
                })

            for tag_data in buy_data['tags']:
                tag_data = ModelFormValidation.convert_uris_to_pk(
                    tag_data,
                    SocialTagForm)
                tag_data.update({
                    'buy': buy.id,
                    'user': request.user.id
                })

                form = SocialTagForm(tag_data)
                if form.is_valid():
                    form.save()
                else:
                    self.raise_bad_request_error(request, form.errors)

            updated_buys.append({ 'id': buy.id })

        return self.create_response(request, { 'buys': updated_buys },
                                    response_class=http.HttpCreated)
# / SocialCart resource
