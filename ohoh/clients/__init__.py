from cmd import Cmd
import requests
import sys

from ohoh import __version__


class DebuggerCliClient(Cmd):
    #: The HTTP header that the debug server uses
    debug_header = "OhOh-Debug-Token"

    #: The location on the debug server that debug commands are sent to
    debug_uri = "localhost:5000/ohoh-debug/"

    #: Last received value from the debug header
    debug_token = None

    intro = "OhOh Interactive Debugger v" + __version__
    prompt = "(odb) "

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
        client_commands = ("exit", "version", "token")
        if line.strip() not in client_commands and self.debug_token is None:
            self.stderr.write("*** Debug token has not been set.\n")
            line = ""
        return line

    def emptyline(self):
        return

    def do_exit(self, args):
        return True

    def do_version(self, args):
        self.stdout.write(self.intro)
        self.stdout.write("\n")

    def do_token(self, args):
        self.stdout.write(self.debug_token)
        self.stdout.write("\n")

    def default(self, line):
        # Query the debug server.
        headers = {self.debug_header: self.debug_token}
        response = requests.post("http://" + self.debug_uri,
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
