from collections import namedtuple
from io import BytesIO
from wsgiref.headers import Headers
from wsgiref.simple_server import demo_app
from wsgiref.util import setup_testing_defaults
try:
    from urlparse import urlsplit
except ImportError:
    from urllib.parse import urlsplit

import pytest
from ohoh.middleware import DebugAppMiddleware

from mock_app import simple_err_app, stored_tb, stored_debugger_state


class Response(namedtuple("response", "status headers output")):
    @property
    def code(self):
        return int(self.status.split(' ')[0])

    @property
    def data(self):
        collect = BytesIO()
        for data in self.output:
            collect.write(data)
        return collect.getvalue()


def request(app, environ):
    resp_start = []
    def start_response(status, headers):
        resp_start.extend((status, Headers(headers)))

    result = app(environ, start_response)
    status, headers = resp_start

    return  Response(status, headers, result)


@pytest.fixture
def environ():
    env = {}
    setup_testing_defaults(env)
    return env


debug_middleware_args = [
    ({}, DebugAppMiddleware.debug_header, DebugAppMiddleware.debug_uri),
    ({'debug_header': "Debug-Header"},
     "Debug-Header", DebugAppMiddleware.debug_uri),
    ({'debug_uri': "/foo"},
     DebugAppMiddleware.debug_header, "/foo"),
    ({'debug_header': "Foo-Header", 'debug_uri': '/bar'},
     "Foo-Header", "/bar"),
]

@pytest.mark.parametrize("args,result_header,debug_uri",
                         debug_middleware_args)
def test_err_app_sends_debug_header(environ, args, result_header, debug_uri):
    application = DebugAppMiddleware(simple_err_app, **args)
    response = request(application, environ)
    assert result_header in response.headers
    assert "location" in response.headers

    print (response.headers['location'])
    uri_parts = urlsplit(response.headers['location'])

    assert uri_parts.path == debug_uri


@pytest.mark.parametrize("args,result_header,_",
                         debug_middleware_args)
def test_healthy_request_no_debug_header(environ, args, result_header, _):
    application = DebugAppMiddleware(demo_app, **args)
    response = request(application, environ)

    assert result_header not in response.headers
    assert "location" not in response.headers

@pytest.mark.parametrize("aug_environ, status", [
    ({"REQUEST_METHOD": "GET"}, 405),
    ({"REQUEST_METHOD": "PUT"}, 405),
    ({"REQUEST_METHOD": "DELETE"}, 405),
    ({"REQUEST_METHOD": "POST"}, 400), # No header
    ({"REQUEST_METHOD": "POST",
      "HTTP_" + DebugAppMiddleware.debug_header: "foo"}, 400)
])
def test_error_codes(environ, aug_environ, status):
    environ['PATH_INFO'] = DebugAppMiddleware.debug_uri
    environ.update(aug_environ)
    application = DebugAppMiddleware(demo_app)
    response = request(application, environ)

    assert response.code == status

@pytest.mark.parametrize("header,data,result", [
    (stored_tb, b"up",
     b"> c:\\python34\\lib\\ntpath.py(110)join()\n"
     b"-> p_drive, p_path = splitdrive(p)\n"),
    (stored_debugger_state, b"down",
     b"> c:\\python34\\lib\\ntpath.py(159)splitdrive()\n-> if len(p) > 1:\n")
])
def test_debug_request(environ, header, data, result):
    environ.update({
        'PATH_INFO': DebugAppMiddleware.debug_uri,
        "REQUEST_METHOD": "POST",
        "HTTP_" + DebugAppMiddleware.debug_header: header,
        "CONTENT_LENGTH": str(len(data)),
        "wsgi.input": BytesIO(data),
    })
    application = DebugAppMiddleware(demo_app)
    response = request(application, environ)

    print (response.data, result, sep='\n')
    assert response.data == result

