import mock
import os
import uuid

from requests.models import Response

from tests.conftest import xml_str_compare
from winrm import Session
from winrm.exceptions import WinRMOperationTimeoutError, WinRMTransportError


test_name = ''
test_message_counter = 1


def mock_uuid():
    return uuid.UUID('11111111-1111-1111-1111-111111111111')


def send(req, timeout='ignore'):
    global test_name
    global test_message_counter

    assert req.headers['Content-Type'] == 'application/soap+xml;charset=UTF-8'
    parent_path = os.path.join(os.path.dirname(__file__), 'test_xmls/%s/%d-' % (test_name, test_message_counter))
    with open("%srequest.xml" % parent_path, 'r') as file:
        request_file = file.read()
    with open("%sresponse.xml" % parent_path, 'r') as file:
        response_file = file.read()
    if xml_str_compare(req.body, request_file):
        test_message_counter += 1

        # If we are mocking out an error, throw the exception
        if b'The WS-Management service cannot complete the operation within the time specified in OperationTimeout' in response_file.encode():
            raise WinRMOperationTimeoutError
        if b'WSManFault xmlns:f="http://schemas.microsoft.com/wbem/wsman/1/wsmanfault"' in response_file.encode():
            raise WinRMTransportError('http', 'Bad HTTP response returned from server. Code 500')

        response = Response()
        response.status_code = 200
        response._content = response_file.encode()
        return response
    else:
        raise Exception(
            'Message was not expected, Test Name: %s, Message Counter: %d' % (test_name, test_message_counter))


@mock.patch('requests.sessions.Session.send', side_effect=send)
@mock.patch('uuid.uuid4', side_effect=mock_uuid)
def test_run_cmd(mock_send, mock_uuid):
    global test_name
    global test_message_counter
    test_name = 'test_run_cmd'
    test_message_counter = 1

    s = Session(endpoint='windows-host', username='john.smith', password='secret')
    actual = s.run_cmd('ipconfig', ['/all'])

    assert actual['stderr'] == b''
    assert b'Windows IP Configuration' in actual['stdout']
    assert actual['return_code'] == 0


@mock.patch('requests.sessions.Session.send', side_effect=send)
@mock.patch('uuid.uuid4', side_effect=mock_uuid)
def test_run_cmd_fail(mock_send, mock_uuid):
    global test_name
    global test_message_counter
    test_name = 'test_run_cmd_fail'
    test_message_counter = 1

    s = Session(endpoint='windows-host', username='john.smith', password='secret')
    actual = s.run_cmd('fake command')

    assert actual.stderr == b"'fake' is not recognized as an internal or external command,\r\noperable program or batch file.\r\n"
    assert actual.stdout == b''
    assert actual.return_code == 1


@mock.patch('requests.sessions.Session.send', side_effect=send)
@mock.patch('uuid.uuid4', side_effect=mock_uuid)
def test_run_cmd_get_config_fail(mock_send, mock_uuid):
    global test_name
    global test_message_counter
    test_name = 'test_run_cmd_get_config_fail'
    test_message_counter = 1

    s = Session(endpoint='windows-host', username='john.smith', password='secret')
    actual = s.run_cmd('ipconfig', ['/all'])

    assert actual['stderr'] == b''
    assert b'Windows IP Configuration' in actual['stdout']
    assert actual['return_code'] == 0


@mock.patch('requests.sessions.Session.send', side_effect=send)
@mock.patch('uuid.uuid4', side_effect=mock_uuid)
def test_run_ps_in_cmd(mock_send, mock_uuid):
    global test_name
    global test_message_counter
    test_name = 'test_run_ps_in_cmd'
    test_message_counter = 1

    s = Session(endpoint='windows-host', username='john.smith', password='secret')
    actual = s.run_cmd('powershell.exe', ['Write-Host', 'testing'])

    assert actual.stderr == b''
    assert actual.stdout == b'testing\n'
    assert actual.return_code == 0


@mock.patch('requests.sessions.Session.send', side_effect=send)
@mock.patch('uuid.uuid4', side_effect=mock_uuid)
def test_run_ps_in_cmd_fail(mock_send, mock_uuid):
    global test_name
    global test_message_counter
    test_name = 'test_run_ps_in_cmd_fail'
    test_message_counter = 1

    s = Session(endpoint='windows-host', username='john.smith', password='secret')
    actual = s.run_cmd('powershell.exe', ['Write-Error', 'testing'])

    assert b'Write-Error testing : testing\r\n' in actual['stderr']
    assert actual.stdout == b''
    assert actual.return_code == 1


@mock.patch('requests.sessions.Session.send', side_effect=send)
@mock.patch('uuid.uuid4', side_effect=mock_uuid)
def test_run_ps_in_cmd_fail(mock_send, mock_uuid):
    global test_name
    global test_message_counter
    test_name = 'test_run_cmd_timeout_error'
    test_message_counter = 1

    s = Session(endpoint='windows-host', username='john.smith', password='secret')
    actual = s.run_cmd('PowerShell -Command Start-Sleep -s 30; Write-Host Test')

    assert actual['stderr'] == b''
    assert actual.stdout == b'Test\n'
    assert actual.return_code == 0


@mock.patch('requests.sessions.Session.send', side_effect=send)
@mock.patch('uuid.uuid4', side_effect=mock_uuid)
def test_run_ps_script(mock_send, mock_uuid):
    global test_name
    global test_message_counter
    test_name = 'test_run_ps_script'
    test_message_counter = 1

    s = Session(endpoint='windows-host', username='john.smith', password='secret')
    test_script = """$DebugPreference = 'Continue'
        $VerbosePreference = 'Continue'
        $a = 'Test'
        Write-Host $a
        Write-Debug 'debug stream'
        Write-Verbose 'verbose stream'
        Write-Error 'error stream'
        Write-Output 'output stream'
        Write-Warning 'warning stream'
        Write-Information -Message 'info stream'"""
    actual = s.run_ps(test_script)

    assert b'error stream\n   + CategoryInfo          : NotSpecified: (:) [Write-Error], WriteErrorException' in actual.error
    assert b'error stream\n   + CategoryInfo          : NotSpecified: (:) [Write-Error], WriteErrorException' in actual.stderr
    assert actual.debug == b'debug stream\n'
    # assert actual.information[0]['message_data'] == b'Test' # Get message from Win2016 Host
    # assert actual.information[1]['message_data'] == b'info stream' # Get message from Win2016 Host
    assert actual.output == b'output stream\n'
    # assert actual.stdout == b'Test\nDEBUG: debug stream\nVERBOSE: verbose stream\noutput stream\nWARNING: warning stream\n' # Get message from Win2016 Host
    assert actual.stdout == b'Test\n\nDEBUG: debug stream\nVERBOSE: verbose stream\noutput stream\nWARNING: warning stream\n'
    assert actual.verbose == b'verbose stream\n'
    assert actual.warning == b'warning stream\n'
    assert actual.return_code == 0


'''
def test_run_ps_with_parameters():
    s = Session(endpoint='192.168.1.6', username='Administrator', password='Password01',
                server_cert_validation='ignore')
    actual = s.run_ps('Test-Path', ['-Path C:\Windows'])

    assert actual.error == b''
    assert actual.stderr == b''
    assert actual.debug == b''
    assert actual.information == []
    assert actual.output == b'True\n'
    assert actual.stdout == b'True\n'
    assert actual.verbose == b''
    assert actual.warning == b''
    assert actual.return_code == 0


def test_run_ps_with_exit_code():
    s = Session(endpoint='192.168.1.6', username='Administrator', password='Password01',
                server_cert_validation='ignore')
    actual = s.run_ps('exit 1')

    assert actual.error == b''
    assert actual.stderr == b''
    assert actual.debug == b''
    assert actual.information == []
    assert actual.output == b''
    assert actual.stdout == b'\n'
    assert actual.verbose == b''
    assert actual.warning == b''
    assert actual.return_code == 1


def test_run_ps_with_error_stop():
    s = Session(endpoint='192.168.1.6', username='Administrator', password='Password01',
                server_cert_validation='ignore')
    actual = s.run_ps("$ErrorActionPreference = 'Stop'; Write-Error test")

    assert b'Write-Error test : test' in actual['error']
    assert b'Write-Error test : test' in actual['stderr']
    assert actual['debug'] == b''
    assert actual['information'] == []
    assert actual['output'] == b''
    assert actual['stdout'] == b''
    assert actual['verbose'] == b''
    assert actual['warning'] == b''
    assert actual['return_code'] == 5


def test_run_ps_with_input():
    s = Session(endpoint='192.168.1.6', username='Administrator', password='Password01',
                server_cert_validation='ignore')
    test_script = "$a = Read-Host -Prompt message; Write-Host $a; $b = Read-Host -Prompt message2; Write-Host $b"
    actual = s.run_ps(test_script, responses=['first prompt', 'second prompt'])

    assert actual['error'] == b''
    assert actual['stderr'] == b''
    assert actual['debug'] == b''
    assert actual['output'] == b''
    assert actual['stdout'] == b'first prompt\nsecond prompt\n'
    assert actual['verbose'] == b''
    assert actual['warning'] == b''
    assert actual['return_code'] == 0
'''


def test_target_as_hostname():
    test_host = 'windows-host'
    expected = 'https://windows-host:5986/wsman'
    actual = Session._build_url(test_host)
    assert actual == expected


def test_target_as_hostname_and_port():
    test_host = 'windows-host:1111'
    expected = 'https://windows-host:1111/wsman'
    actual = Session._build_url(test_host)
    assert actual == expected


def test_target_as_hostname_and_http_port():
    test_host = 'windows-host:5985'
    expected = 'http://windows-host:5985/wsman'
    actual = Session._build_url(test_host)
    assert actual == expected


def test_target_as_schema_http_then_hostname():
    test_host = 'http://windows-host'
    expected = 'http://windows-host:5985/wsman'
    actual = Session._build_url(test_host)
    assert actual == expected


def test_target_as_schema_https_then_hostname():
    test_host = 'https://windows-host'
    expected = 'https://windows-host:5986/wsman'
    actual = Session._build_url(test_host)
    assert actual == expected


def test_target_as_schema_then_hostname_then_port():
    test_host = 'https://windows-host:1111'
    expected = 'https://windows-host:1111/wsman'
    actual = Session._build_url(test_host)
    assert actual == expected


def test_target_as_full_url():
    test_host = 'https://windows-host:1111/wsman'
    expected = 'https://windows-host:1111/wsman'
    actual = Session._build_url(test_host)
    assert actual == expected


def test_target_with_dots():
    test_host = 'https://windows-host.example.com:1111/wsman'
    expected = 'https://windows-host.example.com:1111/wsman'
    actual = Session._build_url(test_host)
    assert actual == expected
