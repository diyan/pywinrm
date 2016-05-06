# pywinrm [![Build Status](https://travis-ci.org/diyan/pywinrm.png)](https://travis-ci.org/diyan/pywinrm) [![Coverage Status](https://coveralls.io/repos/diyan/pywinrm/badge.png)](https://coveralls.io/r/diyan/pywinrm)

pywinrm is a Python client for the Windows Remote Management (WinRM) service.
It allows you to invoke commands on target Windows machines from any machine
that can run Python.

WinRM allows you to perform various management tasks remotely. These include, 
but are not limited to: running batch scripts, powershell scripts, and fetching 
WMI variables.

For more information on WinRM, please visit
[Microsoft's WinRM site](http://msdn.microsoft.com/en-us/library/aa384426.aspx).

## Requirements
* Linux, Mac OS X or Windows
* CPython 2.6-2.7, 3.2-3.5 or PyPy 1.9
* [requests-kerberos](http://pypi.python.org/pypi/requests-kerberos) is optional

## Installation
### To install pywinrm with support for basic, certificate, and NTLM auth, simply
```bash
$ pip install pywinrm
```

### To use Kerberos authentication you need these optional dependencies

```bash
# for Debian/Ubuntu/etc:
$ sudo apt-get install python-dev libkrb5-dev
$ pip install pywinrm[kerberos]

# for RHEL/CentOS/etc:
$ sudo yum install gcc krb5-devel krb5-workstation
$ pip install pywinrm[kerberos]
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

NOTE: pywinrm will try and guess the correct endpoint url from the following formats:

 - windows-host -> http://windows-host:5985/wsman
 - windows-host:1111 -> http://windows-host:1111/wsman
 - http://windows-host -> http://windows-host:5985/wsman
 - http://windows-host:1111 -> http://windows-host:1111/wsman
 - http://windows-host:1111/wsman -> http://windows-host:1111/wsman


### Run Powershell script on remote host

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

Powershell scripts will be base64 UTF16 little-endian encoded prior to sending to the Windows host. Error messages are converted from the Powershell CLIXML format to a human readable format as a convenience.

### Run process with low-level API with domain user, disabling HTTPS cert validation

```python
from winrm.protocol import Protocol

p = Protocol(
    endpoint='https://windows-host:5986/wsman',
    transport='ntlm',
    username=r'somedomain\someuser',
    password='secret',
    server_cert_validation='ignore')
shell_id = p.open_shell()
command_id = p.run_command(shell_id, 'ipconfig', ['/all'])
std_out, std_err, status_code = p.get_command_output(shell_id, command_id)
p.cleanup_command(shell_id, command_id)
p.close_shell(shell_id)
```

### Enabling WinRM on remote host
Enable WinRM over HTTP and HTTPS with self-signed certificate (includes firewall rules):

```
# from powershell:
Invoke-Expression ((New-Object System.Net.Webclient).DownloadString('https://raw.githubusercontent.com/ansible/ansible/devel/examples/scripts/ConfigureRemotingForAnsible.ps1'))
```

Enable WinRM over HTTP for test usage (includes firewall rules):
```
winrm quickconfig
```

Enable WinRM basic authentication. For domain users, it is necessary to use NTLM or Kerberos authentication (both are enabled by default).
```
# from cmd:
winrm set winrm/config/service/auth @{Basic="true"}
```

Allow unencrypted message passing over WinRM (recommended only for troubleshooting and internal use)
```
# from cmd:
winrm set winrm/config/service @{AllowUnencrypted="true"}
```

### Contributors (alphabetically)

- Reina Abolofia
- Lukas Bednar
- Chris Church
- Matt Clark
- Nir Cohen
- David Cournapeau
- Matt Davis
- Patrick Dunnigan
- Gema Gomez
- Juan J. Martinez
- Alessandro Pilotti
- Manuel Sabban
- Jijo Varghese

Want to help - send a pull request. I will accept good pull requests for sure.
