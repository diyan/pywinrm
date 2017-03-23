# pywinrm [![Build Status](https://travis-ci.org/diyan/pywinrm.png)](https://travis-ci.org/diyan/pywinrm) [![AppVeyor Build Status](https://ci.appveyor.com/api/projects/status/github/diyan/pywinrm)](https://ci.appveyor.com/project/diyan/pywinrm) [![Coverage Status](https://coveralls.io/repos/diyan/pywinrm/badge.png)](https://coveralls.io/r/diyan/pywinrm)

pywinrm is a Python client for the Windows Remote Management (WinRM) service.
It allows you to invoke commands on target Windows machines from any machine
that can run Python. As of version 1.0.0 pywinrm can use both the older WSMV
protocol and the newer Powershell Remoting Protocol.

WinRM allows you to perform various management tasks remotely. These include, 
but are not limited to: running batch scripts, powershell scripts, and fetching 
WMI variables.

Used by [Ansible](https://www.ansible.com/) for Windows support.

For more information on WinRM, please visit
[Microsoft's WinRM site](http://msdn.microsoft.com/en-us/library/aa384426.aspx).

Detailed guides on the protocols used can be found here;
[MS-WSMV](https://msdn.microsoft.com/en-us/library/cc251526.aspx)
[MS-PSRP](https://msdn.microsoft.com/en-us/library/dd357801.aspx)

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

### Run a cmd process on a remote host
```python
import winrm

s = winrm.Session(endpoint='windows-host.example.com', username='john.smith', password='secret')
r = s.run_cmd('ipconfig', ['/all'])

>>> r.return_code
0
>>> r.stdout
Windows IP Configuration

   Host Name . . . . . . . . . . . . : WINDOWS-HOST
   Primary Dns Suffix  . . . . . . . :
   Node Type . . . . . . . . . . . . : Hybrid
   IP Routing Enabled. . . . . . . . : No
   WINS Proxy Enabled. . . . . . . . : No
...
```

### Run Powershell commands on a remote host

```python
import winrm

s = winrm.Session(endpoint='windows-host.example.com', username='john.smith', password='secret')

# Run a single Powershell command with parameters
r = s.run_ps('New-Item', parameters=['-Path C:\temp', '-Type Directory'])

# Run a Powershell script
script = """$DebugPreference = 'Continue'
Write-Debug -Message "Cleaning C:\Temp"
if (Test-Path -Path C:\temp) {
    Remote-Item -Path C:\temp
}
New-Item -Path C:\temp -Type Directory"""
r = s.run_ps(script)

# Run a Powershell script with pre-set responses to input requests
script = """$name = Read-Host -Prompt "What is your name"
$age = Read-Host -Prompt "How old are you?"
Write-Host "Hello $name, are you $age years old"
"""
r = s.run_ps(script, responses=['Pywinrm', "100"])

# Run a Powershell script that takes in a pipeline input
script = """begin {
    $DebugPreference = 'Continue'
    Write-Debug -Message "Start Block"
}
process {
    Write-Debug -Message "Process Block $input"
}
end {
    Write-Debug -Message "End Block"
}
"""
r = s.run_ps(script, inputs=["1", "2", "3"])

```

### Run process with low-level API
If you don't want to use the Session class which abtracts a lot of the detail in the background you can interact with either
the WSMV or PSRP client itself and send custom calls if required. See `Transport Options` below as to what you can pass through when initialising the client.

#### WSMV Client
```python
from winrm.wsmv.wsmv import WsmvClient

c = WsmvClient(**transport_opts)
c.open_shell()
command_id = c.run_command('ipconfig', ['/all'])
output = c.get_command_output(command_id)
c.close_shell()
```

#### PSRP Client
```python
from winrm.psrp.psrp import PsrpClient

c = PsrpClient(**transport_opts)
c.open_shell()
command_id = c.run_command('Set-SmbShare', ['-Name Share', '-Path C:\temp'])
output = c.get_command_output(command_id)
c.close_shell()
```

### Low-Level Methods

When using the low-level API you have the following methods available to you for each shell

#### WSMV

* `open_shell(**shell_opts)`: Will create and connect to a new shell on the remote host, see `Shell Options` for a list of options
* `run_command(command, [arguments])`: Will start to execute a command on the shell created.
* `get_command_output(command_id)`: Once a command has been created, this will get the output of the command
* `close_shell()`: Will close the shell at the end of the process

#### PSRP

* `open_shell()`: Will create and connect to a new shell on the remote host
* `run_command(command, [parameters], responses, no_input)`: Will start to execute a command on the shell created, see below for parameter details
* `send_input(command_id, input)`: Will send pipeline input to a command before retrieving the command output.
* `get_command_output(command_id)`: Once a command has been created, this will get the output of the command
* `close_shell()`: Will close the shell at the end of the process

With run_command there are 4 parameters that can be set;
* `command`: The command or script to run
* `parameters`: If running a command, this is a list of parameters to run with the command, each parameter should have a key/value pair in the form `-Key Value`
* `responses`: A pre set list of responses to return to the server when asked, this is useful when running commands that prompt you for input
* `no_input`: A boolean value as to whether the script will allow a pipeline input using the `send_input` method (Default: `True`)


## Outputs

The output variable of `get_command_output` differs between the shell due to Powershell having more output streams. The below are the various attributes available on the return object for each shell.

### WSMV CMD

* `stdout`: The text sent to the Standard Output stream
* `stderr`: The text sent to the Standard Error stream
* `return_code`: The return/exit code of the command

### PSRP Powershell

You can get more details on the streams below by looking at [this](https://blogs.technet.microsoft.com/heyscriptingguy/2015/07/04/weekend-scripter-welcome-to-the-powershell-information-stream/) page. To get any output to the `debug`, `verbose`, and `information` stream in your scripts you need to make sure the following variables are set in your code.

```ps
$DebugPreference = 'Continue'
$VerbosePreference = 'Continue'
$InformationPreference = 'Continue'
```

* `output`: Any objects sent to the output stream
* `verbose`: Any objects sent to the verbose stream
* `debug`: Any objects sent to the debug stream
* `warning`: Any objects sent to the warning stream
* `error`: Any object sent to the error stream. The messages are formatted as you normally see them in Powershell
* `information`: The information stream was added in Windows 10 and Server 2016. This returns a list of objects sent to the information stream and their metadata like a timestamp. This is unlike the other streams where it is a List and not a String
* `stdout`: Any objects that displayed on the console, this can contain objects in the other streams as well as some that are not
* `stderr`: A copy of error and only used for compatibility with the WSMV return object
* `return_code`: The return/exit code if any was set by Powershell, will default to `0` if nothing was set

## Configuration

### Transport Options

When creating a session or a low level client you need to pass in some transport options. The options that are currently available to set are;

* `endpoint`: The URL of the endpoint/server to connect to, see `Endpoint Options` below for more details
* `auth_method`: The authentication method to connect with, see `Authentication Methods` below for more details (Default: `basic`)
* `username`: The username to authenticate with
* `password`: The password to authenticate with
* `cert_pem`: If using `certificate` authentication, this is the file path to the authentication certificate
* `read_timeout_sec`: Maximum seconds to wait before a HTTP connect/read times out (Default `30`). This value should be slightly higher than `operation_timeout_sec` set in the client options below
* `server_cert_validation`: Whether server certificate should be validated on Python versions that support it (Default: `validate`), Options: `validate`, `ignore`
* `kerberos_delegation`: If True, TGT is sent to the endpoint to allow multiple hops/credential delegation (Default: `False`)
* `kerberos_hostname_override`: The hostname to use for the Kerberos exchange (Default: hostname in the endpoint URL)
* `credssp_disable_tlsv1_2`: Whether to allow pre TLS 1.2 encrypted transport for CredSSP authentication for older servers (Default: `False`)

### Client Options

If using the low level API and are creating a client there are some options you can set this way;

* `operation_timeout_sec`: The maximum allowed time in seconds for any single WSMan HTTP operations (Default: `20`). Note this only applies to requests for information through WSMan, a command can still exceed this amount of time to run
* `locale`: The locale requests for text formatting on the response (Default: `en-US`)
* `encoding`: The string encoding format to encode messages in (Default: `utf-8`)
* `max_envelope_size`: The maximum envelope size in bytes (Default: `153600`). Pywinrm will try and get the actual value from the server when creating the Shell but if this fails for any reason like invalid rights will rely on this setting
* `min_runspaces`: The minimum amount of PSRP Runspaces to create on the Server (Default: `1`)
* `max_runspaces`: The maximum amount of PSRP RUnspaces to create on the Server (Defaut: `1`)

### Shell Options

If you are using WSMV to create a shell there are further options around customising this shell when calling the `open_shell` method;

* `noprofile`: If True then the profile loaded will be the default profile and not that users (Default: `False`)
* `codepage`: The set of characters of code pages in Windows  to set as the console output code page (Default: `437`). See [here](https://msdn.microsoft.com/en-us/library/windows/desktop/dd317756(v=vs.85).aspx) for a list of valid options
* `environment`: A dictionary of key/value pairs to set as environment variables when creating a new shell
* `working_directory`: The working directory to set when creating a new shell
* `lifetime`: Configured the maximum time that the Remote Shell will stay open
* `idle_time_out`: Configured the time the service will close and terminate the instance if idle for this time period
* `input_streams`: A simple token list of all input streams that are used in the execution (Default: `stdin`)
* `output_stream`: A simple token list of all output streams that are used in the execution (Default: `stdout stderr`)
* `open_content`: Additional values that come under the Open Content model of a SHell instance


### Endpoint Options

When setting the endpoint in the `Transport Options` there are some rules that apply

* `schema`: Will default to `https` if both this and `port` is not specified, changes to `http` if the port is `5985`
* `host`: Needs to be specified
* `port`: Will default to `5986` unless `http` is specified in the `schema` then it will be `5985`
* `path`: Will default to `wsman` if not specified

Examples

* `windows-host` -> https://windows-host:5986/wsman
* `windows-host:1111` -> https://windows-host:1111/wsman
* `windows-host:5985` -> http://windows-host:5985/wsman
* `https://windows-host` -> https://windows-host:5986/wsman
* `http://windows-host` -> http://windows-host:5985/wsman
* `https://windows-host:1111` -> https://windows-host:1111/wsman
* `https://windows-host:1234/wsman` -> https://windows-host:1234/wsman

### Authentication Methods

pywinrm support the following authentication methods

* `basic`: Basic auth only works for local Windows accounts and not domain accounts
* `kerberos`: Kerberos auth works for domain accounts and not local Windows accounts, recommended option for Domain accounts and if double hop auth support is required
* `ntlm`: NTLM auth works for both domain and local accounts, Kerberos should be favoured instead unless there are reasons where Kerberos won't work in your environment
* `certificate`: Certificate authentication is done through a certificate that is mapped to a local Windows account on the server
* `credssp`: CredSSP auth works for both domain and local accounts and also allows double hop/credential delegation to the remote server

#### Basic Auth Example

Basic auth is very basic and involves base64 encoding the credentials and sending them through over the message headers. Unless you are using HTTPS these credentials are viewable by anyone over the network and should be avoided for a more secure protocol.

```python
import winrm

s = winrm.Session(endpoint='windows-host.example.com', auth_method='basic', username='john.smith', password='secret')
r = s.run_ps('Write-Host', ['test'])
```

#### Kerberos Auth Example

There are extra dependencies that need to be installed to allow Kerberos support, see the top of the README for more details. Currently there are a few limitation of Kerberos like

* Kerberos only works when the client is in the same domain as the server
* Kerberos requires a valid ticket to be initialised outside of pywinrm using the kinit command
* Channel Binding Token does not work when CBT is set to `Strict`, use `(Get-Item -Path "WSMan:\localhost\Service\Auth\CbtHardeningLevel").Value` on the remote host to find the currently configured value

```python
import winrm

s = winrm.Session(endpoint='windows-host.example.com', auth_method='kerberos')
r = s.run_ps('Write-Host', ['test'])
```

#### NTLM Auth Example

NTLM auth is very simple to use and is similar to basic auth where only the username and password need to be supplied

```python
import winrm

s = winrm.Session(endpoint='windows-host.example.com', auth_method='ntlm', username='DOMAIN\\User', password='secret')
r = s.run_ps('Write-Host', ['test'])
```

#### Certificate Auth Example

Certificate auth is a bit more complex to set up and requires some work on the remote server before it can be used. It requires the transport options `cert_pem` and `cert_key_pem` to be set for it to work. For help with setting up certificate auth with a local windows account you can look at [this](http://www.hurryupandwait.io/blog/certificate-password-less-based-authentication-in-winrm) page for more detailed information.

```python
import winrm

s = winrm.Session(endpoint='windows-host.example.com', auth_method='certificate', cert_pem='/tmp/cert.pem', cert_key_pem='/tmp/key.pem')
r = s.run_ps('Write-Host', ['test'])
```

#### CredSSP Auth Example

There are extra dependencies that need to be installed to allow CredSSP support, see the top of the README for more details. CredSSP also requires the remote host to have TLS 1.2 configured or else the connection will fail. TLS 1.2 is installed by default from Server 2012 and Windows 8 onwards but older servers aren't configured by default. You can either use `` to use an older protocol (not recommended) or install TLS 1.2 support using some hotfixes by

* Installing the TLS 1.2 update from [Microsoft](https://support.microsoft.com/en-us/help/3080079/update-to-add-rds-support-for-tls-1.1-and-tls-1.2-in-windows-7-or-windows-server-2008-r2)
* Adding the TLS 1.2 registry keys as shown on this [page](https://technet.microsoft.com/en-us/library/dn786418.aspx#BKMK_SchannelTR_TLS12)

```python
import winrm

s = winrm.Session(endpoint='windows-host.example.com', auth_method='credssp', username='user@DOMAIN.COM', password='secret')
r = s.run_ps('Write-Host', ['test'])
```

## Message Encryption

Currently pywinrm does not support WinRM message encryption through NTLM, Kerberos or CredSSP authentication so the only way to keep your messages and credentials secured would be to use HTTPS as the transport mechanism. You can use the guide below under `Server Configuration` to see how to enable a HTTPS endpoint on your server. If you still wish to use a HTTP endpoint and loose ALL confidentiality in your messages you can enable unencrypted message support on the server by running the following command as an Admin

```ps
# Run in Powershell
Set-Item -Path "WSMan:\localhost\Service\AllowUnencrypted" -Value $true
```

As a repeat this should definitely not be used as your credentials and messages will allow anybody to see what is sent over the wire.

## Server Configuration

To enable WinRM on a server you can run the following [script](https://github.com/ansible/ansible/blob/devel/examples/scripts/ConfigureRemotingForAnsible.ps1). This script will do the following for you

* Set up a HTTPS listener using a self signed certificate
* Enable Basic authentication
* Enable CredSSP authentication if the `-EnableCredSSP` switch is set

For a production environment this script should be avoided as it opens up a few too many things and uses a self signed certificate but it helps to you give you an idea on

## Future Improvements

A list of things to add for the future

* Add support for NTLM/Kerberos/CredSSP message encryption over HTTP
* Add support for compressing WinRM messages

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
