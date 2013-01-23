import decimal
from cart.features.buys_and_requests import *
from cart.models import ShippingRequest


@step(r'It\'s (\d+) hours later.')
def a(step, hours):
    datetime.set_delay({ 'hours': int(hours) })


@step(r'Seller respond to Shipping Request for (.+) and assign price (.+)\.')
def b(step, buy_name, price):
    shipping_request_resource_uri = get_shipping_request_uri(buy_name)

    shipping_request_pk = shipping_request_resource_uri.split('/')[-2]
    url = reverse('api_dispatch_detail', kwargs={
        'resource_name': 'pending_shipping_request',
        'api_name': 'v1',
        'pk': shipping_request_pk
    })
    client_api_put(url, { 'price': price })
