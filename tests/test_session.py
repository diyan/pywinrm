import mock
import os
import pytest
import uuid

from requests.models import Response

from tests.conftest import xml_str_compare
from winrm import Session
from winrm.exceptions import WinRMOperationTimeoutError, WinRMTransportError, WinRMError


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
def test_wsmv_mismatch_message_id(mock_send, mock_uuid):
    global test_name
    global test_message_counter
    test_name = 'test_wsmv_mismatch_message_id'
    test_message_counter = 1
    with pytest.raises(WinRMError) as excinfo:
        s = Session(endpoint='windows-host', username='john.smith', password='secret')
        s.run_cmd('test')

    assert str(excinfo.value) == "Response related to Message ID: 'uuid:11111111-1111-1111-1111-111111111112' " \
                                 "does not match request Message ID: 'uuid:11111111-1111-1111-1111-111111111111'"


@mock.patch('requests.sessions.Session.send', side_effect=send)
@mock.patch('uuid.uuid4', side_effect=mock_uuid)
def test_run_ps_script(mock_send, mock_uuid):
    # This was run on a Server 2016 box so Write-Information was available
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
    assert actual.information[0]['message_data'] == b'Test'
    assert actual.information[1]['message_data'] == b'info stream'
    assert actual.output == b'output stream\n'
    assert actual.stdout == b'Test\nDEBUG: debug stream\nVERBOSE: verbose stream\noutput stream\nWARNING: warning stream\n'
    assert actual.verbose == b'verbose stream\n'
    assert actual.warning == b'warning stream\n'
    assert actual.return_code == 0


@mock.patch('requests.sessions.Session.send', side_effect=send)
@mock.patch('uuid.uuid4', side_effect=mock_uuid)
def test_run_ps_with_parameters(mock_send, mock_uuid):
    # This was run on a Server 2012 R2 box
    global test_name
    global test_message_counter
    test_name = 'test_run_ps_with_parameters'
    test_message_counter = 1

    s = Session(endpoint='windows-host', username='john.smith', password='secret')
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


@mock.patch('requests.sessions.Session.send', side_effect=send)
@mock.patch('uuid.uuid4', side_effect=mock_uuid)
def test_run_ps_with_exit_code(mock_send, mock_uuid):
    # This was run on a Server 2012 box
    global test_name
    global test_message_counter
    test_name = 'test_run_ps_with_exit_code'
    test_message_counter = 1

    s = Session(endpoint='windows-host', username='john.smith', password='secret')
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


@mock.patch('requests.sessions.Session.send', side_effect=send)
@mock.patch('uuid.uuid4', side_effect=mock_uuid)
def test_run_ps_with_error_stop(mock_send, mock_uuid):
    # This was run on a Server 2008 R2 box
    global test_name
    global test_message_counter
    test_name = 'test_run_ps_with_error_stop'
    test_message_counter = 1

    s = Session(endpoint='windows-host', username='john.smith', password='secret')
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


@mock.patch('requests.sessions.Session.send', side_effect=send)
@mock.patch('uuid.uuid4', side_effect=mock_uuid)
def test_run_ps_with_responses(mock_send, mock_uuid):
    # This was run on a Server 2008 box
    global test_name
    global test_message_counter
    test_name = 'test_run_ps_with_responses'
    test_message_counter = 1

    s = Session(endpoint='windows-host', username='john.smith', password='secret')
    test_script = "$a = Read-Host -Prompt message; Write-Host $a; $b = Read-Host -Prompt message2; Write-Host $b"
    actual = s.run_ps(test_script, responses=['first prompt', 'second prompt'])

    assert actual['error'] == b''
    assert actual['stderr'] == b''
    assert actual['debug'] == b''
    assert actual['output'] == b''
    assert actual['stdout'] == b'first prompt\n\nsecond prompt\n\n'
    assert actual['verbose'] == b''
    assert actual['warning'] == b''
    assert actual['return_code'] == 0


@mock.patch('requests.sessions.Session.send', side_effect=send)
@mock.patch('uuid.uuid4', side_effect=mock_uuid)
def test_run_with_multiple_fragments(mock_send, mock_uuid):
    # This was run on a Server 2012 R2 box
    global test_name
    global test_message_counter
    test_name = 'test_run_with_multiple_fragments'
    test_message_counter = 1

    s = Session(endpoint='windows-host', username='john.smith', password='secret')
    long_string = 'Long String' * 5000
    actual = s.run_ps('Write-Host', [long_string])

    assert actual['error'] == b''
    assert actual['stderr'] == b''
    assert actual['debug'] == b''
    assert actual['output'] == b''
    assert actual['stdout'] == long_string.encode() + b'\n\n'
    assert actual['verbose'] == b''
    assert actual['warning'] == b''
    assert actual['return_code'] == 0


@mock.patch('requests.sessions.Session.send', side_effect=send)
@mock.patch('uuid.uuid4', side_effect=mock_uuid)
def test_run_with_pipeline_input(mock_send, mock_uuid):
    # This was run on a Server 2012 R2 box
    global test_name
    global test_message_counter
    test_name = 'test_run_with_pipeline_input'
    test_message_counter = 1

    s = Session(endpoint='windows-host', username='john.smith', password='secret')
    script = """
        begin {
            $DebugPreference = 'Continue'
            Write-Debug "Start Block"
        }
        process {
            Write-Debug "Process Block $input"
        }
        end {
            Write-Debug "End Block"
        }"""
    actual = s.run_ps(script, inputs=['input 1', 'input 2'])
    assert actual.error == b''
    assert actual.stderr == b''
    assert actual.debug == b'Start Block\nProcess Block\nProcess Block\nEnd Block\n'
    assert actual.output == b'input 1\ninput 2\n'
    assert actual.stdout == b'DEBUG: Start Block\nDEBUG: Process Block\ninput 1\nDEBUG: Process Block\ninput 2\nDEBUG: End Block\n'
    assert actual.verbose == b''
    assert actual.warning == b''
    assert actual.return_code == 0


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
