# pywinrm [![Build Status](https://travis-ci.org/diyan/pywinrm.png)](https://travis-ci.org/diyan/pywinrm) [![Coverage Status](https://coveralls.io/repos/diyan/pywinrm/badge.png)](https://coveralls.io/r/diyan/pywinrm)

pywinrm is a Python client for Windows Remote Management (WinRM).
This allows you to invoke commands on target Windows machines from any machine
that can run Python.

WinRM allows you to call native objects in Windows. These include, but are not
limited to, running batch scripts, powershell scripts and fetching WMI variables.
For more information on WinRM, please visit
[Microsoft's WinRM site](http://msdn.microsoft.com/en-us/library/aa384426.aspx).

## Requirements
* Linux, Mac OS X or Windows
* CPython 2.6, 2.7, 3.2, 3.3 or PyPy 1.9
* [python-kerberos](http://pypi.python.org/pypi/kerberos) is optional

## Installation
### To install pywinrm, simply
```bash
$ pip install http://github.com/diyan/pywinrm/archive/master.zip
```

### To use Kerberos authentication you need these optional dependencies

```bash
$ sudo apt-get install python-dev libkrb5-dev
$ pip install kerberos
```

## Example Usage
### Run a process on a remote host
```python
import winrm

s = winrm.Session('windows-host.example.com', auth=('john.smith', 'secret'))
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

NOTE: pywirnm will try and guess the correct endpoint url from the following formats:

 - windows-host -> http://windows-host:5985/wsman
 - windows-host:1111 -> http://windows-host:1111/wsman
 - http://windows-host -> http://windows-host:5985/wsman
 - http://windows-host:1111 -> http://windows-host:1111/wsman
 - http://windows-host:1111/wsman -> http://windows-host:1111/wsman


### Run Powershell on remote host

```python
import winrm

ps_script = """$strComputer = $Host
Clear
$RAM = WmiObject Win32_ComputerSystem
$MB = 1048576

"Installed Memory: " + [int]($RAM.TotalPhysicalMemory /$MB) + " MB" """

s = winrm.Session('windows-host.example.com', auth=('john.smith', 'secret'))
r = s.run_ps(ps_script)
>>> r.status_code
0
>>> r.std_out
Installed Memory: 3840 MB

>>> r.std_err

```

Powershell script will be base64 UTF16 little endian encoded prior to sending to Windows host. Error messages are converted from the Powershell CLIXML format to a human readable format as a convenience.

### Run process with low-level API

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

## Client-side and server-side configuration

### Server-side. Configure WinRM service on Windows host

NOTE You may want to use [ievms](https://xdissent.github.com/ievms) to get free Windows VM up and running:

```bash
$ curl -s https://raw.githubusercontent.com/xdissent/ievms/master/ievms.sh | env IEVMS_VERSIONS="9" bash
```
Enable WinRM service on remote host/VM:

```
C:\> winrm quickconfig
```

Allow basic WinRM authentication for service:

```
C:\> winrm set winrm/config/service/auth @{Basic="true"}
C:\> winrm set winrm/config/service @{AllowUnencrypted="true"}
```

NOTES:

- Basic auth will work only if unencrypted data transfer will be allowed on the server side
- For hosts in domain it's safer to use Kerberos authentication, not Basic
- Unencrypted data transfer vulnerable to man-in-the-middle attack and could be used only in secure environments like VPN tunnel
- Message encryption is not yet implemented in pywinrm

### Client-side. Configure WinRM client on Windows host

It make sense to configure native WinRM client on same Windows host/VM and make sure it works.

Allow basic WinRM authentication for client:

```
C:\> winrm set winrm/config/client/auth @{Basic="true"}
C:\> winrm set winrm/config/client @{AllowUnencrypted="true"}
```
Make sure that WinRM works on localhost with basic authentication and unencrypted messages:

```
C:\> winrs -r:localhost -u:IEUser -p:Passw0rd! -unencrypted hostname
IE9Win7
```


### More details on how to configure WinRM

- https://support.microsoft.com/en-us/kb/555966

### Contributors (alphabetically)

- Alessandro Pilotti
- David Cournapeau
- Gema Gomez
- Matt Clark
- Patrick Dunnigan


Want to help - send a pull request. I will accept good pull requests for sure.
