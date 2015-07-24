from base64 import b64decode, b64encode
from codecs import EncodedFile
from datetime import datetime, timedelta
from io import BytesIO
from pdb import Pdb
from StringIO import StringIO
from wsgiref.headers import Headers
from wsgiref.util import application_uri, request_uri
import bz2
import logging
import os
import re
import sys
import traceback

import dill as pickle
import jwt

from .tbutil import Traceback


LOG = logging.getLogger(__name__)


class DebugAppMiddleware(object):
    debug_header = "OhOh-Debug-Token"
    token_ttl = timedelta(hours=1)
    secret = 'a51dfa470cae45bcd88b2e9ac5562fa5e26e5c5'
    debug_uri = "/ohoh-debug/"
    max_content_length = 1024

    def __init__(self, app, **args):
        LOG.log(logging.DEBUG + 5, "Setting environment variable: DEBUG=1")
        os.environ["DEBUG"] = "1"

        self._app = app

        for arg in args:
            setattr(self, arg, args[arg])

    def __call__(self, environ, start_response):
        uri = request_uri(environ, 0)
        LOG.log(logging.DEBUG + 5, "Received request to: %s", uri)

        # Dump the environ
        LOG.debug("Environ dump: \n%s", "\n".join([
            "    {0} = {1!r}".format(*item) for item in sorted(environ.items())
        ]))

        if environ['PATH_INFO'] == self.debug_uri:
            LOG.log(logging.DEBUG + 5,
                    "Handling debug request")
            return self.handle_debug_request(environ, start_response)
        else:
            LOG.log(logging.DEBUG + 5,
                    "Delegating request to wrapped WSGI app")
            try:
                return self._app(environ, start_response)
            except:
                LOG.exception("Received an exception. Preparing to debug...")
                return self.handle_application_error(environ, start_response)

    def handle_debug_request(self, environ, start_response):
        if environ['REQUEST_METHOD'] != 'POST':
            LOG.debug("Request method invalid.")
            start_response('405 Method Not Allowed', [])
            return []

        request_headers = get_headers(environ)
        debug_token = request_headers[self.debug_header]
        LOG.debug("Unpacking context from debug header '%s: %s'",
                  self.debug_header, debug_token)
        obj  = self.unpack_header(request_headers[self.debug_header])

        if obj is None:
            LOG.debug("Debug header invalid.")
            start_response("400 Bad Request", [])
            return []

        LOG.debug("Successfully unpacked: %s", obj)

        infile = environ['wsgi.input']
        input_encoding = get_content_charset(request_headers)
        outfile = StringIO()
        debugger = Pdb(stdin=BytesIO(), stdout=outfile)

        LOG.debug("Setting up the debugger.")
        if isinstance(obj, Traceback):
            # Start up the request Pdb debugger
            debugger.setup(None, obj)
            debugger.botframe = obj.tb_frame

        elif isinstance(obj, tuple):
            # It was a state-save of the pdb obj
            lineno, stack, curindex, curframe, cfl, btfm = obj
            debugger.lineno = lineno
            debugger.stack = stack
            debugger.curindex = curindex
            debugger.curframe = curframe
            debugger.curframe_locals = cfl
            debugger.botframe = btfm

        else:
            LOG.debug("Unknown context: %r", obj)
            start_response("500 Internal Server Error", [])
            return []

        # Read the text from the input stream
        n = min(
            int(request_headers.get(
                'content-length', self.max_content_length)),
            self.max_content_length
        )
        LOG.debug("Reading at most %d bytes from client.", n)
        text_bytes = infile.read(n)
        LOG.debug("Converting bytes to text using charset %r",
                  input_encoding)
        text = text_bytes.decode(input_encoding)

        LOG.debug("Sending command to debugger: %r", text)
        stop = debugger.onecmd(text)

        response = outfile.getvalue()
        LOG.debug("Debugger response: %r", response)

        headers = [("Content-Type", "text/plain")]

        if stop:
            LOG.debug("Done debugging. Not sending a header.")

        else:
            # Save the state of the debugger
            state = (
                debugger.lineno,
                debugger.stack,
                debugger.curindex,
                debugger.curframe,
                debugger.curframe_locals,
                debugger.botframe
            )
            LOG.debug("Debugger state: %r", state)
            LOG.debug("Packing debugger state into debug header: %s",
                      self.debug_header)
            debug_header = self.pack_header(state)
            LOG.debug("Debug header (%d bytes): %s",
                      len(debug_header), debug_header)
            headers.append((self.debug_header, debug_header))

        start_response("200 OK", headers)
        return [response]

    def handle_application_error(self, environ, start_response):
        status = "500 Internal Server Error"
        headers = Headers([])

        # Package the exception info as into a special header and
        # send it to the client
        type, exc, tb = sys.exc_info()

        tbfile = StringIO()
        traceback.print_exc(file=tbfile)
        headers['Content-Type'] = 'text/plain'

        LOG.debug("Packing traceback context into debug header: %s",
                  self.debug_header)
        debug_header = self.pack_header(Traceback(tb))
        LOG.debug("Debug header (%d bytes): %s",
                  len(debug_header), debug_header)
        headers[self.debug_header] = debug_header

        app_uri = application_uri(environ)
        headers["Location"] = app_uri + self.debug_uri

        start_response(status, headers.items())
        return [tbfile.getvalue()]

    def pack_header(self, context):
        pickled = pickle.dumps(context)
        compressed = bz2.compress(pickled)
        b64dump = b64encode(compressed)
        payload = {
            "context": b64dump.decode('ascii')
        }
        if self.token_ttl:
            payload['exp'] = datetime.utcnow() + self.token_ttl

        return jwt.encode(payload, self.secret, algorithm="HS256")

    def unpack_header(self, header):
        try:
            b64dump = jwt.decode(
                header, self.secret, algorithms=["HS256"]
            )['context'].encode('ascii')
            compressed = b64decode(b64dump)
            pickled = bz2.decompress(compressed)
            return pickle.loads(pickled)
        except:
            LOG.exception("Trouble unpacking debug header: %s", header)
            return None


def get_headers(environ):
    headers = Headers([
        (name[5:].replace("_", "-"), environ[name]) for name in environ
        if name.startswith("HTTP_")
    ])
    headers['Content-Type'] = environ['CONTENT_TYPE']
    headers['Content-Length'] = environ['CONTENT_LENGTH']
    return headers

def get_content_charset(headers, default="utf-8"):
    content_type_header = headers['content-type']
    if content_type_header is None:
        return default

    m = re.search("charset=(?P<charset>[-\w]+)", content_type_header)
    if m is None:
        return default

    return m['charset']
