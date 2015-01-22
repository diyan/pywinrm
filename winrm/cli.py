#!/usr/bin/env python
"""
winrm - Remote command execution on Windows
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

winrm (client) is a command-line interface to to execute remote commands
on Windows through the WinRM protocol.

Examples:

Get the hostname of the windows computer
```
$ ./winrm -p password Administrator@10.0.0.10 hostname
windows-hostname
```

winrm also takes commands from stdin
```
$ ./winrm -p password Administrator@10.0.0.10 <<\EOF
hostname
EOF
windows-hostname
```

it is easy to run powershell commands
```
$ ./winrm -t ps -p password Administrator@192.168.123.231 1+1
2
```

it is also easy to run powershell scripts
```
$ ./winrm -p password Administrator@10.0.0.10 < whereis.ps1
...
```

even with arguments
```
$ ./winrm -p password --args notepad Administrator@10.0.0.10 < whereis.ps1
Notepad|C:\Windows\system32\notepad.exe
```

TODO: Multiline commands doesn't work
```
$ ./winrm -p password Administrator@10.0.0.10 <<\EOF
echo 1
echo 2
EOF
1
```

Works for powershell though
```
$ ./winrm -t ps -p password Administrator@10.0.0.10 <<\EOF
echo 1
echo 2
EOF
1
2
```

"""

from __future__ import print_function

import argparse
import getpass
import logging
import os
import sys
import traceback

import winrm

from winrm.exceptions import (
    WinRMTransportError,
    UnauthorizedError
)

log = logging.getLogger('winrm')

def setup_verbose_logging():
    log.setLevel(logging.INFO)
    log.addHandler(logging.StreamHandler())

def run(command, hostname,
        auth=(),
        interpreter='cmd',
        args=()):
    session = winrm.Session(hostname, auth)
    if interpreter == 'ps':
        return session.run_ps(command, args)
    else:
        return session.run_cmd(command, args)

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

def main():
    parser = argparse.ArgumentParser(description='Run commands on remote Windows using WinRM')

    parser.add_argument('-v', '--verbose', action="store_true")
    parser.add_argument('-l', '--login-name')
    parser.add_argument('-p', '--password')

    parser.add_argument('-t', '--interpreter', choices=('cmd', 'ps'))
    parser.add_argument('-a', '--args', action='append', default=[])
    parser.add_argument('hostname', help='[user@]hostname')

    parser.add_argument('command', nargs='?')

    args = parser.parse_args()
    if '@' in args.hostname:
        args.login_name,args.hostname = args.hostname.split('@')

    if not args.login_name:
        args.login_name = os.environ['USER']

    if not args.password:
        args.password = getpass.getpass()

    if args.verbose:
        setup_verbose_logging()

    if not sys.stdin.isatty():
        args.command = sys.stdin.read()

    # avoid the interpreter argument when using a script file
    if args.interpreter == None:
        try:
            stdin_filename = os.readlink('/proc/self/fd/0')
            root, ext = os.path.splitext(stdin_filename)
            if 'ps' in ext:
                args.interpreter = 'ps'
        except OSError:
            pass

    if not args.command:
        parser.error('command argument required')

    kwargs = {
        'auth': (args.login_name, args.password),
        'args': args.args,
        'interpreter': args.interpreter
    }

    try:
        response = run(args.command, args.hostname, **kwargs)
        # result includes newline, use stdout.write to avoid
        # adding additional newlines
        sys.stdout.write(response.std_out)
        # always write std_out since erronous powershell
        # is put in std_out

        if response.status_code != 0:
            sys.stdout.write(response.std_err)
            sys.exit(response.status_code)


    except Exception, e:
        handle_expection(e)

if __name__ == '__main__':
    main()
