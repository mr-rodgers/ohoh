from __future__ import absolute_import
from io import TextIOBase
from wsgiref.simple_server import make_server as make_wsgi_server
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer
import logging
import server_reloader
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


def make_server(host, port, wsgi_app, use_debugger=True,
                server_class=_OhOhServer, handler_class=OhOhRequestHandler):
    if use_debugger:
        LOG.debug("Wrapping WSGI application: %r", wsgi_app)
        wsgi_app = DebugAppMiddleware(wsgi_app)

    return make_wsgi_server(host, port, wsgi_app, handler_class=handler_class)


def run_simple(host, port, wsgi_app, use_debugger=True, use_reloader=True,
               server_class=_OhOhServer, handler_class=OhOhRequestHandler):
    def start():
        # Create the server
        httpd = make_server(host, port, wsgi_app, server_class=server_class,
                            handler_class=handler_class)

        # And run it
        LOG.log(logging.INFO, "* Serving on %s:%d %s...",
                host, port, "with debugger" if use_debugger else "")

        if use_reloader is True:
            LOG.log(logging.INFO, "* Using reloader")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            LOG.log(logging.DEBUG + 5, "Keyboard Interrupt. Stopping server.")
            return

    def before_reload():
        LOG.log(logging.INFO, "* Restarting with reloader.")
        LOG.log(logging.INFO, "")

    if use_reloader is True:
        server_reloader.main(start, before_reload=before_reload)
    else:
        start()
