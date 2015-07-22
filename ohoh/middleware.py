from wsgiref.util import request_uri
import logging
import os


LOG = logging.getLogger(__name__)


class DebugAppMiddleware(object):
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
        return self._app(environ, start_response)
