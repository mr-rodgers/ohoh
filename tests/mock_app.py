from os import path


def mock_err_app(environ, start_response):
    # A mock WSGI app that throws an exception
    path.join("foo bar", 475564)
