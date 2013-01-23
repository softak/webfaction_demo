from lettuce import *
from django_any import any_model
from stores.models import Category, Store, DiscountGroup, Discount, Item
from profiles.models import Profile
from django.contrib.auth.models import User


@step(r'I have the following discount models in "(.*)"')
def discounts_in_database(step, store_name):
    store = Store.objects.get(name=store_name)
    for discount_dict in step.hashes:
        Discount.objects.create(store=store, **discount_dict)


@step(r'Given I have the following items in "(.*)" '
      r'grouped together with "(.*)":')
def items_in_database(step, store_name, discount_model_name):
    discount = Discount.objects.get(name=discount_model_name)
    discount_group = DiscountGroup.objects.create(name='Test',
                                                  discount=discount)
    store = Store.objects.get(name=store_name)
    for item_dict in step.hashes:
        Item.objects.create(store=store,
                            discount_group=discount_group,
                            **item_dict)


@step(r'I have the following users in my database:')
def users_in_database(step):
    for user_dict in step.hashes:
        user = any_model(User, is_active=True, **user_dict)
        user.set_password('123')
        user.save()

        any_model(Profile, avatar=None, user=user)


@step(r'I have the following stores in my database:')
def stores_in_database(step):
    for store_dict in step.hashes:
        store_dict['user'] = User.objects.get(username=store_dict['user'])
        store_dict['category'], _ = Category.objects.get_or_create(
                name=store_dict['category'])
        store_dict['location'] = 'POINT(56 100)'
        Store.objects.create(**store_dict)

@step(r'I\'m logged in as (.+).')
def c(step, username):
    assert world.client.login(username=username, password='123')


# Utils
from utils import to_json, from_json
from django.test.client import FakePayload
from django.core.urlresolvers import reverse

def client_api_post(url, data):
    return world.client.post(url, '', content_type='application/json', **{
        'wsgi.input': FakePayload(to_json(data))
    })

def client_api_put(url, data):
    return world.client.put(url, '', content_type='application/json', **{
        'wsgi.input': FakePayload(to_json(data))
    })

def get_cart():
    url = reverse('api_dispatch_list', kwargs={
        'resource_name': 'social_cart',
        'api_name': 'v1'
    })
    result = world.client.get(url)
    assert result.status_code == 200
    return from_json(result.content)

def get_buy_ids(step):
    buy_ids = []
    for buy in step.hashes:
        buy_name = buy['name']
        buy_ids.append(getattr(world, buy_name))
    return buy_ids

def set_buy_pk(buy_name, buy_pk):
    setattr(world, buy_name, buy_pk)

def get_buy_pk(buy_name):
    return getattr(world, buy_name)

def get_shipping_request_uri(buy_name):
    return getattr(world, 'shipping_request_uri_for_%d' % get_buy_pk(buy_name))

def get_pickup_request_uri(buy_name):
    return getattr(world, 'pickup_request_uri_for_%d' % get_buy_pk(buy_name))

def set_shipping_request_uri(buy_name, uri):
    attr_name = 'shipping_request_uri_for_%d' % get_buy_pk(buy_name)
    setattr(world, attr_name, uri)

def set_pickup_request_uri(buy_name, uri):
    attr_name = 'pickup_request_uri_for_%d' % get_buy_pk(buy_name)
    setattr(world, attr_name, uri)
