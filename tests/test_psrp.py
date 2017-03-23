import pytest

from winrm.contants import PsrpPSInvocationState, PsrpRunspacePoolState
from winrm.exceptions import WinRMError
from winrm.psrp.psrp import PsrpClient, Pipeline


def test_run_command_without_opening_runspace():
    with pytest.raises(WinRMError) as excinfo:
        c = PsrpClient({'endpoint': 'windows-host', 'username': 'test', 'password': 'test', 'auth_method': 'basic'})
        c.run_command('command')

    assert str(excinfo.value) == 'Cannot execute command pipeline as the RunspacePool State is not Opened'


def test_run_command_with_existing_pipelines():
    with pytest.raises(WinRMError) as excinfo:
        c = PsrpClient({'endpoint': 'windows-host', 'username': 'test', 'password': 'test', 'auth_method': 'basic'})
        failed_pipeline = Pipeline(c)
        failed_pipeline.state = PsrpPSInvocationState.FAILED

        stopped_pipeline = Pipeline(c)
        stopped_pipeline.state = PsrpPSInvocationState.STOPPED

        running_pipeline = Pipeline(c)
        running_pipeline.state = PsrpPSInvocationState.RUNNING

        c.state = PsrpRunspacePoolState.OPENED
        c.max_runspaces = 1
        c.pipelines = [failed_pipeline, stopped_pipeline, running_pipeline]
        c.run_command('command')

    assert str(excinfo.value) == 'Cannot create new command pipeline as Runspace Pool already ' \
                                 'has 1 running, max allowed 1'


def test_set_max_envelope_size_newer_protocol():
    c = PsrpClient({'endpoint': 'windows-host', 'username': 'test', 'password': 'test', 'auth_method': 'basic'})
    c._set_max_envelope_size('2.2')
    assert c.server_config['max_envelope_size'] == 512000


def test_set_max_envelope_size_older_protocol():
    c = PsrpClient({'endpoint': 'windows-host', 'username': 'test', 'password': 'test', 'auth_method': 'basic'})
    c._set_max_envelope_size('2.1')
    assert c.server_config['max_envelope_size'] == 153600


def test_input_callback_in_pipeline_not_enough_responses():
    with pytest.raises(WinRMError) as excinfo:
        c = PsrpClient({'endpoint': 'windows-host', 'username': 'test', 'password': 'test', 'auth_method': 'basic'})
        p = Pipeline(c)
        p._input_callback('', '', '')

    assert str(excinfo.value) == 'Expecting response index at 1 but only 0 responses have been pre-set'
