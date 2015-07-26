from cmd import Cmd
import re
import requests
import sys

from ohoh import __version__


class DebuggerCliClient(Cmd):
    #: The HTTP header that the debug server uses
    debug_header = "OhOh-Debug-Token"

    #: The location on the debug server that debug commands are sent to
    debug_uri = "http://localhost:5000/ohoh-debug/"

    #: Last received value from the debug header
    debug_token = None

    intro = "OhOh Interactive Debugger v" + __version__
    prompt = "(odb) "
    doc_header = "Client commands (type help <topic>):"
    misc_header = "Debug commands (type help <topic>):"

    stdout = sys.stdout
    stderr = sys.stderr

    def find_debug_header(self, header_list):
        """
        Search a list of (header, value) tuples for a debug header. If
        found, return the index. Otherwise, return -1.
        """
        matchers = {
            "debug_uri": ("location", False),
            "debug_token": (self.debug_header.lower(), True)
        }

        for i, htup in enumerate(header_list):
            header, val = htup
            for attr in matchers:
                h, ret = matchers[attr]
                if header.lower() == h:
                    setattr(self, attr, val)

                    if ret:
                        return i
        else:
            return -1

    def precmd(self, line):
        client_commands = (u"exit", u"version", u"token" u"url")
        cl_cmd_reg = re.compile(
            ur"(?:{0})\s".format(
                u"|".join([
                    re.escape(cl_cmd) for cl_cmd in client_commands
                ])
            )
        )

        if self.debug_token is None and cl_cmd_reg.match(line):
            self.stderr.write(u"*** Debug token has not been set.\n")
            line = u""
        return line

    def emptyline(self):
        return

    def do_quit(self, args):
        return True

    def do_version(self, args):
        self.stdout.write(self.intro)
        self.stdout.write("\n")

    def do_token(self, new_token):
        if new_token:
            self.debug_token = new_token
            self.stdout.write("*** New debug token has been set.")
        else:
            self.stdout.write(self.debug_token)

        self.stdout.write("\n")

    def do_url(self, new_url):
        if new_url:
            if not re.match("http[s]://", new_url, re.I):
                new_url = "http://" + new_url

            self.debug_uri = new_url
            self.stdout.write("*** New debug url has been set.")
        else:
            self.stdout.write(self.debug_uri)

        self.stdout.write("\n")

    def default(self, line):
        # Query the debug server.
        headers = {self.debug_header: self.debug_token}
        response = requests.post(self.debug_uri,
                                 data=line.encode("utf8"), timeout=30,
                                 headers=headers)

        if response.status_code == 200:
            self.debug_token = response.headers.get(self.debug_header, None)
            self.stdout.write(response.text)

            if not self.debug_token:
                return True

        else:
            self.stderr.write("*** Failed to issue remote debugger command.\n")

        return

    def completedefault(self, text, line, begidx, endidx):
        return [
            cmd_name for cmd_name in COMMANDS
            if cmd_name.startswith(text) and begidx == 0
        ]


COMMANDS = {
    # Client commands
    'quit': "Exit the debugger.",
    'token': "token [new-token]\n\t"
             "Show or set the current debug token. You typically won't \n\t"
             "need to use this since most clients will set it for you.",
    'url': "url [debug-url]\n\t"
           "Show or set the url to be used for debug requests.",
    'version': "Show the client's version number.",

    # Server commands
    'where': "Print a stack trace, with the most recent frame at the \n\t"
             "bottom. An arrow indicates the current frame, which \n\t"
             "determines the context of most commands.",
    'down': "Move the current frame one level down in the stack trace (to \n\t"
            "a newer frame).",
    'up': "Move the current frame one level up in the stack trace (to an \n\t"
          "older frame).",
    'p': "p expression\n\t"
         "Evaluate the expression in the current context and print its value.",
    'args': "Print the argument list to the current function.",
    'pp': "pp expression\n\t"
          "Like the ``p`` command, except the value of the expression is \n\t"
          "pretty-printed using the pprint module",
    '!': "(!)statement\n\t"
            "Execute the (one-line) statement in the context of the \n\t"
            "current stack frame. The exclamation point can be omitted \n\t"
            "unless the first word of the statement resembles a debugger\n\t"
            "command. To set a global variable, you can prefix the\n\t"
            "assignment command with a global command on the same line.",
}


def make_helper(name):
    def help(self):
        if not COMMANDS[name].startswith(name) and name != "!":
            self.stdout.write(name)
            self.stdout.write("\n\t")
        self.stdout.write(COMMANDS[name])
        self.stdout.write("\n")
    return help


for name in COMMANDS:
    setattr(DebuggerCliClient, "help_" + name, make_helper(name))
