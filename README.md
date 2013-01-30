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

## Example Usage. TODO update public API
```python
from pywinrm import WinRMClient

winrm = WinRMClient(
    endpoint='http://windows-host:5985/wsman',
    transport='plaintext',
    username='john.smith',
    password='secret')
shell_id = winrm.open_shell()
command_id = winrm.run_command(shell_id, 'ipconfig', ['/all'])
stdout, stderr, return_code = winrm.get_command_output(shell_id, command_id)
winrm.cleanup_command(shell_id, command_id)
winrm.close_shell(shell_id)
```

## Powershell example
```python
from pywinrm import WinRMClient
import base64

script = """$strComputer = $Host
Clear

$RAM = WmiObject Win32_ComputerSystem
$MB = 1048576

"Installed Memory: " + [int]($RAM.TotalPhysicalMemory /$MB) + " MB" """

# powershell scripts with multi lines, braces, etc. 
# must be utf-16 unicoded and base64 encoded
script = base64.b64encode(script.encode("utf-16"))

cmd = "powershell -encodedcommand %s" % (script)

winrm = WinRMClient(
    endpoint='http://windows-host:5985/wsman',
    transport='plaintext',
    username='john.smith',
    password='secret')
shell_id = winrm.open_shell()
command_id = winrm.run_command(shell_id, cmd)
stdout, stderr, return_code = winrm.get_command_output(shell_id, command_id)
winrm.cleanup_command(shell_id, command_id)
winrm.close_shell(shell_id)
print stdout
```

## Contribute

Want to help - send a pull request. I will accept good pull requests for sure.
