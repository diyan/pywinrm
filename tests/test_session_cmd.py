import mock
import os
import uuid

from requests.models import Response

from tests.conftest import xml_str_compare
from winrm import Session
from winrm.exceptions import WinRMOperationTimeoutError

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

        # If we are mocking out a timeout error, throw the exception
        if b'The WS-Management service cannot complete the operation within the time specified in OperationTimeout' in response_file.encode():
            raise WinRMOperationTimeoutError

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
