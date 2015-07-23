from datetime import datetime, timedelta
from wsgiref.headers import Headers
from wsgiref.util import request_uri
import cPickle as pickle
import logging
import os
import sys

import jwt

from .tbutil import Traceback


LOG = logging.getLogger(__name__)


class DebugAppMiddleware(object):
    debug_header = "OhOh-Debug-Token"
    token_ttl = timedelta(hours=1)
    secret = 'a51dfa470cae45bcd88b2e9ac5562fa5e26e5c5ce22ae62a2682e75a0d4d2c63'

    def __init__(self, app, debug_uri="/ohoh-debug"):
        LOG.log(logging.DEBUG + 5, "Setting environment variable: DEBUG=1")
        os.environ["DEBUG"] = "1"

        self._app = app

    def __call__(self, environ, start_response):
        uri = request_uri(environ, 0)
        LOG.log(logging.DEBUG + 5, "Received request to: %s", uri)

        # Dump the environ
        LOG.debug("Environ dump: \n%s", "\n".join([
            "    {0} = {1!r}".format(*item) for item in sorted(environ.items())
        ]))

        LOG.log(logging.DEBUG + 5, "Delegating request to wrapped WSGI app")
        try:
            return self._app(environ, start_response)
        except:
            LOG.exception("Received an exception. Preparing to debug...")
            return self.handle_application_error(environ, start_response)

    def handle_application_error(self, environ, start_response):
        status = "500 INTERNAL SERVER ERROR"
        headers = Headers([])

        # Package the exception info as into a special header and
        # send it to the client
        type, exc, tb = sys.exc_info()

        message = ["{0.__name__}: {1}".format(type, exc)]
        headers['Content-Type'] = 'text/plain'

        LOG.debug("Packing exception info into debug header: %s",
                  self.debug_header)
        pickled_tb = pickle.dumps(Traceback(tb))
        debug_header = self.pack_header(pickled_tb)
        LOG.debug("Debug header: %s", debug_header)
        headers[self.debug_header] = debug_header

        start_response(status, headers.items())
        return message

    def pack_header(self, context):
        payload = {
            "context": context
        }
        if self.token_ttl:
            payload['exp'] = datetime.utcnow() + self.token_ttl

        return jwt.encode(payload, self.secret, algorithm="HS256")
