ohoh
====

|build-status| |license|


OhOh is a debugger for your WSGI applications. Using OhOh, you can inspect
the stack frames of a wsgi app that's thrown an exception.

Usage
-----

Use this command to serve your wsgi app in debug mode::

    > ohoh "package.module:wsgi_app" -s localost:5000

For a full range of options, see ``ohoh -h``

OhOh provides a plug-in for the ``httpie`` utility. You can install ``httpie`` 
using ``pip install httpie``. Once you send a request that results in an
exception, you will enter the debugger automatically::

    > http localhost:5000
    HTTP/1.0 500 Internal Server Error
    Date: Fri, 24 Jul 2015 23:41:20 GMT
    Server: WSGIServer/0.2 CPython/3.4.2
    Content-Type: text/plain; charset=utf-8
    OhOh-Debug-Token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1N [Truncated (5061 chars) ...]
    Location: http://localhost:5000/ohoh-debug/
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
    (odb) up
    > c:\python34\lib\ntpath.py(110)join()
    -> p_drive, p_path = splitdrive(p)
    (odb)


Commands
--------

The following commands are supported by the command interpreter
(you can type ``help`` at the debugger prompt for online help with commands):

===============     ========================================================
Command             Description
---------------     --------------------------------------------------------
Client commands
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
quit                Exit the debugger.
---------------     --------------------------------------------------------
token               View the current debug server token.
---------------     --------------------------------------------------------
url                 View or set the url to which debug requests are sent.
---------------     --------------------------------------------------------
version             View the version number of the debugger.
---------------     --------------------------------------------------------
Debug commands
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
!                   Execute a one-line statement in the current context.
---------------     --------------------------------------------------------
args                Print the argument list to the current function.
---------------     --------------------------------------------------------
p                   Print the value of an expression.
---------------     --------------------------------------------------------
pp                  Pretty print the value of an expression.
---------------     --------------------------------------------------------
where               Print the stack trace, with the most recent call last.
---------------     --------------------------------------------------------
up                  Move up one frame in the stack.
---------------     --------------------------------------------------------
down                Move down one frame in the stack.
===============     ========================================================


Check back later for a list of supported commands.



.. |build-status| image:: https://travis-ci.org/te-je/ohoh.svg?branch=develop
    :target: https://travis-ci.org/te-je/ohoh
    :alt: build status
    :scale: 100%
    
.. |license| image:: https://img.shields.io/badge/license-MIT-blue.svg
    :target: https://raw.githubusercontent.com/te-je/ohoh/develop/LICENSE.txt
    :alt: License
    :scale: 100%
