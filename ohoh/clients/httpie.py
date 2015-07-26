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
from ohoh.clients import DebuggerCliClient


class Formatter(DebuggerCliClient, FormatterPlugin):
    name = DebuggerCliClient.intro

    def __init__(self, env, **kwargs):
        self.enabled = True
        self.stdout = env.stdout
        self.stderr = env.stderr
        DebuggerCliClient.__init__(self)

    def format_headers(self, headers):
        header_list = [
            (part[0], part[-1])
            for part in map(
                lambda hstr: hstr.partition(":"),
                headers.splitlines(False)
            )
        ]
        idx = self.find_debug_header(header_list)

        if idx < 0:
            return headers
        else:
            # Truncate the displayed header
            header, val = header_list[idx]
            max_value_length = 80 - len(header) - 1

            if len(val) > max_value_length:
                truncate = u" [Truncated ({0} bytes) ...]".format(
                    len(val.strip()))
                val = val[:max_value_length - len(truncate)] + truncate

                header_list[idx] = header, val

            return u"\n".join([
                ":".join((header, val)) for header, val in header_list
            ])

    def format_body(self, content, mime):
        if self.debug_token is not None:
            self.traceback_text = content
            self.cmdloop()
            return u""
        else:
            return content

    def preloop(self):
        self.stderr.write(self.traceback_text)
