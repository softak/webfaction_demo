from datetime import datetime

from django.db import transaction
from django.db.models import Q
from django.conf import settings
from django.conf.urls.defaults import url
from django.core.exceptions import ObjectDoesNotExist,\
                                   MultipleObjectsReturned
from django.utils.decorators import method_decorator

from tastypie.constants import ALL
from tastypie.utils import trailing_slash
from tastypie.utils.mime import build_content_type
from tastypie import http, fields
from tastypie.exceptions import ImmediateHttpResponse
from tastypie.authorization import Authorization
from tastypie.validation import CleanedDataFormValidation

from stores.forms import ItemCreationForm, ItemImageCreationForm, \
                         DiscountCreationForm, DiscountGroupCreationForm, \
                         ItemSearchForm
from stores.models import Store, Item, ItemImage, Discount, DiscountGroup
from cart.models import SocialBuy, SocialTag, PersonalTag, ShippingRequest
from profiles.resources import UserResource
from profiles.models import Profile

from utils.tastypie_ import ModelResource, ModelFormValidation, \
                            CustomToManyField, CustomToOneField
from utils import thumbnail, round_money


class StoreResource(ModelResource):
    id = fields.IntegerField(
        attribute='id')
    name = fields.CharField(
        attribute='name')
    address = fields.CharField(
        attribute='address')
    phone = fields.CharField(
        attribute='phone')
    buyers = fields.ToManyField(UserResource,
        attribute=lambda bundle: bundle.obj \
            .get_buyers() \
            .exclude(id=bundle.request.user.id)[:10],
        full=True,
        null=True)
    lat = fields.FloatField(
        attribute='location__x')
    lng = fields.FloatField(
        attribute='location__y')
    category_id = fields.IntegerField(
        attribute='category__id')
    icon = fields.FileField()
    marker = fields.FileField()
    image = fields.FileField(
        null=True)
    deals = fields.IntegerField()

    class Meta:
        resource_name = 'store'
        queryset = Store.objects.all()
        fields = ('address', 'name', 'phone')
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']
        authorization = Authorization()

    def dehydrate_deals(self, bundle):
        return bundle.obj.items.count()

    def dehydrate_image(self, bundle):
        store = bundle.obj
        if store.window_image:
            return store.window_image.url

    def dehydrate_icon(self, bundle):
        store = bundle.obj
        if store.category.icon:
            return store.category.icon.url
        else:
            return settings.STATIC_URL  + 'img/category-default-icon.png'

    def dehydrate_marker(self, bundle):
        store = bundle.obj
        if store.category.marker:
            return store.category.marker.url
        else:
            return settings.STATIC_URL  + 'img/category-default-marker.png'


class ItemResource(ModelResource):
    store = fields.ForeignKey(StoreResource,
        attribute='store',
        readonly=True)
    default_image = fields.FileField(
        readonly=True)
    best_offer_price = fields.DecimalField(
        readonly=True,
        null=True)
    best_offer_finish_date = fields.DateTimeField(
        readonly=True,
        null=True)

    class Meta:
        resource_name = 'item'
        queryset = Item.objects.all()
        filtering = {
            'store': ('exact',),
            'is_out_of_stock': ALL,
        }

        list_allowed_methods = ['get', 'post']
        detail_allowed_methods = ['get', 'put', 'delete']

        authorization = Authorization()
        validation = CleanedDataFormValidation(form_class=ItemCreationForm)
        always_return_data = True

    def obj_get_list(self, request=None, **kwargs):
        qs = super(ItemResource, self).obj_get_list(request, **kwargs)
        form = ItemSearchForm(request.GET)
        if form.is_valid():
            qs = form.search(qs)
        return qs

    def dehydrate_default_image(self, bundle):
        default_image = bundle.obj.get_default_image()
        if default_image is None:
            default_image = 'http://vk.com/images/question_a.gif'
        return thumbnail(default_image, '150x150', crop='center').url

    def full_dehydrate(self, bundle):
        item = bundle.obj
        store = item.store

        best_price = None
        best_buy = None
        buys = SocialBuy.objects\
            .filter(store=store)\
            .active_or_created_by(bundle.request.user)\
            .unexpired()

        for buy in buys:
            buy_price = buy.get_price(bundle.request.user, item)
            if best_price is None or buy_price < best_price:
                best_price = buy_price
                best_buy = buy

        bundle.best_price = best_price
        bundle.best_buy = best_buy

        return super(ItemResource, self).full_dehydrate(bundle)

    def dehydrate_best_offer_price(self, bundle):
        if not bundle.best_price is None:
            return bundle.best_price

    def dehydrate_best_offer_finish_date(self, bundle):
        if not bundle.best_buy is None:
            return bundle.best_buy.finish_date

    def hydrate(self, bundle):
        if not bundle.obj.pk:
            bundle.obj.store = bundle.request.user.store
        return bundle


class ItemImageResource(ModelResource):
    item = fields.ForeignKey(ItemResource, attribute='item', readonly=True)
    image = fields.ApiField(attribute='image', readonly=True)
    thumb = fields.FileField(readonly=True)

    class Meta:
        resource_name = 'itemimage'
        queryset = ItemImage.objects.all()
        filtering = {
            'item': ('exact',),
        }
        list_allowed_methods = ['get', 'post']
        detail_allowed_methods = ['get', 'put', 'delete']
        authorization = Authorization()

    def dehydrate_thumb(self, bundle):
        return thumbnail(bundle.obj.image, '220x220', crop='center').url

    def dehydrate_image(self, bundle):
        return thumbnail(bundle.obj.image, '400x400', crop='center').url

    def apply_authorization_limits(self, request, item_images_list):
        item_images_list = super(ItemImageResource, self)\
            .apply_authorization_limits(request, item_images_list)
        return item_images_list.filter(item__store__user=request.user)

    def post_list(self, request, **kwargs):
        form = ItemImageCreationForm(data=request.POST,
                                     files=request.FILES)
        if form.is_valid():
            if form.instance.item.store != request.user.store:
                raise ImmediateHttpResponse(response=http.HttpForbidden())
            images = form.save()

            to_be_serialized = []
            for image in images:
                bundle = self.build_bundle(obj=image, request=request)
                bundle = self.full_dehydrate(bundle)
                to_be_serialized.append(bundle)

            response = self.create_response(request, to_be_serialized)
            response['x-frame-options'] = 'SAMEORIGIN'
            return response
        else:
            desired_format = self.determine_format(request)
            serialized = self.serialize(request,
                                        {'errors': form.errors },
                                        desired_format)
            response = http.HttpBadRequest(
                content=serialized,
                content_type=build_content_type(desired_format))
            response['x-frame-options'] = 'SAMEORIGIN'
            raise ImmediateHttpResponse(response=response)


class DiscountResource(ModelResource):
    store = fields.ForeignKey(StoreResource,
        attribute='store',
        related_name='discount_models',
        readonly=True)
    discount_groups = fields.ToManyField(
        'stores.resources.DiscountGroupResource',
        'discount_groups',
        readonly=True)

    class Meta:
        resource_name = 'discount'
        queryset = Discount.objects.all()
        list_allowed_methods = ['get', 'post']
        detail_allowed_methods = ['get', 'put', 'delete']
        authorization = Authorization()
        validation = ModelFormValidation(form_class=DiscountCreationForm)
        always_return_data = True

    def apply_authorization_limits(self, request, discounts_list):
        discounts_list = super(DiscountResource, self) \
                .apply_authorization_limits(request, discounts_list)
        if request.method == 'GET':
            return discounts_list
        else:
            return discounts_list.filter(store=request.user.store)

    def is_valid(self, bundle, request=None):
        bundle.data.update({'store': request.user.store.id})
        return super(DiscountResource, self).is_valid(bundle,
                                                      request=request)

    def hydrate(self, bundle):
        if not bundle.obj.pk:
            bundle.obj.store_id = bundle.request.user.store.id
        return bundle


class DiscountGroupResource(ModelResource):
    discount = fields.ForeignKey(DiscountResource,
        attribute='discount',
        related_name='discount_group')
    items = fields.ToManyField(ItemResource,
        attribute='items',
        related_name='discount_group',
        null=True)

    class Meta:
        resource_name = 'discount_group'
        queryset = DiscountGroup.objects.all()
        list_allowed_methods = ['get', 'post']
        detail_allowed_methods = ['get', 'put', 'delete']
        authorization = Authorization()
        validation = ModelFormValidation(
            form_class=DiscountGroupCreationForm)
        always_return_data = True

    def alter_deserialized_detail_data(self, request, data):
        # items should always be a list
        if data.has_key('items') and type(data['items']) != list:
            data['items'] = [data['items']]
        return data

    def apply_authorization_limits(self, request, groups_list):
        groups_list = super(DiscountGroupResource, self) \
            .apply_authorization_limits(request, groups_list)
        if request.method == 'GET':
            return groups_list
        else:
            return groups_list.filter(discount__store=request.user.store)


# DetailItemResource

class DetailItemSocialTagResource(ModelResource):
    quantity = fields.IntegerField(
        attribute='quantity')
    discounted_price = fields.DecimalField(
        attribute='price')

    class Meta:
        queryset = SocialTag.objects.all().unapproved()
        fields = ('quantity', 'price', 'discounted_price')
        include_resource_uri = False


class DetailItemPersonalTagResource(ModelResource):
    quantity = fields.IntegerField(
        attribute='quantity')
    discounted_price = fields.DecimalField(
        attribute='price')

    class Meta:
        queryset = PersonalTag.objects.all().unapproved()
        fields = ('quantity', 'price', 'discounted_price')
        include_resource_uri = False


class DetailItemSocialBuyResource(ModelResource):
    id = fields.IntegerField(attribute='id')
    creator = fields.ForeignKey(UserResource, attribute='user', full=True)
    finish_date = fields.DateTimeField(attribute='finish_date')
    is_active = fields.BooleanField(attribute='is_active')
    discounted_price = fields.DecimalField()
    bought = fields.IntegerField()
    tag = fields.ApiField()

    class Meta:
        queryset = SocialBuy.objects.unexpired()
        fields = ('id', 'creator', 'finish_date',
                  'discounted_price', 'is_active', 'tag')
        include_resource_uri = False

    def dehydrate_bought(self, bundle):
        return bundle.obj.approved_tags.filter(user=bundle.request.user,
                                               item=bundle.parent_obj) \
                                       .count()

    def dehydrate_tag(self, bundle):
        try:
            tag = bundle.obj.draft_tags.get(user=bundle.request.user,
                                            item=bundle.parent_obj)
            tag_resource = DetailItemSocialTagResource()
            bundle = tag_resource.build_bundle(obj=tag,
                                               request=bundle.request)
            return tag_resource.full_dehydrate(bundle)
        except SocialTag.DoesNotExist:
            return False

    def dehydrate_discounted_price(self, bundle):
        item = bundle.parent_obj
        buy = bundle.obj
        return buy.get_price(bundle.request.user, item)

    def get_detail(self, request, **kwargs):
        if kwargs.has_key('parent_obj'):
            parent_obj = kwargs.pop('parent_obj')

        try:
            obj = self.cached_obj_get(
                request=request,
                **self.remove_api_resource_names(kwargs))
        except ObjectDoesNotExist:
            return http.HttpNotFound()
        except MultipleObjectsReturned:
            return http.HttpMultipleChoices(
                'More than one resource is found at this URI.')

        bundle = self.build_bundle(obj=obj, request=request)
        if not parent_obj is None:
            bundle.parent_obj = parent_obj
        bundle = self.full_dehydrate(bundle)
        return self.create_response(request, bundle)


class DetailItemResource(ModelResource):
    store = fields.ForeignKey(StoreResource,
        attribute='store')
    price = fields.DecimalField(
        attribute='price')
    personal_tag = fields.ApiField()
    buys = CustomToManyField(DetailItemSocialBuyResource,
        attribute=lambda bundle:
            SocialBuy.objects.filter(store=bundle.obj.store) \
                             .active_or_created_by(bundle.request.user) \
                             .unexpired(),
        full=True,
        null=True)

    class Meta:
        resource_name = 'detail_item'
        queryset = Item.objects.all()
        fields = ['buys']
        detail_allowed_methods = ['get']
        authorization = Authorization()

    def dehydrate_personal_tag(self, bundle):
        try:
            tag = PersonalTag.objects.unapproved() \
                                     .get(user=bundle.request.user,
                                          item=bundle.obj)
            tag_resource = DetailItemPersonalTagResource()
            bundle = tag_resource.build_bundle(obj=tag,
                                               request=bundle.request)
            return tag_resource.full_dehydrate(bundle)
        except PersonalTag.DoesNotExist:
            return False

    def override_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/"
                 r"(?P<item_pk>\w[\w/-]*)/"
                 r"buys/(?P<buy_pk>\w[\w/-]*)%s$" % (
                    self._meta.resource_name,
                    trailing_slash()),
                self.wrap_view('get_buys'),
                name='api_get_buys'),
            url(r"^(?P<resource_name>%s)/"
                 r"(?P<item_pk>\w[\w/-]*)/"
                 r"personal_tag%s$" % (
                     self._meta.resource_name,
                     trailing_slash()),
                self.wrap_view('get_personal_tag'),
                name='api_get_personal_tag'),
        ]

    def get_buys(self, request, **kwargs):
        try:
            lookup_kwargs = self.remove_api_resource_names(kwargs)
            obj = self.cached_obj_get(request=request,
                                      pk=lookup_kwargs['item_pk'])
        except ObjectDoesNotExist:
            return http.HttpGone()
        except MultipleObjectsReturned:
            return http.HttpMultipleChoices(
                'More than one resource is found at this URI.')

        child_resource = DetailItemSocialBuyResource()
        return child_resource.get_detail(request,
                                         id=lookup_kwargs['buy_pk'],
                                         parent_obj=obj)

    def get_personal_tag(self, request, **kwargs):
        try:
            lookup_kwargs = self.remove_api_resource_names(kwargs)
            obj = self.cached_obj_get(request=request,
                                      pk=lookup_kwargs['item_pk'])
        except ObjectDoesNotExist:
            return http.HttpGone()
        except MultipleObjectsReturned:
            return http.HttpMultipleChoices(
                'More than one resource is found at this URI.')

        child_resource = DetailItemPersonalTagResource()
        return child_resource.get_detail(request, user=request.user, item=obj)

# / DetailItemResource


# TODO Make it applied for personal buys too.
class PendingShippingRequestResource(ModelResource):
    creator = fields.ForeignKey(UserResource,
        attribute='user',
        full=True,
        readonly=True)
    social_buy = CustomToOneField('cart.resources.SocialCartBuyResource',
        attribute='buy',
        full=True,
        readonly=True)
    address = fields.CharField(
        attribute='address',
        readonly=True)
    price = fields.DecimalField(
        attribute='price',
        null=True)
    total = fields.DecimalField(
        null=False,
        readonly=True)

    class Meta:
        resource_name = 'pending_shipping_request'
        queryset = ShippingRequest.objects.not_responded()
        fields = ('creator', 'social_buy', 'address', 'price', 'total')
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get', 'put', 'delete']
        authorization = Authorization()

    def apply_authorization_limits(self, request, queryset):
        queryset = super(PendingShippingRequestResource, self) \
                .apply_authorization_limits(request, queryset)
        return queryset.filter(Q(buy__store=request.user.store) | 
                               Q(store=request.user.store))
    
    def dehydrate(self, bundle):
        total = 0
        for tag_bundle in bundle.data['social_buy'].data['tags']:
            total += tag_bundle.data['discounted_price']
        bundle.data['total'] = round_money(total)
        return bundle
    
    def hydrate(self, bundle):
        if bundle.data.has_key('price') and bundle.data['price']:
            bundle.obj.priced_date = datetime.utcnow()
        return bundle

    @method_decorator(transaction.commit_on_success)
    def obj_update(self, *args, **kwargs):
        request = kwargs['request']
        Profile.objects.select_for_update().get(user=request.user)
        return super(PendingShippingRequestResource, self) \
                .obj_update(*args, **kwargs)

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
