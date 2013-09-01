import re
import pytest
xfail = pytest.mark.xfail


def test_open_shell_and_close_shell(winrm_real):
    shell_id = winrm_real.open_shell()
    assert re.match('^\w{8}-\w{4}-\w{4}-\w{4}-\w{12}$', shell_id)

    winrm_real.close_shell(shell_id)


def test_run_command_with_arguments_and_cleanup_command(winrm_real):
    shell_id = winrm_real.open_shell()
    command_id = winrm_real.run_command(shell_id, 'ipconfig', ['/all'])
    assert re.match('^\w{8}-\w{4}-\w{4}-\w{4}-\w{12}$', command_id)

    winrm_real.cleanup_command(shell_id, command_id)
    winrm_real.close_shell(shell_id)


def test_run_command_without_arguments_and_cleanup_command(winrm_real):
    shell_id = winrm_real.open_shell()
    command_id = winrm_real.run_command(shell_id, 'hostname')
    assert re.match('^\w{8}-\w{4}-\w{4}-\w{4}-\w{12}$', command_id)

    winrm_real.cleanup_command(shell_id, command_id)
    winrm_real.close_shell(shell_id)


def test_get_command_output(winrm_real):
    shell_id = winrm_real.open_shell()
    command_id = winrm_real.run_command(shell_id, 'ipconfig', ['/all'])
    stdout, stderr, return_code = winrm_real.get_command_output(
        shell_id, command_id)

    assert return_code == 0
    assert 'Windows IP Configuration' in stdout
    assert len(stderr) == 0

    winrm_real.cleanup_command(shell_id, command_id)
    winrm_real.close_shell(shell_id)


@xfail()
def test_set_timeout(winrm_real):
    raise NotImplementedError()


@xfail()
def test_set_max_env_size(winrm_real):
    raise NotImplementedError()


@xfail()
def test_set_locale(winrm_real):
    raise NotImplementedError()