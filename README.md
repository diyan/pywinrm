# pywinrm [![Build Status](https://travis-ci.org/diyan/pywinrm.png)](https://travis-ci.org/diyan/pywinrm)

pywinrm is a Python client for Windows Remote Management (WinRM).
This allows you to invoke commands on target Windows machines from any machine
that can run Python.

WinRM allows you to call native objects in Windows.  This includes, but is not
limited to, running batch scripts, powershell scripts and fetching WMI variables.
For more information on WinRM, please visit
[Microsoft's WinRM site](http://msdn.microsoft.com/en-us/library/aa384426.aspx).

## Requirements
* Linux, Mac OS X or Windows
* CPython 2.6, 2.7, 3.2, 3.3 or PyPy 1.9
* [python-kerberos](http://pypi.python.org/pypi/kerberos) is optional

## Installation
To install pywinrm, simply (TODO fix setup.py):
```bash
$ pip install http://github.com/diyan/pywinrm/archive/master.zip
```

In order to use Kerberos authentication you need to install optional dependency:
```bash
$ sudo apt-get install python-dev libkrb5-dev
$ pip install kerberos
```

## Example Usage
### Standard API example (in progress)
```python
import winrm

s = winrm.Session('windows-host', auth=('john.smith', 'secret'))
r = s.run_cmd('ipconfig', ['/all'])
>>> r.status_code
0
>>> r.std_out
Windows IP Configuration

   Host Name . . . . . . . . . . . . : WINDOWS-HOST
   Primary Dns Suffix  . . . . . . . :
   Node Type . . . . . . . . . . . . : Hybrid
   IP Routing Enabled. . . . . . . . : No
   WINS Proxy Enabled. . . . . . . . : No
...
>>> r.std_err

```

### Low-level API example
```python
from winrm.protocol import Protocol

p = Protocol(
    endpoint='http://windows-host:5985/wsman',
    transport='plaintext',
    username='john.smith',
    password='secret')
shell_id = p.open_shell()
command_id = p.run_command(shell_id, 'ipconfig', ['/all'])
std_out, std_err, status_code = p.get_command_output(shell_id, command_id)
p.cleanup_command(shell_id, command_id)
p.close_shell(shell_id)
```

## Contribute

Want to help - send a pull request. I will accept good pull requests for sure.