from __future__ import absolute_import
from io import TextIOBase
from wsgiref.simple_server import make_server, WSGIRequestHandler, WSGIServer
import logging
import sys

from .middleware import DebugAppMiddleware
import ohoh


LOG = logging.getLogger(__name__)


class ErrOutLogger(TextIOBase):
    def write(self, s):
        LOG.error(s)
        return len(s)


class OhOhRequestHandler(WSGIRequestHandler):
    server_version = "OhOh/" + ohoh.__version__

    def get_stderr(self):
        return ErrOutLogger()

    def log_message(self, format, *args):
        pass


class _OhOhServer(WSGIServer):
    def handle_error(self, request, client_address):
        et, ev, tb = sys.exc_info()
        if issubclass(et, KeyboardInterrupt):
            raise ev
        else:
            LOG.exception("Exception occurred during request from %s:%d",
                          *client_address)


def run_simple(host, port, wsgi_app, use_debugger=True,
               server_class=_OhOhServer,
               handler_class=OhOhRequestHandler):
    if use_debugger:
        LOG.debug("Wrapping WSGI application: %r", wsgi_app)
        wsgi_app = DebugAppMiddleware(wsgi_app)

    # Construct the server
    httpd = make_server(host, port, wsgi_app, handler_class=handler_class)

    # Run the server
    LOG.log(logging.INFO + 5, "* Serving on %s:%d %s...",
            host, port, "with debugger" if use_debugger else "")
    try:
        return httpd.serve_forever()
    except KeyboardInterrupt:
        LOG.log(logging.DEBUG + 5, "Keyboard Interrupt. Stopping server.")
        return
