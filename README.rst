ohoh
====

|build-status| |license|


OhOh is a debugger for your WSGI applications. Using OhOh, you can inspect
the stack frames of a wsgi app that's thrown an exception.

Usage
-----

Use this command to serve your wsgi app in debug mode::

    > ohoh "package.module:wsgi_app" -s host:port

For a full range of options, see ``ohoh -h``

OhOh provides a plug-in for the ``httpie`` utility. You can install ``httpie`` 
using ``pip install httpie``. Once you send a request that results in an
exception, you will enter the debugger automatically::

    > http localhost

    HTTP/1.0 500 Internal Server Error
    Date: Fri, 24 Jul 2015 23:41:20 GMT
    Server: WSGIServer/0.2 CPython/3.4.2
    Content-Type: text/plain; charset=utf-8
    OhOh-Debug-Token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1N [Truncated (5061 chars) ...]
    Location: http://localhost/ohoh-debug/
    Content-Length: 454

    Traceback (most recent call last):
      File "c:\dev\ohoh\build\lib\ohoh\middleware.py", line 57, in __call__
        return self._app(environ, start_response)
      File "tests\mock_app.py", line 6, in simple_err_app
        path.join("foo bar", 475564)
      File "C:\Python34\lib\ntpath.py", line 110, in join
        p_drive, p_path = splitdrive(p)
      File "C:\Python34\lib\ntpath.py", line 159, in splitdrive
        if len(p) > 1:
    TypeError: object of type 'int' has no len()
    OhOh Interactive Debugger v0.1.dev28+n8ec9121
    (odb)


Commands
--------

Check back later for a list of supported commands.



.. |build-status| image:: https://travis-ci.org/te-je/ohoh.svg?branch=develop
    :target: https://travis-ci.org/te-je/ohoh
    :alt: build status
    :scale: 100%
    
.. |license| image:: https://img.shields.io/badge/license-MIT-blue.svg
    :target: https://raw.githubusercontent.com/te-je/ohoh/develop/LICENSE.txt
    :alt: License
    :scale: 100%
