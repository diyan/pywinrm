import pytest

from winrm.protocol import Protocol


def test_open_shell_and_close_shell(protocol_fake):
    shell_id = protocol_fake.open_shell()
    assert shell_id == '11111111-1111-1111-1111-111111111113'

    protocol_fake.close_shell(shell_id)


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
        protocol = Protocol('endpoint',
                            username='username',
                            password='password',
                            read_timeout_sec='30a',
                            operation_timeout_sec='29')
    assert str(exc.value) == "failed to parse read_timeout_sec as int: " \
        "invalid literal for int() with base 10: '30a'"


def test_fail_set_operation_timeout_as_sec():
    with pytest.raises(ValueError) as exc:
        protocol = Protocol('endpoint',
                            username='username',
                            password='password',
                            read_timeout_sec=30,
                            operation_timeout_sec='29a')
    assert str(exc.value) == "failed to parse operation_timeout_sec as int: " \
        "invalid literal for int() with base 10: '29a'"
