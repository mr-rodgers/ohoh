# -*- coding: utf-8 -*-
from __future__ import absolute_import
from cmd import Cmd
import re
import sys

from httpie.plugins import FormatterPlugin
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import TerminalFormatter
import requests

from ohoh import __version__


class Formatter(FormatterPlugin, Cmd):
    debug_header = "OhOh-Debug-Token"
    debug_uri = "localhost:5000/ohoh-debug/"
    name = intro = "OhOh Interactive Debugger v" + __version__
    prompt = "(odb) "

    def __init__(self, **kwargs):
        self.enabled = True
        self.kwargs = kwargs
        self.regexp = re.compile("\s*{0}:\s*(?P<token>.+)\s*".format(
            re.escape(self.debug_header)), re.IGNORECASE
        )
        Cmd.__init__(self)

    def format_headers(self, headers):
        header_list = headers.splitlines(True)

        self.debug_token = None

        for i, header in enumerate(header_list):
            if header.lower().startswith("location:"):
                self.debug_uri = header.split(":")[1].strip()
                continue

            m = self.regexp.match(header)
            if m is not None:
                self.debug_token = m.group('token')
                el = u" [Truncated ({0} chars) ...]".format(
                    len(self.debug_token))
                new_header = header[:80 - len(el)] + el + u"\n"\
                    if len(header) > 80 else header
                header_list[i] = new_header
                break

        return u"".join(header_list)

    def format_body(self, content, mime):
        if getattr(self, 'debug_token', None) is not None:
            self.traceback_text = content
            self.cmdloop()
            return u""
        else:
            return content

    def preloop(self):
        # Output the text with pygments
        lexer = get_lexer_by_name("pytb", stripall=True)
        formatter = TerminalFormatter()
        stderr = self.kwargs['env'].stderr
        stderr.write(highlight(self.traceback_text, lexer, formatter))

    def emptyline(self):
        return

    def default(self, line):
        if line == "debug-token":
            print self.debug_token
            return

        if line == "version":
            print self.intro
            return

        # Query the debug server.
        headers = {self.debug_header: self.debug_token}
        response = requests.post("http://" + self.debug_uri,
                                 data=line.encode("utf8"), timeout=10,
                                 headers=headers)

        if response.status_code == 200:
            self.debug_token = response.headers.get(self.debug_header, None)
            sys.stdout.write(response.text)

            if not self.debug_token:
                return True

        else:
            sys.stderr.write("*** Failed to issue remote debugger command.\n")

        return

    def do_exit(self, *args):
        return True
