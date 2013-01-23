from datetime import datetime

from django.conf import settings
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.db import models, transaction
from django.db.models import Sum, Count, Q
from django.db.models.signals import post_delete, post_save
from django.contrib.auth.models import User

from stores.models import Item, Store

from paypal import PayPalConfig, PayPalAPInterface, PayPalECInterface
from utils import QuerySetManager, round_money


# TODO is it correct way to make Singleton?
paypal_config = PayPalConfig(
    API_ENVIRONMENT=settings.PP_API_ENVIRONMENT,
    API_USERID=settings.PP_API_USERID,
    API_PASSWORD=settings.PP_API_PASSWORD,
    API_SIGNATURE=settings.PP_API_SIGNATURE,
    API_APPLICATION_ID=settings.PP_API_APPLICATION_ID)

paypalAP = PayPalAPInterface(config=paypal_config)
paypalEC = PayPalECInterface(config=paypal_config)
# / TODO


class TransactionQuerySet(models.query.QuerySet):
    def approved(self):
        return self.filter(is_approved=True)

    def unapproved(self):
        return self.filter(is_approved=False)

    def for_tags(self, tags):
        ids = tags.values_list('transaction', flat=True).distinct()
        return self.filter(id__in=ids)


class Transaction(models.Model):
    is_approved = models.BooleanField(_('approved'),
        default=False)
    pay_key = models.CharField(_('PayPal pay key'),
        blank=True,
        max_length=50)
    payment_details = models.TextField(_('PayPal payment details'),
        blank=True,
        max_length=10000)

    objects = QuerySetManager(TransactionQuerySet)

    def __unicode__(self):
        return '%s, is approved: %s' % (self.pay_key, self.is_approved)

    def get_paypal_url(self):
        return paypalEC.generate_express_checkout_redirect_url(self.pay_key)

    @method_decorator(transaction.commit_on_success)
    def cancel(self):
        if self.is_approved:
            raise Exception('Can\'t cancel approved transaction.')
        
        from profiles.models import Profile
        Profile.objects.select_for_update().get(user=self.profile.user)

        self.personaltag_set.update(transaction=None)
        self.socialtag_set.update(transaction=None)
        self.shipping_requests.update(transaction=None)
        self.pickup_requests.update(transaction=None)

        self.profile.pending_transaction = None
        self.profile.save()

    @method_decorator(transaction.commit_on_success)
    def try_complete(self):
        from profiles.models import Profile
        Profile.objects.select_for_update().get(user=self.profile.user)

        details = paypalEC.get_express_checkout_details(self.pay_key)

        try:
            details.PAYERID
        except AttributeError: # User has not been logged in PayPal.
            return

        do_express_checkout_payment_params = {}
        for (idx, request) in enumerate(self.payment_requests.all()):
            prefix = lambda key: 'PAYMENTREQUEST_%d_%s' % (idx, key)
            do_express_checkout_payment_params.update({
                prefix('AMT'): request.amount,
                prefix('CURRENCYCODE'): request.currency_code,
                prefix('SELLERPAYPALACCOUNTID'): request.seller_paypal_account_id,
                prefix('PAYMENTREQUESTID'): request.payment_request_id
            })

        response = paypalEC.do_express_checkout_payment(
            TOKEN=self.pay_key,
            PAYERID=details.PAYERID,
            PAYMENTACTION='Sale',
            **do_express_checkout_payment_params)

        if response.success:
            self.is_approved = True
            if not self.profile:
                pass # TODO Raise something? Log? We just finished nobody's transaction!
            self.profile.pending_transaction = None
            self.profile.save()
            self.payment_details = str(response)
            self.save()
        else:
            if int(response.L_ERRORCODE0) == 10485:
                # Payment has not been authorized by the user.
                pass
            else:
                pass


class PaymentRequest(models.Model):
    """
    Transaction-related model. Nothing in common with ShippingRequest and
    PickupRequest.
    """
    transaction = models.ForeignKey(Transaction,
        related_name='payment_requests')
    currency_code = models.CharField(_('currency code'),
        default='USD',
        max_length='3')
    amount = models.DecimalField(_('amount'),
        max_digits=10,
        decimal_places=2)
    seller_paypal_account_id = models.CharField(_('seller PayPal account'),
        max_length='100')
    payment_request_id = models.CharField(
        max_length='100')


class ShippingRequest(models.Model):
    # If ShippingRequest contains SocialTags, `buy` must be not null and
    # point to SocialBuy.
    # If ShippingRequest contains PersonalTags, 'store' must be not null and
    # point to Store.
    # `buy` and `store` can't be both not null or both null at the same time.
    # TODO unify social & personal purchases
    buy = models.ForeignKey('SocialBuy',
        related_name='shipping_requests',
        null=True,
        blank=True)
    store = models.ForeignKey(Store,
        related_name='shipping_requests',
        null=True,
        blank=True)

    user = models.ForeignKey(User)
    address = models.CharField(_('full shipping address'),
        max_length='2000')

    transaction = models.ForeignKey(Transaction,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='shipping_requests')

    price = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True)
    priced_date = models.DateTimeField(
        blank=True,
        null=True)

    sent_date = models.DateTimeField(_('date shipped'),
        blank=True,
        null=True)

    class QuerySet(models.query.QuerySet):
        def responded(self):
            return self.filter(price__isnull=False)

        def not_responded(self):
            return self.unapproved().filter(price__isnull=True)

        def approved(self):
            return self.exclude(transaction__isnull=True) \
                       .exclude(transaction__is_approved=False)

        def unapproved(self):
            now = datetime.utcnow()
            d1 = now - settings.SHIPPING_PRICE_REQUEST_PROCESSING_PERIOD
            if_processing_period_left = Q(
                price__isnull=True,
                buy__isnull=False,
                buy__finish_date__lt=d1)

            d2 = now - settings.SHIPPING_PAY_PERIOD
            if_pay_period_left = Q(
                price__isnull=False,
                priced_date__lt=d2,
                buy__isnull=False,
                buy__finish_date__lt=now)

            return self.filter(Q(transaction__isnull=True) |
                               Q(transaction__is_approved=False)) \
                       .exclude(if_processing_period_left | if_pay_period_left)

        def for_tags(self, tags):
            ids = tags.values_list('shipping_request', flat=True).distinct()
            return self.filter(id__in=ids)

    objects = QuerySetManager(QuerySet)

    @property
    def is_approved(self):
        return self.transaction and self.transaction.is_approved

    def get_store(self):
        return self.store or (self.buy and self.buy.store)


class PickupRequest(models.Model):
    user = models.ForeignKey(User)
    buy = models.ForeignKey('SocialBuy',
        related_name='pickup_requests',
        null=True, blank=True)
    store = models.ForeignKey(Store,
        related_name='pickup_requests',
        null=True, blank=True)
    transaction = models.ForeignKey(Transaction,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='pickup_requests')
    code = models.CharField(_('pickup code'),
        max_length=100)
    pickup_date = models.DateTimeField(
        blank=True, null=True)

    class QuerySet(models.query.QuerySet):
        def approved(self):
            return self.exclude(transaction__isnull=True) \
                       .exclude(transaction__is_approved=False)

        def unapproved(self):
            return self.filter(Q(transaction__isnull=True) |
                               Q(transaction__is_approved=False)) \
                       .filter(buy__finish_date__gt=datetime.utcnow())

        def for_tags(self, tags):
            ids = tags.values_list('pickup_request', flat=True).distinct()
            return self.filter(id__in=ids)

    objects = QuerySetManager(QuerySet)


class Tag(models.Model):
    user = models.ForeignKey(User)
    item = models.ForeignKey(Item)
    quantity = models.PositiveIntegerField(_('item quantity'))
    transaction = models.ForeignKey(Transaction,
        null=True, blank=True, on_delete=models.SET_NULL)
    paid = models.DecimalField(_('amount paid'),
        max_digits=10, decimal_places=2,
        null=True, blank=True)
    shipping_request = models.ForeignKey(ShippingRequest,
        null=True, blank=True, on_delete=models.SET_NULL)
    pickup_request = models.ForeignKey(PickupRequest,
        null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        abstract = True

    @property
    def is_approved(self):
        return self.transaction and self.transaction.is_approved

    @property
    def original_price(self):
        """Returns original price of this tag."""
        return self.item.price * self.quantity

    class QuerySet(models.query.QuerySet):

        def draft(self):
            return self.unapproved().with_delivery_method_not_selected()

        def approved(self):
            return self.exclude(transaction__isnull=True)\
                       .exclude(transaction__is_approved=False)

        def unapproved(self):
            return self.filter(Q(transaction__isnull=True) |
                               Q(transaction__is_approved=False))

        def with_delivery_method_not_selected(self):
            return self.filter(shipping_request__isnull=True,
                               pickup_request__isnull=True)

        def with_pending_postage_request(self):
            return self.filter(shipping_request__isnull=False,
                               shipping_request__price__isnull=False)

        def with_pickup_selected(self):
            return self.filter(shipping_request__isnull=True,
                               pickup_request__isnull=False)

        def with_delivery_method_selected(self):
            return self.exclude(shipping_request__isnull=True,
                                pickup_request__isnull=True)\
                       .exclude(shipping_request__isnull=False,
                                shipping_request__price__isnull=True)


class PersonalTag(Tag):

    class Meta:
        unique_together = ('user', 'item', 'transaction')

    @property
    def price(self):
        """Returns current price of this tag."""
        return round_money(self.item.price * self.quantity)

    objects = QuerySetManager(Tag.QuerySet)


class SocialTag(Tag):
    buy = models.ForeignKey('SocialBuy',
        related_name='tags')

    @property
    def item_discounted_price(self):
        discount_group = self.item.discount_group
        buyers_number = self.buy.get_buyers_number(discount_group)
        items_number = self.buy.get_items_number(discount_group)

        if SocialTag.objects.filter(buy=self.buy, user=self.user) \
                            .approved().exists():
            buyers_delta = 0
        else:
            buyers_delta = 1

        result = self.buy.unapproved_tags\
                         .filter(item__discount_group=discount_group) \
                         .aggregate(items_number=Sum('quantity'))

        items_delta = result['items_number'] or 0

        if discount_group is None:
            discount = 1
        else:
            discount = discount_group.discount.apply(
                buyers_number=buyers_number+buyers_delta,
                items_number=items_number+items_delta)
        return round_money(self.item.price * discount)

    @property
    def price(self):
        """Returns current price of this tag."""
        result = self.quantity * self.item_discounted_price
        return round_money(result)

    class QuerySet(Tag.QuerySet):

        def unapproved(self):
            now = datetime.utcnow()

            d1 = now - settings.SHIPPING_PRICE_REQUEST_PROCESSING_PERIOD
            if_processing_period_left = Q(
                shipping_request__isnull=False,
                shipping_request__price__isnull=True,
                buy__finish_date__lt=d1)

            d2 = now - settings.SHIPPING_PAY_PERIOD
            if_pay_period_left = Q(
                shipping_request__price__isnull=False,
                shipping_request__priced_date__lt=d2,
                buy__finish_date__lt=now)

            return super(SocialTag.QuerySet, self).unapproved().exclude(
                if_processing_period_left | if_pay_period_left)

    objects = QuerySetManager(QuerySet)


class SocialBuy(models.Model):
    user = models.ForeignKey(User, related_name='social_buys')
    store = models.ForeignKey(Store, related_name='social_buys')
    start_date = models.DateTimeField(_('date started'), auto_now_add=True)
    finish_date = models.DateTimeField(_('date finished'))
    is_active = models.BooleanField(_('active'), default=False)
    is_finalized = models.BooleanField(_('finalized'), default=False)


    def __unicode__(self):
        return '%d' % self.id

    def merge_draft_tags(self, user):
        draft_tag_ids = self.draft_tags\
            .filter(user=user).values_list('id', flat=True)
        conflict_items = Item.objects.annotate(n=Count('socialtag'))\
            .filter(socialtag__id__in=draft_tag_ids).filter(n__gt=1)
        for item in conflict_items:
            tags_to_merge = self.draft_tags.filter(item=item, user=user)
            summary_quantity = tags_to_merge.aggregate(
                n=Sum('quantity'))['n']

            result_tag = SocialTag.objects.create(
                buy=self,
                item=item,
                user=user,
                quantity=summary_quantity)

            # We can't delete `tags_to_merge` before result tag created
            #, as social buy can become empty and then deleted. Also
            # `tags_to_merge` may contain result tag (due to queryset
            # lazyness), so we need to exclude result from queryset
            # explicilty.
            tags_to_merge.exclude(id=result_tag.id).delete()

    @property
    def approved_tags(self):
        return SocialTag.objects.filter(buy=self).approved()

    @property
    def unapproved_tags(self):
        return SocialTag.objects.filter(buy=self).unapproved()

    @property
    def draft_tags(self):
        return SocialTag.objects.filter(buy=self).draft()

    def get_items_number(self, discount_group):
        result = self.approved_tags\
            .filter(item__discount_group=discount_group)\
            .aggregate(items_number=Sum('quantity'))
        return result['items_number'] or 0

    def get_buyers_number(self, discount_group):
        return self.approved_tags\
            .filter(item__discount_group=discount_group)\
            .values('user').distinct().count()

    def get_price(self, user, item, quantity=1):
        """
        Returns the cost that user must pay in order to buy `quantity` of
        `item` through this buy.
        """
        discount_group = item.discount_group
        buyers_number = self.get_buyers_number(discount_group)
        items_number = self.get_items_number(discount_group)

        if SocialTag.objects.filter(buy=self, user=user).exists():
            buyers_delta = 0
        else:
            buyers_delta = 1

        result = self.unapproved_tags\
            .filter(item__discount_group=discount_group)\
            .aggregate(items_number=Sum('quantity'))

        items_delta = int(result['items_number'] or 0)

        if discount_group is None:
            discount = 1
        else:
            discount = discount_group.discount.apply(
                buyers_number=buyers_number+buyers_delta,
                items_number=items_number+quantity+items_delta)

        result = item.price * discount * quantity
        return round_money(result)

    class QuerySet(models.query.QuerySet):

        def for_user(self, user):
            buy_ids = SocialTag.objects\
                .filter(user=user).draft()\
                .values_list('buy', flat=True).distinct()
            return self.filter(id__in=buy_ids)

        def for_tags(self, tags):
            buy_ids = tags.values_list('buy', flat=True).distinct()
            return self.filter(id__in=buy_ids)

        def contains_draft_tags(self):
            return self.exclude(tags__transaction__is_approved=True)\
                       .filter(tags__shipping_request__isnull=True,
                               tags__pickup_request__isnull=True)\
                       .distinct()

        def for_transaction(self, transaction):
            buy_ids = transaction.socialtag_set.values_list('buy', flat=True) \
                                               .distinct()
            return self.filter(id__in=buy_ids)

        def unfinalized(self):
            return self.filter(is_finalized=False)

        def finalized(self):
            return self.filter(is_finalized=True)

        def unexpired(self):
            return self.filter(finish_date__gt=datetime.utcnow())

        def expired(self):
            return self.filter(finish_date__lte=datetime.utcnow())

        def active_or_created_by(self, user):
            return self.filter(Q(is_active=True) | Q(user=user))

    objects = QuerySetManager(QuerySet)


#TODO add docstring (how to use these functions)
def check_related_buy_on_emptiness(sender, **kwargs):
    buy = kwargs['instance'].buy
    if not (buy.is_active or buy.tags.exists()):
        buy.delete()

post_delete.connect(check_related_buy_on_emptiness,
        sender=SocialTag, dispatch_uid='apps.cart.models')

def mark_related_buy_active(sender, **kwargs):
    tag = kwargs['instance']
    if tag.is_approved:
        tag.buy.is_active = True
        tag.buy.save()

post_save.connect(mark_related_buy_active,
        sender=SocialTag, dispatch_uid='apps.cart.models')

def mark_related_buy_active2(sender, **kwargs):
    transaction = kwargs['instance']
    if transaction.is_approved:
        SocialBuy.objects.for_transaction(transaction) \
                         .update(is_active=True)

post_save.connect(mark_related_buy_active2,
        sender=Transaction, dispatch_uid='apps.cart.models')

def schedule_finish_buy_task(sender, **kwargs):
    buy = kwargs['instance']
    created = kwargs['created']
    if created:
        from cart.tasks import finalize_social_buy
        finalize_social_buy.apply_async(args=[buy], eta=buy.finish_date)
# post_save.connect(schedule_finish_buy_task,
#         sender=SocialBuy, dispatch_uid='apps.cart.models')
