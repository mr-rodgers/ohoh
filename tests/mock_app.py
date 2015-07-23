from os import path


def mock_err_app(environ, start_response):
    # A mock WSGI app that throws an exception
    path.join("foo bar", 475564)


def echo(*args, **kwargs):
    for arg in args:
        print arg

    for arg in kwargs:
        print "{0!r}={1}".format(arg, kwargs[arg])
