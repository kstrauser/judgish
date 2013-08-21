#!/usr/bin/env python

import json
import os
import urllib
import urlparse
import webbrowser
import BaseHTTPServer

TOKEN_FILE = os.path.expanduser('~/.judgish-tokens')

CLIENT_ID = 'XJtBFQwBesZHYE4TGcFwzvfq6D6a7NCa'

AUTH_URL = 'https://account.app.net/oauth/authenticate?' + \
    urllib.urlencode({
        'client_id': CLIENT_ID,
        'response_type': 'token',
        'scope': 'stream,public_messages',
        'redirect_uri': 'http://localhost:8000',
    })

PORT = 8000

TEMPLATE_SUCCESS = """
<html>
<body><p>Thanks! You may close this window now.</p></body>
</html>
"""

TEMPLATE_FAIL = """
<html>
<body><p>Something bad happened!</p></body>
</html>
"""

TEMPLATE_REDIRECT = """
<html>
<head>
<script>
window.location = window.location.toString().replace('#', '?');
</script>
</head>
</html>
"""


class AuthHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        if '?' in self.path:
            querystring = urlparse.urlparse(self.path).query
            querydict = urlparse.parse_qs(querystring)
            try:
                self.server.access_token = querydict['access_token'][0]
            except KeyError:
                template = TEMPLATE_FAIL
            else:
                template = TEMPLATE_SUCCESS

            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(template)
            self.wfile.close()
        else:
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(TEMPLATE_REDIRECT)
            self.wfile.close()


class TokenBucket(object):
    def __init__(self):
        try:
            with open(TOKEN_FILE) as token_file:
                self.tokens = json.loads(token_file.read())
        except IOError:
            self.tokens = {}

    def write(self):
        with open(TOKEN_FILE, 'w') as token_file:
            token_file.write(json.dumps(self.tokens, indent=4))

    def get(self, username, system):
        return self.tokens.get(self._get_key(username, system))

    def set(self, username, system, access_token):
        self.tokens[self._get_key(username, system)] = access_token

    def unset(self, username, system):
        try:
            del self.tokens[self._get_key(username, system)]
        except KeyError:
            pass

    @staticmethod
    def _get_key(username, system):
        return '%s@%s' % (username, system)


def fetch_adn_access_token():
    webbrowser.open(AUTH_URL)

    httpd = BaseHTTPServer.HTTPServer(("", PORT), AuthHandler)
    httpd.access_token = None

    while httpd.access_token is None:
        httpd.handle_request()

    httpd.server_close()

    return httpd.access_token


def get_access_token(username, system):
    bucket = TokenBucket()

    token = bucket.get(username, system)
    if token is not None:
        return token

    if system == 'adn':
        token = fetch_adn_access_token()
    else:
        raise ValueError('Unknown system: %s' % system)

    bucket.set(username, system, token)
    bucket.write()

    return token


if __name__ == '__main__':
    print 'Access_token:', get_access_token('kirks', 'adn')
