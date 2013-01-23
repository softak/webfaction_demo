import os
import re
import urlparse
import urllib
import httplib
import hmac
import base64
import hashlib


ppencode_re = re.compile(r'([A-Za-z0-9_]+)')

def ppencode(string):
    global ppencode_re
    result = ''
    for char in string:
        if re.match(ppencode_re, char) is None:
            result += '%' + hex(ord(char))[2:]
        elif char == ' ':
            result += '+'
        else:
            result += char
    return result


class Uri(object):
    scheme = None
    host = None
    port = None
    path = None

    def __init__(self, scheme=None, host=None, port=None,
                 path=None, query=None):
        self.query = query or {}
        if scheme is not None:
            self.scheme = scheme
        if host is not None:
            self.host = host
        if port is not None:
            self.port = port
        if path:
            self.path = path

    @staticmethod
    def parse_uri(uri_string):
        parts = urlparse.urlparse(uri_string)
        uri = Uri()
        if parts[0]:
            uri.scheme = parts[0]
        if parts[1]:
            host_parts = parts[1].split(':')
            if host_parts[0]:
                uri.host = host_parts[0]
            if len(host_parts) > 1:
                uri.port = int(host_parts[1])
        if parts[2]:
            uri.path = parts[2]

        if parts[4]:
            param_pairs = parts[4].split('&')
            for pair in param_pairs:
                pair_parts = pair.split('=')
                if len(pair_parts) > 1:
                    uri.query[urllib.unquote_plus(pair_parts[0])] = \
                            urllib.unquote_plus(pair_parts[1])
                elif len(pair_parts) == 1:
                    uri.query[urllib.unquote_plus(pair_parts[0])] = None
        return uri


class HttpRequest(object):
    method = None
    uri = None

    def __init__(self, uri=None, method=None, headers=None):
        self.headers = headers or {}
        self._body_parts = []
        if method is not None:
            self.method = method
        if isinstance(uri, (str, unicode)):
            uri = Uri.parse_uri(uri)
        self.uri = uri or Uri()


def build_oauth_base_string(http_request, consumer_key, signature_type,
                            timestamp, version, token):
    params = {}
    params['oauth_consumer_key'] = consumer_key
    params['oauth_signature_method'] = signature_type
    params['oauth_timestamp'] = str(timestamp)
    params['oauth_token'] = token
    params['oauth_version'] = version
    
    sorted_keys = sorted(params.keys())
  
    pairs = []
    for key in sorted_keys:
        pairs.append('%s=%s' % (key, params[key]))
    
    all_parameters = '&'.join(pairs)
    normalized_host = http_request.uri.host.lower()
    normalized_scheme = (http_request.uri.scheme or 'http').lower()
    non_default_port = None

    if (http_request.uri.port is not None
        and ((normalized_scheme == 'https' and http_request.uri.port != 443)
        or (normalized_scheme == 'http' and http_request.uri.port != 80))):
        non_default_port = http_request.uri.port
    
    path = http_request.uri.path or '/'
    request_path = None

    if not path.startswith('/'):
        path = '/%s' % path
    if non_default_port is not None:
        request_path = '%s://%s:%s%s' % (normalized_scheme, normalized_host,
                                         non_default_port, path)
    else:
        request_path = '%s://%s%s' % (normalized_scheme, normalized_host,
                                      path)
    
    base_string = '&'.join(
            (http_request.method.upper(),
             ppencode(request_path),
             ppencode(all_parameters)))
    return base_string


def generate_hmac_signature(http_request, consumer_key, consumer_secret,
                            timestamp, version, token, token_secret):
    base_string = build_oauth_base_string(
        http_request, consumer_key, 'HMAC-SHA1', timestamp, version, token)
    hash_key = '%s&%s' % (ppencode(consumer_secret), ppencode(token_secret))
    hashed = hmac.new(hash_key, base_string, hashlib.sha1)
    return base64.b64encode(hashed.digest())
