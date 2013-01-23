from decimal import *
from utils import to_json, round_money
from collections import defaultdict

from django.db import transaction
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.http import Http404
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from cart.resources import SocialCartResource, PersonalCartResource
from cart.models import PersonalTag, SocialTag, \
                        Transaction, PaymentRequest, \
                        ShippingRequest, PickupRequest, \
                        paypalEC
from profiles.models import Profile


@login_required
def personal_cart(request):
    data = PersonalCartResource().to_dict(obj=request.user, request=request)
    return render(request, 'cart/personal_cart.j.html', {
        'cart_json': to_json(data),
        'is_empty': not data['buys']
    })


@login_required
def social_cart(request):
    data = SocialCartResource().to_dict(obj=request.user, request=request)
    return render(request, 'cart/social_cart.j.html', {
        'cart_json': to_json(data),
        'is_empty': not data['buys'] and \
                    not data['pending_shipping_requests'] and \
                    not data['pickup_requests'] and \
                    not data['shipping_requests']
    })


@login_required
def preview_social_cart(request):
    return render(request, 'cart/social_cart_preview.j.html', {
        'cart': SocialCartResource().to_dict(obj=request.user,
                                             request=request)
    })


@login_required
def preview_personal_cart(request):
    tags = PersonalTag.objects.filter(user=request.user).unapproved()
    return render(request, 'cart/personal_cart_preview.j.html', {
        'cart': PersonalCartResource().to_dict(obj=request.user,
                                               request=request),
        'total_price': reduce(lambda sum, tag: sum + tag.price, tags, 0)
    })


def _get_payment_requests(tags_by_stores,
                         shipping_requests_by_stores,
                         fee_percent):
    payment_requests = []
    sd_fee_amount = 0

    for (store, tags) in tags_by_stores.iteritems():
        store_amount = 0
        for tag in tags:
            sd_fee_amount += tag.price  * (1 - fee_percent)
            tag.paid = tag.price * fee_percent
            store_amount += tag.paid
            tag.save()

        shipping_price = 0
        if shipping_requests_by_stores.has_key(store):
            for shipping_request in shipping_requests_by_stores[store]:
                # Should we charge fee from shipping?
                shipping_price += shipping_request.price

        payment_requests.append({
            'CURRENCYCODE': 'USD',
            'AMT': round_money(store_amount) + round_money(shipping_price),
            'SHIPPINGAMT': round_money(shipping_price),
            'ITEMAMT': round_money(store_amount),
            'SELLERPAYPALACCOUNTID': store.paypal_email,
            'PAYMENTREQUESTID': store.paypal_email,
        })

    payment_requests.append({
        'CURRENCYCODE': 'USD',
        'AMT': round_money(sd_fee_amount),
        'SELLERPAYPALACCOUNTID': settings.PP_API_EMAIL,
        'PAYMENTREQUESTID': settings.PP_API_EMAIL
    })

    return payment_requests


# SOCIAL CART
@login_required
@transaction.commit_on_success
def approve_cart(request, cart=None):
    user = request.user
    profile = Profile.objects.select_for_update().get(user=user)

    if not profile.pending_transaction is None:
        raise Http404

    tags = SocialTag.objects.filter(user=user) \
                            .unapproved() \
                            .with_delivery_method_selected() \
                            .select_related('item', 'item__store')
    shipping_requests = ShippingRequest.objects.for_tags(tags)
    pickup_requests = PickupRequest.objects.for_tags(tags)

    tags_by_stores = defaultdict(list)
    for tag in tags:
        store = tag.item.store
        tags_by_stores[store].append(tag)

    shipping_requests_by_stores = defaultdict(list)
    for shipping_request in shipping_requests:
        store = shipping_request.buy.store
        shipping_requests_by_stores[store].append(shipping_request)

    if len(tags_by_stores) > 8:
        raise Http404

    payment_requests = _get_payment_requests(
        tags_by_stores,
        shipping_requests_by_stores,
        settings.SD_FEE)
    
    return_url = request.build_absolute_uri(reverse('cart.social_cart'))
    response = paypalEC.set_express_checkout(
        payment_requests,
        NOSHIPPING=1,
        RETURNURL=return_url,
        CANCELURL=return_url)
    
    if response.success:
        transaction_ = Transaction.objects.create(pay_key=response.token)

        for payment_request in payment_requests:
            PaymentRequest.objects.create(
                transaction=transaction_,
                currency_code=payment_request['CURRENCYCODE'],
                amount=payment_request['AMT'],
                seller_paypal_account_id=payment_request['SELLERPAYPALACCOUNTID'],
                payment_request_id=payment_request['PAYMENTREQUESTID'])

        # Order is _important_. First we update requests and then tags. 
        # Somehow it happens that `shipping_requests` and `pickup_requests`
        # querysets re-evaluated when `tags` updated and becomes empty (as 
        # there is no `draft` tags after 
        # `tags.update(transaction=transaction_)`.
        shipping_requests.update(transaction=transaction_)
        pickup_requests.update(transaction=transaction_)
        tags.update(transaction=transaction_)

        profile.pending_transaction = transaction_
        profile.save()

        # `useraction=commit` turns "Continue" button to "Pay now"
        return redirect(
            transaction_.get_paypal_url() + '&useraction=commit')


@login_required
@transaction.commit_on_success
def cancel_pending_transaction(request):
    transaction = request.user.profile.pending_transaction
    redirect_to = request.GET.get('back', 'cart.social_cart')

    if not transaction is None:
        transaction.cancel()

    return redirect(redirect_to)
