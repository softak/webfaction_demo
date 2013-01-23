from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from datetime import datetime, timedelta
from django_any import any_model
from lettuce import *
from utils import to_json, from_json

from stores.models import Category, Store, DiscountGroup, Discount, Item
from profiles.models import Profile


from cart.features.common import *


@step(r'I see (.+) on "(.+)" item page and it\'s ((?:active)|(?:inactive)).')
def a(step, buy_name, item_name, buy_expected_state):
    url = reverse('api_dispatch_detail', kwargs={
        'resource_name': 'detail_item',
        'api_name': 'v1',
        'pk': Item.objects.get(name=item_name).pk
    })
    
    result = world.client.get(url)
    assert result.status_code == 200
    response = from_json(result.content)

    found_buy = None
    for buy in response['buys']:
        if buy['id'] != get_buy_pk(buy_name):
            continue

        found_buy = buy
        assert (buy_expected_state == 'active' and buy['is_active']) or \
               (buy_expected_state == 'inactive' and not buy['is_active'])

    assert not found_buy is None


@step(r'I don\'t see any Social Buy on "(.*)" item page.')
def b(step, item_name):
    url = reverse('api_dispatch_detail', kwargs={
        'resource_name': 'detail_item',
        'api_name': 'v1',
        'pk': Item.objects.get(name=item_name).pk
    })
    result = world.client.get(url)
    assert result.status_code == 200
    response = from_json(result.content)

    assert len(response['buys']) == 0


@step(r'To buy (\d+) "(.+)" I create a Social Buy that finishes in '
      r'(\d+) hours. Let\'s call it (.+).')
def d(step, quantity, item_name, hours, buy_name):
    url = reverse('api_dispatch_list', kwargs={
        'resource_name': 'social_cart',
        'api_name': 'v1'
    })
    finish_date = datetime.utcnow() + timedelta(hours=int(hours))
    # Cast to string and remove milliseconds
    finish_date = str(finish_date).split('.')[0]
    item = Item.objects.get(name=item_name)
    
    data = {
        'buys': [{
            'finish_date': str(finish_date),
            'store': item.store.id,
            'tags': [{
                'item': item.id,
                'quantity': int(quantity)
            }]
        }]
    }
    
    result = client_api_post(url, data)
    assert result.status_code == 201
    response = from_json(result.content)
    assert len(response['buys']) == 1

    buy_data = response['buys'][0]
    assert buy_data.has_key('id')

    set_buy_pk(buy_name, buy_data['id'])


@step(r'I request shipping for (.+).')
def e(step, buy_name):
    url = reverse('api_create_shipping_request', kwargs={
        'resource_name': 'social_cart',
        'api_name': 'v1',
        'buy_pk': get_buy_pk(buy_name)
    })
    data = { 'address': 'Cool address' }
    result = client_api_post(url, data)
    assert result.status_code == 201
    response = from_json(result.content)

    set_shipping_request_uri(buy_name, response['resource_uri'])


@step(r'I see no Social Buys.')
def f(step):
    expected_buy_ids = get_buy_ids(step)
    response = get_cart()
    assert len(response['buys']) == 0


@step(r'I see pending Shipping Requests only '
      r'for the following Social Buys:')
def g(step):
    expected_buy_ids = get_buy_ids(step)
    response = get_cart()

    for request in response['pending_shipping_requests']:
        assert request['buy']['id'] in expected_buy_ids
    assert len(expected_buy_ids) == len(response['pending_shipping_requests'])


@step(r'I see the only following Social Buys:')
def h(step):
    expected_buy_ids = get_buy_ids(step)
    response = get_cart()

    for buy in response['buys']:
        assert buy['id'] in expected_buy_ids
    assert len(expected_buy_ids) == len(response['buys'])


@step(r'I cancel pending Shipping Request for (.+).')
def i(step, buy_name):
    url = get_shipping_request_uri(buy_name)
    result = world.client.delete(url)
    assert result.status_code == 204


@step(r'I see no pending Shipping Requests.')
def j(step):
    response = get_cart()
    assert len(response['pending_shipping_requests']) == 0


@step(r'I put (\d+) "(.+)" to (.+)\.')
def k(step, quantity, item_name, buy_name):
    url = reverse('api_dispatch_list', kwargs={
        'resource_name': 'social_cart',
        'api_name': 'v1'
    })
    
    item = Item.objects.get(name=item_name)
    
    data = {
        'buys': [{
            'id': get_buy_pk(buy_name),
            'tags': [{
                'item': item.id,
                'quantity': int(quantity)
            }]
        }]
    }

    result = client_api_post(url, data)
    assert result.status_code == 201
    response = from_json(result.content)
    assert response['buys'][0]['id'] == get_buy_pk(buy_name)


@step(r'I see that (.+) contains (\d+) "(.+)"')
def l(step, buy_name, quantity, item_name):
    url = reverse('api_get_buy', kwargs={
        'resource_name': 'social_cart',
        'api_name': 'v1',
        'buy_pk': get_buy_pk(buy_name)
    })
    result = world.client.get(url)
    assert result.status_code == 200
    response = from_json(result.content)
    assert response.has_key('tags')
    
    found_tag = None
    for tag in response['tags']:
        if tag['item_name'] == item_name:
            found_tag = tag
            break

    assert found_tag['quantity'] == int(quantity)


@step(r'I request pickup for (.+).')
def m(step, buy_name):
    url = reverse('api_create_pickup_request', kwargs={
        'resource_name': 'social_cart',
        'api_name': 'v1',
        'buy_pk': get_buy_pk(buy_name)
    })

    result = client_api_post(url, {})
    assert result.status_code == 201
    response = from_json(result.content)

    set_pickup_request_uri(buy_name, response['resource_uri'])


@step(r'I cancel pending Pickup Request for (.+).')
def n(step, buy_name):
    url = get_pickup_request_uri(buy_name)
    result = world.client.delete(url)
    assert result.status_code == 204


@step(r'I see Pickup Requests only for the following Social Buys:')
def o(step):
    expected_buy_ids = get_buy_ids(step)
    response = get_cart()

    for request in response['pickup_requests']:
        assert request['buy']['id'] in expected_buy_ids
    assert len(expected_buy_ids) == len(response['pickup_requests'])


@step(r'I see totally empty cart.')
def p(step):
    response = get_cart()

    assert len(response['buys']) == 0
    assert len(response['pending_shipping_requests']) == 0
    assert len(response['shipping_requests']) == 0
    assert len(response['pickup_requests']) == 0


@step(r'I see Shipping Requests only '
      r'for the following Social Buys:')
def r(step):
    expected_buy_ids = get_buy_ids(step)
    response = get_cart()

    for request in response['shipping_requests']:
        assert request['buy']['id'] in expected_buy_ids
    assert len(expected_buy_ids) == len(response['shipping_requests'])
