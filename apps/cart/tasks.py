from datetime import datetime, timedelta
from collections import defaultdict

from django.conf import settings

from celery.task import task

from cart.models import Transaction, paypalEC

# TODO
# Code below is a draft code.

@task
def try_finalize_social_buy(buy):
    transactions = Transaction.objects.for_tags(buy.socialtag_set) \
                                      .unapproved()
    for transaction in transactions:
        transaction.cancel()

    # Remove all pickup requests
    pickup_requests = PickupRequest.objects.for_tags(buy.socialtag_set) \
                                           .unapproved()
    pickup_requests.delete()

    # Remove all shipping requests
    shipping_requests = ShippingRequest.objects.for_tags(buy.socialtag_set) \
                                               .unapproved()
    shipping_requests.delete()

    # Remove all draft tags (some of them becomes draft after request deletion)
    buy.draft_tags.delete()

    # If buy contains only approved tags, we can emit discount and
    # mark buy as finalized.
    if not buy.unapproved_tags.exists():
        emit_discounts(buy)
        buy.is_finalized = True
        buy.save()


def emit_discounts(buy):
    tags_by_transactions = defaultdict(list)
    
    for tag in buy.approved_tags:
        tags_by_transactions[tag.transaction].append(tag)

    for transaction, tags in tags_by_transactions.iteritems():
        final_discount = 0
        for tag in tags:
            final_discount += tag.paid - tag.price * settings.SD_FEE

        response = paypalEC.refund(
            [{
                'amount': final_discount,
                'email': buy.store.paypal_email
            }],
            currencyCode='USD',
            payKey=transaction.pay_key)
