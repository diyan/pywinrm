import pytest
import copy
import xmltodict

from winrm.tests import base as base_test
from winrm.tests.winrm_responses import shells as shell_responses
from winrm.protocol import Protocol


def convert_to_dict(ordered_dict):
    new_dict = dict()
    for name, value in ordered_dict.items():
        if isinstance(value, dict):
            new_dict[name] = convert_to_dict(value)
        else:
            new_dict[name] = value
    return new_dict


def test_open_shell_and_close_shell(protocol_fake):
    shell_id = protocol_fake.open_shell()
    assert shell_id == '11111111-1111-1111-1111-111111111113'

    protocol_fake.close_shell(shell_id, close_session=True)


def test_run_command_with_arguments_and_cleanup_command(protocol_fake):
    shell_id = protocol_fake.open_shell()
    command_id = protocol_fake.run_command(shell_id, 'ipconfig', ['/all'])
    assert command_id == '11111111-1111-1111-1111-111111111114'

    protocol_fake.cleanup_command(shell_id, command_id)
    protocol_fake.close_shell(shell_id)


def test_run_command_without_arguments_and_cleanup_command(protocol_fake):
    shell_id = protocol_fake.open_shell()
    command_id = protocol_fake.run_command(shell_id, 'hostname')
    assert command_id == '11111111-1111-1111-1111-111111111114'

    protocol_fake.cleanup_command(shell_id, command_id)
    protocol_fake.close_shell(shell_id)


def test_get_command_output(protocol_fake):
    shell_id = protocol_fake.open_shell()
    command_id = protocol_fake.run_command(shell_id, 'ipconfig', ['/all'])
    std_out, std_err, status_code = protocol_fake.get_command_output(
        shell_id, command_id)
    assert status_code == 0
    assert b'Windows IP Configuration' in std_out
    assert len(std_err) == 0

    protocol_fake.cleanup_command(shell_id, command_id)
    protocol_fake.close_shell(shell_id)


def test_send_command_input(protocol_fake):
    shell_id = protocol_fake.open_shell()
    command_id = protocol_fake.run_command(shell_id, u'cmd')
    protocol_fake.send_command_input(shell_id, command_id, u'echo "hello world" && exit\r\n')
    std_out, std_err, status_code = protocol_fake.get_command_output(
        shell_id, command_id)
    assert status_code == 0
    assert b'hello world' in std_out
    assert len(std_err) == 0

    protocol_fake.cleanup_command(shell_id, command_id)
    protocol_fake.close_shell(shell_id)


def test_set_timeout_as_sec():
    protocol = Protocol('endpoint',
                        username='username',
                        password='password',
                        read_timeout_sec='30',
                        operation_timeout_sec='29')
    assert protocol.read_timeout_sec == 30
    assert protocol.operation_timeout_sec == 29


def test_fail_set_read_timeout_as_sec():
    with pytest.raises(ValueError) as exc:
        Protocol('endpoint',
                 username='username',
                 password='password',
                 read_timeout_sec='30a',
                 operation_timeout_sec='29')
    assert str(exc.value) == "failed to parse read_timeout_sec as int: " \
        "invalid literal for int() with base 10: '30a'"


def test_fail_set_operation_timeout_as_sec():
    with pytest.raises(ValueError) as exc:
        Protocol('endpoint',
                 username='username',
                 password='password',
                 read_timeout_sec=30,
                 operation_timeout_sec='29a')
    assert str(exc.value) == "failed to parse operation_timeout_sec as int: " \
        "invalid literal for int() with base 10: '29a'"


class TestTransportShells(base_test.BaseTest):

    def test_open_shell(self):
        self.mocked_request.post('https://example.com', text=shell_responses.OPEN_SHELL_RESPONSE)
        server_conn = Protocol(endpoint="https://example.com",
                               username='test',
                               password='test',
                               )
        response = server_conn.open_shell()
        self.assertEqual('5207F2DF-E6CA-4D10-8C7F-5380F01D6FDE', response)

        # MessageID will be dynamic, no need to compare
        expected_shell_request = xmltodict.parse(copy.deepcopy(shell_responses.OPEN_SHELL_REQUEST))
        actual_shell_request = xmltodict.parse(copy.deepcopy(self.mocked_request.request_history[0].body))
        del expected_shell_request['env:Envelope']['env:Header']['a:MessageID']
        del actual_shell_request['env:Envelope']['env:Header']['a:MessageID']

        self.assertEqual(convert_to_dict(expected_shell_request), convert_to_dict(actual_shell_request))
