from urlparse import parse_qs
from pprint import pformat


class ResponseDict(object):
    def __init__(self, raw):
        self.raw = raw

    def __str__(self):
        return pformat(self.raw)

    def __getattr__(self, key):
        return self.get(key)

    def get(self, key):
        try:
            value = self.raw[key]
            if len(value) == 1:
                return value[0]
            return value
        except KeyError:
            raise AttributeError(self)


class PayPalAPResponse(ResponseDict):
    def __init__(self, query_string, config):
        raw = parse_qs(query_string)
        super(PayPalAPResponse, self).__init__(raw)

        self.config = config

        response_envelope = {}
        for (key, value) in self.raw.iteritems():
            if key.startswith('responseEnvelope.'):
                response_envelope[key.lstrip('responseEnvelope.')] = value

        self.response_envelope = ResponseDict(response_envelope)
        
    def __getattr__(self, key):
        if key == 'responseEnvelope':
            return self.response_envelope
        else:
            return super(PayPalAPResponse, self).__getattr__(key)
    
    @property
    def success(self):
        return self.responseEnvelope.ack.upper() in \
               (self.config.ACK_SUCCESS, self.config.ACK_SUCCESS_WITH_WARNING)


class PayPalECResponse(ResponseDict):
    def __init__(self, query_string, config):
        raw = parse_qs(query_string)
        super(PayPalECResponse, self).__init__(raw)
        self.config = config
    
    def get(self, key):
        key = key.upper()
        return super(PayPalECResponse, self).get(key)

    @property
    def success(self):
        return self.ack.upper() in (self.config.ACK_SUCCESS, 
                                    self.config.ACK_SUCCESS_WITH_WARNING)
