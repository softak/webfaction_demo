import sys
import paypal as paypal_orig


class TestPayPalECResponse(paypal_orig.responses.PayPalECResponse):
    def __init__(self, raw, config):
        super(paypal_orig.responses.PayPalECResponse, self).__init__(raw)
        self.config = config    


class paypal(object):
    class PayPalECInterface(paypal_orig.PayPalECInterface):
        def set_express_checkout(self, receivers, **kwargs):
            return TestPayPalECResponse({
                'SUCCESS': [True],
                'TOKEN': ['123123123']
            }, self.config)

        def get_express_checkout_details(self, token, **kwargs):
            return TestPayPalECResponse({
                'SUCCESS': [True],
                'PAYERID': ['123123123']
            }, self.config)
        
        def do_express_checkout_payment(self, **kwargs):
            return TestPayPalECResponse({
                'SUCCESS': [True]
            }, self.config)

    def __getattr__(self, attr):
        return getattr(paypal_orig, attr)


def patch():
    # Should be called before django modules loaded, say in the ./manage.py
    sys.modules['paypal'] = paypal()
