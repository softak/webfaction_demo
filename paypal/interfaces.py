import httplib
import collections
import types
import time
from urllib import urlencode

from .signatures import generate_hmac_signature, HttpRequest
from .responses import *


class PayPalAPInterface(object):

    def __init__(self, config=None, **kwargs):
        if config:
            self.config = config
        else:
            self.config = PayPalConfig(**kwargs)

    def _encode_utf8(self, kwargs):
        unencoded_pairs = kwargs
        for i in unencoded_pairs.keys():
            if isinstance(unencoded_pairs[i], types.UnicodeType):
                unencoded_pairs[i] = unencoded_pairs[i].encode('utf-8')
        return unencoded_pairs 

    def generate_preapproval_redirect_url(self, preapproval_key):
        url_vars = (self.config.PAYPAL_URL_BASE, preapproval_key)
        return '%s?cmd=_ap-preapproval&preapprovalkey=%s' % url_vars

    def generate_permissions_redirect_url(self, request_token):
        url_vars = (self.config.PAYPAL_URL_BASE, request_token)
        return '%s?cmd=_grant-permission&request_token=%s' % url_vars

    def generate_payment_redirect_url(self, pay_key):
        url_vars = (self.config.PAYPAL_URL_BASE, pay_key)
        return '%s?cmd=_ap-payment&paykey=%s' % url_vars

    def _call(self, method, part, xppheader=None, **kwargs):
        headers = {
            'X-PAYPAL-APPLICATION-ID': self.config.API_APPLICATION_ID,
            'X-PAYPAL-REQUEST-DATA-FORMAT': 'NV',
            'X-PAYPAL-RESPONSE-DATA-FORMAT': 'NV'
        }

        if xppheader is None:
            headers.update({
                'X-PAYPAL-SECURITY-USERID': self.config.API_USERID,
                'X-PAYPAL-SECURITY-PASSWORD': self.config.API_PASSWORD, 
                'X-PAYPAL-SECURITY-SIGNATURE': self.config.API_SIGNATURE,
            })
        else:
            headers.update({
                'X-PAYPAL-AUTHORIZATION': xppheader
            })

        params = collections.OrderedDict()
        for key in sorted(kwargs.iterkeys()): # Ordering is important!
            params[key] = kwargs[key]

        params.update({
            'requestEnvelope.errorLanguage': 'en_US',
            'requestEnvelope.detailLevel': 'ReturnAll'
        })

        enc_params = urlencode(self._encode_utf8(params))

        if part == '/AdaptivePayments/':
            api_endpoint = self.config.API_ENDPOINT['AP']
        elif part == '/Permissions/':
            api_endpoint = self.config.API_ENDPOINT['AP']
        
        conn = httplib.HTTPSConnection(api_endpoint,
                                       timeout=self.config.HTTP_TIMEOUT)
        conn.request('POST', part + method, enc_params, headers)
        response = conn.getresponse()
        response = PayPalAPResponse(response.read(), self.config)
        conn.close()

        return response

    def callAP(self, method, **kwargs):
        return self._call(method, '/AdaptivePayments/', **kwargs)

    def callPermissions(self, method, **kwargs):
        return self._call(method, '/Permissions/', **kwargs)
    
    def callPermissionsOnBehalf(self, method, access_token=None,
                                secret_token=None, **kwargs):
        timestamp = int(time.time())
        uri = 'https://%s/Permissions/GetBasicPersonalData' % \
                self.config.API_ENDPOINT
        http_request = HttpRequest(uri=uri, method='POST')
        signature = generate_hmac_signature(
                http_request, self.config.API_USERID, self.config.API_PASSWORD,
                timestamp, '1.0', access_token, secret_token)
        xppheader = 'timestamp=%d,token=%s,signature=%s' % \
                (timestamp, access_token, signature)
        return self._call(method, '/Permissions/', xppheader=xppheader, **kwargs)

    def pay(self, receivers, **kwargs):
        for index, receiver in enumerate(receivers):
            for key, value in receiver.iteritems():
                arg_name = 'receiverList.receiver(%d).%s' % (index, key)
                kwargs[arg_name] = receiver[key]
        return self.callAP('Pay', **kwargs)

    def refund(self, receivers, **kwargs):
        for index, receiver in enumerate(receivers):
            for key, value in receiver.iteritems():
                arg_name = 'receiverList.receiver(%d).%s' % (index, key)
                kwargs[arg_name] = receiver[key]
        return self.callAP('Refund', **kwargs)

    def get_payment_details(self, pay_key):
        return self.callAP('PaymentDetails', payKey=pay_key)
    
    def set_payment_options(self, pay_key):
        return self.callAP('SetPaymentOptions', payKey=pay_key)

    def execute_payment(self, pay_key):
        return self.callAP('ExecutePayment', payKey=pay_key)


class PayPalECInterface(object):

    def __init__(self , config=None, **kwargs):
        if config:
            self.config = config
        else:
            self.config = PayPalConfig(**kwargs)

    def _encode_utf8(self, kwargs):
        unencoded_pairs = kwargs
        for i in unencoded_pairs.keys():
            if isinstance(unencoded_pairs[i], types.UnicodeType):
                unencoded_pairs[i] = unencoded_pairs[i].encode('utf-8')
        return unencoded_pairs 

    def generate_express_checkout_redirect_url(self, token):
        url_vars = (self.config.PAYPAL_URL_BASE, token)
        return '%s?cmd=_express-checkout&token=%s' % url_vars

    def _call(self, method, **kwargs):
        params = collections.OrderedDict({
            'USER': self.config.API_USERID,
            'PWD': self.config.API_PASSWORD,
            'SIGNATURE': self.config.API_SIGNATURE,
            'VERSION': '85.0',
            'METHOD': method
        })

        for key in sorted(kwargs.iterkeys()): # Ordering is important!
            params[key] = kwargs[key]

        enc_params = urlencode(self._encode_utf8(params))
        conn = httplib.HTTPSConnection(self.config.API_ENDPOINT['EC'],
                                       timeout=self.config.HTTP_TIMEOUT)
        conn.request('POST', '/nvp/', enc_params)
        response = conn.getresponse()
        response = PayPalECResponse(response.read(), self.config)
        conn.close()

        return response

    def set_express_checkout(self, receivers, **kwargs):
        for index, receiver in enumerate(receivers):
            for key, value in receiver.iteritems():
                kwargs['PAYMENTREQUEST_%d_%s' % (index, key)] = receiver[key]
        return self._call('SetExpressCheckout', **kwargs)

    def get_express_checkout_details(self, token, **kwargs):
        kwargs['TOKEN'] = token
        return self._call('GetExpressCheckoutDetails', **kwargs)
    
    def do_express_checkout_payment(self, **kwargs):
        return self._call('DoExpressCheckoutPayment', **kwargs)
