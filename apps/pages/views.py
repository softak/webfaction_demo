import commonware
import simplejson as json
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from django.core.urlresolvers import reverse
from django.conf import settings
from session_csrf import anonymous_csrf
from stores.models import Store, Category, Item
from stores.resources import StoreResource

log = commonware.log.getLogger('sd')


def home(request):
    stores = Store.objects.filter(is_active=True)
    return render(request, 'pages/home.j.html', {
        'stores': stores
    })

@anonymous_csrf
@csrf_protect
def new_home(request):
    stores = Store.objects.filter(is_active=True)

    categories = Category.objects.all().filter(id__in=
        stores.values_list('category', flat=True))

    data = {
        'stores': stores,
        'stores_json': StoreResource().to_json(obj=stores, request=request),
        'categories': categories,
        'categories_json': json.dumps(
            list(categories.values('id', 'name'))),

        #TODO
        'sample_items': Item.objects.all()
    }
    return render(request, 'pages/new_home.j.html', data)


from paypal import PayPalConfig, PayPalAPInterface
interface = PayPalAPInterface(config=PayPalConfig(
    API_ENVIRONMENT=settings.PP_API_ENVIRONMENT,
    API_USERID=settings.PP_API_USERID,
    API_PASSWORD=settings.PP_API_PASSWORD,
    API_SIGNATURE=settings.PP_API_SIGNATURE,
    API_APPLICATION_ID=settings.PP_API_APPLICATION_ID
))


# Sandbox login/password to manage test accounts:
# RRHUBJOHHN@GMAIL.COM / shoppingdomain
# Test accounts:
# sllr1_1319977604_biz@gmail.com / 12345678
# sllr2_1319978021_biz@gmail.com / 12345678
# sllr3_1324111206_biz@gmail.com / 12345678
# buyer1_1319977758_per@gmail.com / 12345678

def request_refund_permission(request):
    response = interface._call2('RequestPermissions', '/Permissions/',
        callback=request.build_absolute_uri(reverse('pages.rrp_callback')),
        scope='REFUND'
    )
    return render(request, 'pages/paypal1.j.html', {
        'paypal_url': interface.generate_permissions_redirect_url(response.token)
    })

def request_refund_permission_callback(request):
    request_token, verification_code = request.GET.get('request_token'), request.GET.get('verification_code')
    response = interface._call2('GetAccessToken', '/Permissions/',
        token=request_token,
        verifier=verification_code
    )
    print response
    return render(request, 'pages/paypal2.j.html', {})

from django.core.cache import cache
def make_parallel_payment(request):
    response = interface.pay(
        [
            {
                'email': 'sllr1_1319977604_biz@gmail.com',
                'amount': '5.00',
                'primary': 'false'
            },
            {
                'email': 'sllr2_1319978021_biz@gmail.com',
                'amount': '5.00',
                'primary': 'false'
            },
        ],

        returnUrl=request.build_absolute_uri(reverse('pages.mpp_callback')),
        cancelUrl=request.build_absolute_uri(reverse('pages.mpp')),
        currencyCode='USD',
        actionType='PAY',
        feesPayer='SENDER'
    )
    cache.set('pay_key', response.payKey, 60*60*1000)
    return render(request, 'pages/paypal1.j.html', {
        'paypal_url': interface.generate_payment_redirect_url(response.payKey)
    })
import re
from collections import defaultdict

def make_parallel_payment_callback(request):
    pay_key = cache.get('pay_key')
    print 'paymentdet', pay_key
    response = interface._call('PaymentDetails',
        payKey=pay_key
    )
    print 'paymentdetdone'
    payment_info = defaultdict(dict)
    p = re.compile('paymentInfoList.paymentInfo\((\d+)\)\.(.+)')
    for (key, value) in response.raw.iteritems():
        m = p.match(key)
        if m:
            payment_info[int(m.group(1))][m.group(2)] = value
    print payment_info[1]
    print 'ref'
    response = interface.refund([
            { 'amount': '1.00',
              'email': payment_info[1]['receiver.email'][0] } # TODO
        ],
        currencyCode='USD',
        transactionId=payment_info[1]['transactionId'][0]
    )
    print 'refdone'
    print response
    return render(request, 'pages/paypal2.j.html', {
    })

# Without permission:
"""
{'currencyCode': ['USD'],
 'refundInfoList.refundInfo(0).receiver.amount': ['5.00'],
 'refundInfoList.refundInfo(0).receiver.email': ['sllr2_1319978021_biz@gmail.com'],
 'refundInfoList.refundInfo(0).refundStatus': ['NO_API_ACCESS_TO_RECEIVER'],
 'responseEnvelope.ack': ['Success'],
 'responseEnvelope.build': ['2279004'],
 'responseEnvelope.correlationId': ['dd5104ee722ae'],
 'responseEnvelope.timestamp': ['2011-12-06T07:32:56.612-08:00']}
"""

# With
"""
{'currencyCode': ['USD'],
 'refundInfoList.refundInfo(0).encryptedRefundTransactionId': ['9CB47322JL1123748'],
 'refundInfoList.refundInfo(0).receiver.amount': ['5.00'],
 'refundInfoList.refundInfo(0).receiver.email': ['sllr2_1319978021_biz@gmail.com'],
 'refundInfoList.refundInfo(0).refundFeeAmount': ['0.00'],
 'refundInfoList.refundInfo(0).refundGrossAmount': ['5.00'],
 'refundInfoList.refundInfo(0).refundHasBecomeFull': ['true'],
 'refundInfoList.refundInfo(0).refundNetAmount': ['5.00'],
 'refundInfoList.refundInfo(0).refundStatus': ['REFUNDED'],
 'refundInfoList.refundInfo(0).refundTransactionStatus': ['COMPLETED'],
 'refundInfoList.refundInfo(0).totalOfAllRefunds': ['5.00'],
 'responseEnvelope.ack': ['Success'],
 'responseEnvelope.build': ['2279004'],
 'responseEnvelope.correlationId': ['71b229d944285'],
 'responseEnvelope.timestamp': ['2011-12-06T07:34:28.480-08:00']}
"""
