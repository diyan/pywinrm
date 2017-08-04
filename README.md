# pywinrm 
pywinrm is a Python client for the Windows Remote Management (WinRM) service.
It allows you to invoke commands on target Windows machines from any machine
that can run Python.

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/diyan/pywinrm/blob/master/LICENSE)
[![Travis Build](https://travis-ci.org/diyan/pywinrm.svg)](https://travis-ci.org/diyan/pywinrm)
[![AppVeyor Build](https://ci.appveyor.com/api/projects/status/github/diyan/pywinrm?svg=true)](https://ci.appveyor.com/project/diyan/pywinrm) [![Coverage](https://coveralls.io/repos/diyan/pywinrm/badge.svg)](https://coveralls.io/r/diyan/pywinrm)
[![PyPI](https://img.shields.io/pypi/dm/pywinrm.svg)](https://pypi.python.org/pypi/pywinrm)

WinRM allows you to perform various management tasks remotely. These include, 
but are not limited to: running batch scripts, powershell scripts, and fetching 
WMI variables.

Used by [Ansible](https://www.ansible.com/) for Windows support.

For more information on WinRM, please visit
[Microsoft's WinRM site](http://msdn.microsoft.com/en-us/library/aa384426.aspx).

## Requirements
* Linux, Mac OS X or Windows
* CPython 2.6-2.7, 3.3-3.5 or PyPy2
* [requests-kerberos](http://pypi.python.org/pypi/requests-kerberos) and [requests-credssp](https://github.com/jborean93/requests-credssp) is optional

## Installation
### To install pywinrm with support for basic, certificate, and NTLM auth, simply
```bash
$ pip install pywinrm
```

### To use Kerberos authentication you need these optional dependencies

```bash
# for Debian/Ubuntu/etc:
$ sudo apt-get install gcc python-dev libkrb5-dev
$ pip install pywinrm[kerberos]

# for RHEL/CentOS/etc:
$ sudo yum install gcc python-devel krb5-devel krb5-workstation
$ pip install pywinrm[kerberos]
```

### To use CredSSP authentication you need these optional dependencies

```bash
# for Debian/Ubuntu/etc:
$ sudo apt-get install gcc python-dev libssl-dev
$ pip install pywinrm[credssp]

# for RHEL/CentOS/etc:
$ sudo yum install gcc python-devel openssl-devel
$ pip install pywinrm[credssp]
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

### Valid transport options

pywinrm supports various transport methods in order to authenticate with the WinRM server. The options that are supported in the `transport` parameter are;
* `basic`: Basic auth only works for local Windows accounts not domain accounts. Credentials are base64 encoded when sending to the server.
* `plaintext`: Same as basic auth.
* `certificate`: Authentication is done through a certificate that is mapped to a local Windows account on the server.
* `ssl`: When used in conjunction with `cert_pem` and `cert_key_pem` it will use a certificate as above. If not will revert to basic auth over HTTPS.
* `kerberos`: Will use Kerberos authentication for domain accounts which only works when the client is in the same domain as the server and the required dependencies are installed. Currently a Kerberos ticket needs to be initiliased outside of pywinrm using the kinit command.
* `ntlm`: Will use NTLM authentication for both domain and local accounts. Currently no support for NTLMv2 auth and other features included in that version (WIP).
* `credssp`: Will use CredSSP authentication for both domain and local accounts. Allows double hop authentication. This only works over a HTTPS endpoint and not HTTP.

### HTTP or HTTPS endpoint

While either a HTTP or HTTPS endpoint can be used as the transport method, using HTTPS is prefered as the messages are encrypted using SSL. To use HTTPS either a self signed certificate or one from a CA can be used. You can use this [guide](http://www.joseph-streeter.com/?p=1086) to set up a HTTPS endpoint with a self signed certificate.

If you still wish to use a HTTP endpoint and loose confidentiality in your messages you will need to enable unencrypted messages in the server by running the following command
```
# from powershell:
winrm set winrm/config/service '@{AllowUnencrypted="true"}'

# from cmd:
winrm set winrm/config/service @{AllowUnencrypted="true"}

```
As a repeat this should definitely not be used as your credentials and messages will allow anybody to see what is sent over the wire.

There are plans in place to allow message encryption for messages sent with Kerberos or NTLM messages in the future.

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

Enable WinRM basic authentication. For domain users, it is necessary to use NTLM, Kerberos or CredSSP authentication (Kerberos and NTLM authentication are enabled by default CredSSP isn't).
```
# from cmd:
winrm set winrm/config/service/auth @{Basic="true"}
```

Enable WinRM CredSSP authentication. This allows double hop support so you can authenticate with a network service when running command son the remote host. This command is run in Powershell.
```powershell
Enable-WSManCredSSP -Role Server -Force
Set-Item -Path "WSMan:\localhost\Service\Auth\CredSSP" -Value $true
```

### Contributors (alphabetically)

- Alessandro Pilotti
- Alexey Diyan
- Chris Church
- David Cournapeau
- Gema Gomez
- Jijo Varghese
- Jordan Borean
- Juan J. Martinez
- Lukas Bednar
- Manuel Sabban
- Matt Clark
- Matt Davis
- Maxim Kovgan
- Nir Cohen
- Patrick Dunnigan
- Reina Abolofia

Want to help - send a pull request. I will accept good pull requests for sure.
