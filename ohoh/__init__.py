from __future__ import absolute_import
from argparse import ArgumentParser
from codecs import open
from collections import namedtuple
from importlib import import_module
from os import path
import logging
import re
import sys


here = path.dirname(__file__)
with open(path.join(here, "VERSION.txt"), encoding="ascii") as f:
    __version__ = f.read().strip()


# Verbosity levels; from 0 to 3
VERBOSITY = [logging.INFO + 5, logging.INFO, logging.DEBUG + 5, logging.DEBUG]
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 5000
DEFAULT_ADDR = "{0}:{1}".format(DEFAULT_HOST, DEFAULT_PORT)
# filename:obj | filename | pkg.mod:obj | pkg.mod
APP_REGEX = re.compile(r"""^
    (?:
      (?P<module>             # Capture group for module
        (?:[A-Z]\w*)            # Should be a valid indentifier
        (?:\.[A-Z]\w*)*         # Followed by optional submodules
      )
      |
      (?P<filename>           # Capture group for a filename
        (?:[A-Z]+:[\\/])?       # An optional drive component
        [^:]*
      )
    )
    (?:                     # Optional object component
      :                       # Denoted by a :
      (?P<obj>                # Capture group for the object name
        [A-Z]\w*                # Should be a valid identifier
      )
      (?P<funcall>            # Followed by optional function call
        \(
        (?P<funcargs>.*)        # Capture group for function arguments
        \)
      )?
    )?
    $""", re.VERBOSE | re.IGNORECASE)


Address = namedtuple("Address", "host port")


def address(addrstr):
    if ":" in addrstr:
        host, port = addrstr.split(":", 2)
        port = int(port)
    else:
        host = addrstr
        port = 5000
    return Address(host, port or DEFAULT_PORT)


def app_spec(locstr):
    m = APP_REGEX.match(locstr)
    if not m:
        raise ValueError(locstr)

    if m.group("filename") or m.group('module').endswith('.py'):
        fn = m.group("filename") or m.group("module")

        if not path.isfile(fn):
            if m.group('module') and m.group('module').endswith('.py'):
                modname = fn
            else:
                raise IOError("no such file: {0}".format(fn))

        dirname = path.dirname(fn)
        modname = path.splitext(path.basename(fn))[0]
        sys.path.insert(0, dirname)

    else:
        modname = m.group('module')

    mod = import_module(modname)
    if not m.group("obj"):
        app = mod.app
    else:
        obj = getattr(mod, m.group('obj'))
        if m.group("funcargs"):
            # FIXME: Is this dangerous?
            app = eval("obj({0})".format(m.group("funcargs")))
        elif m.group("funcall"):
            app = obj()
        else:
            app = obj

    if not callable(app):
        raise TypeError(app)

    return app


def pypath(dirname):
    if not path.isdir(dirname):
        raise ValueError(dirname)
    else:
        sys.path.append(dirname)
    return dirname


def build_parser():
    parser = ArgumentParser(
        description="Serve a WSGI app in debug mode."
    )
    # Usage: ohoh localhost:5000 "package.module:app"
    parser.add_argument("-v", "--verbose", dest="verbosity", action="count",
                        default=0, help="Increase the verbosity level.")
    parser.add_argument("--serve", "-s", action="store", metavar="address",
                        type=address, default=DEFAULT_ADDR, dest="address",
                        help="The address to bind the server to. "
                        "Accepted in the form `host:port`, but either part "
                        "may be omitted. `host` binds to port {DEFAULT_PORT} "
                        "using the given interface. `:port` binds to the "
                        "given port on all interfaces.".format(**globals()))
    parser.add_argument("app", action="store", type=app_spec,
                        help="A path to the WSGI application. Example: "
                        '"package.module:app", "package.module:AppCls()"'
                        ', "filename.py:app" or "filename.py:AppCls()". If a '
                        "filename is used, its directory is prepended to "
                        "sys.path.")
    parser.add_argument("-p", "--append-path", metavar="package-dir",
                        action="append", type=pypath,
                        help="Append a directory to sys.path. These arguments "
                        "MUST come before the app argument, otherwise they "
                        "will not be added to sys.path before the app is "
                        "imported.")
    return parser


def main():

    parser = build_parser()
    args = parser.parse_args()

    # Set up the log handler according to what the user request
    handler = logging.StreamHandler()
    handler.setLevel(VERBOSITY[min(args.verbosity, 3)])
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    LOG.addHandler(handler)

    run_simple(args.address.host, args.address.port, args.app)


from .wsgi import run_simple


if __name__ == '__main__':
    main()
