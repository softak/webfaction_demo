class PayPalConfig(object):
    _valid_= {
        'API_ENVIRONMENT' : ['sandbox', 'production'],
    }

    _API_ENDPOINTS= {
        'sandbox': {
            'EC': 'api-3t.sandbox.paypal.com',
            'AP': 'svcs.sandbox.paypal.com',
        },
        'production': {
            'EC': 'api-3t.paypal.com',
            'AP': 'svcs.paypal.com',
        }
    }

    _PAYPAL_URL_BASE= {
        'sandbox' : 'https://www.sandbox.paypal.com/webscr',
        'production' : 'https://www.paypal.com/webscr',
    }

    API_ENVIRONMENT = 'sandbox'

    API_USERID = None
    API_PASSWORD = None
    API_SIGNATURE = None

    API_ENDPOINT = None
    PAYPAL_URL_BASE = None
       
    ACK_SUCCESS = 'SUCCESS'
    ACK_SUCCESS_WITH_WARNING = 'SUCCESSWITHWARNING'

    HTTP_TIMEOUT = 15

    def __init__(self, **kwargs):
        if 'API_ENVIRONMENT' not in kwargs:
            kwargs['API_ENVIRONMENT'] = self.API_ENVIRONMENT
        
        if kwargs['API_ENVIRONMENT'] not in self._valid_['API_ENVIRONMENT']:
            raise Exception('Invalid API_ENVIRONMENT')

        self.API_ENVIRONMENT = kwargs['API_ENVIRONMENT']

        self.API_ENDPOINT = self._API_ENDPOINTS[self.API_ENVIRONMENT]
        self.PAYPAL_URL_BASE = self._PAYPAL_URL_BASE[self.API_ENVIRONMENT]        
        
        for arg in ('API_USERID', 'API_PASSWORD', 'API_SIGNATURE',
                    'API_APPLICATION_ID'):
            if arg not in kwargs:
                raise Exception('Missing in PayPalConfig: %s ' % arg)
            setattr(self, arg, kwargs[arg])
                
        for arg in ['HTTP_TIMEOUT']:
            if arg in kwargs:
                setattr(self, arg, kwargs[arg])
