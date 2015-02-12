# -*- coding: utf-8 -*-

"""
winrm - Remote command execution on Windows
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

winrm (client) is a command-line interface to execute remote commands
on Windows through the WinRM protocol.

Usage examples:

Get the hostname of the windows computer:
```
$ winrm -p password Administrator@10.0.0.10 hostname
```
winrm also takes commands from stdin
```
$ winrm Administrator@10.0.0.10 <<< ipconfig
```

it is easy to run powershell commands
```
$ winrm -i ps -p password Administrator@192.168.123.231 1+1
```

it is also easy to run powershell scripts
```
$ winrm -p password Administrator@10.0.0.10 < whereis.ps1
```

even with arguments
```
$ winrm -p password -a notepad -a wordpad Administrator@10.0.0.10 < whereis.ps1
```

TODO: Multiline commands doesn't work
```
$ winrm -p password Administrator@10.0.0.10 <<\EOF
echo 1
echo 2
EOF
```

Works for powershell though
```
$ winrm -i ps -p password Administrator@10.0.0.10 <<\EOF
echo 1
echo 2
EOF
1
2
```
"""

from __future__ import print_function

import argparse
import codecs
import getpass
import locale
import logging
import os
import sys
import traceback

from . import run
from .exceptions import (
    WinRMTransportError,
    UnauthorizedError
)

log = logging.getLogger('winrm')

def setup_verbose_logging():
    log.setLevel(logging.DEBUG)
    log.addHandler(logging.StreamHandler())

def handle_expection(e):
    error = e.__class__
    if error == WinRMTransportError:
        print('Server is not responding: {}'.format(e), file=sys.stderr)
    elif error == UnauthorizedError:
        print('Permission denied: {}'.format(e), file=sys.stderr)
    else:
        print(str(e), file=sys.stderr)

    log.info(traceback.format_exc())
    sys.exit(1)

def get_parser():
    parser = argparse.ArgumentParser(description="Execute remote commands through the WinRM protocol.")

    parser.add_argument('-a', '--args', default=[], action='append', help='inject script argument in head of script')
    parser.add_argument('-i', '--interpreter', choices=('cmd', 'ps'))
    parser.add_argument('-l', '--login-name')
    parser.add_argument('-p', '--password')
    parser.add_argument('-t', '--transport', default='plaintext', choices=('plaintext', 'kerberos', 'ssl'))
    parser.add_argument('-v', '--verbose', action="store_true")

    parser.add_argument('hostname', help='[user@]hostname')
    parser.add_argument('command', nargs='?', type=lambda s: unicode(s, locale.getpreferredencoding()))

    return parser

def process_args(args, parser):
    if '@' in args.hostname:
        args.login_name,args.hostname = args.hostname.split('@')

    if not args.login_name:
        args.login_name = os.environ['USER']

    if not args.password:
        args.password = getpass.getpass()

    if args.verbose:
        setup_verbose_logging()

    if not sys.stdin.isatty():
        try:
            sys.stdin = codecs.getreader(locale.getpreferredencoding())(sys.stdin);
            args.command = sys.stdin.read()
        except IOError:
            pass

    # avoid the interpreter argument when using a script file
    if args.interpreter == None:
        args.interpreter = 'cmd'
        try:
            stdin_filename = os.readlink('/proc/self/fd/0')
            root, ext = os.path.splitext(stdin_filename)
            if 'ps' in ext:
                args.interpreter = 'ps'
        except OSError:
            pass

    if not args.command:
        parser.error('command argument required')

def get_args():
    parser = get_parser()
    args = parser.parse_args()
    process_args(args, parser)
    return args

def main():
    args = get_args()

    kwargs = {
        'auth': (args.login_name, args.password),
        'args': args.args,
        'interpreter': args.interpreter,
        'transport': args.transport
    }

    try:
        response = run(args.command, args.hostname, **kwargs)
        if response.status_code == 0:
            sys.stdout.write(response.std_out)
            # Running errounous powershell on the windows server
            # doesn't go into std_err?!?
            # Try any erronous command, e.g., ()
            # Therefore, we also write std_err on success
            sys.stderr.write(response.std_err)
        else:
            sys.stderr.write(response.std_err)
            sys.exit(response.status_code)

    except Exception, e:
        handle_expection(e)

if __name__ == '__main__':
    main()
