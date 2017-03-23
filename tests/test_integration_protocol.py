# coding=utf-8
import re


def test_open_shell_and_close_wsmv_shell(wsmv_client_real):
    wsmv_client_real.open_shell()
    assert re.match('^\w{8}-\w{4}-\w{4}-\w{4}-\w{12}$', wsmv_client_real.shell_id)
    wsmv_client_real.close_shell()


def test_unicode_roundtrip_wsmv(wsmv_client_real):
    wsmv_client_real.open_shell(codepage=65001)

    try:
        output = wsmv_client_real.run_command(
            u'PowerShell', arguments=['-Command', 'Write-Host', u'こんにちは']
        )
        assert output.stdout == (u'こんにちは\n'.encode('utf-8'))
        assert output.stderr == b''
        assert output.return_code == 0
    finally:
        wsmv_client_real.close_shell()


def test_run_command_with_arguments_wsmv(wsmv_client_real):
    wsmv_client_real.open_shell()

    try:
        output = wsmv_client_real.run_command('ipconfig', ['/all'])
        assert output.stderr == b''
        assert b'Windows IP Configuration' in output.stdout
        assert output.return_code == 0
    finally:
        wsmv_client_real.close_shell()


def test_run_command_without_arguments_wsmv(wsmv_client_real):
    wsmv_client_real.open_shell()

    try:
        output = wsmv_client_real.run_command('hostname')
        assert output.stderr == b''
        assert len(output.stdout) > 0
        assert output.return_code == 0
    finally:
        wsmv_client_real.close_shell()


def test_run_command_taking_more_than_operation_timeout_sec_wsmv(wsmv_client_real):
    wsmv_client_real.open_shell()

    try:
        command = 'PowerShell -Command Start-Sleep -s {0}'.format(wsmv_client_real.operation_timeout_sec * 2)
        output = wsmv_client_real.run_command(command)
        assert output.stderr == b''
        assert output.stdout == b''
        assert output.return_code == 0
    finally:
        wsmv_client_real.close_shell()


def test_run_bad_command_wsmv(wsmv_client_real):
    wsmv_client_real.open_shell()

    try:
        output = wsmv_client_real.run_command('fake command')
        assert output.stderr == b"'fake' is not recognized as an internal or external command," \
                                b"\r\noperable program or batch file.\r\n"
        assert output.stdout == b''
        assert output.return_code == 1
    finally:
        wsmv_client_real.close_shell()


def test_run_ps_script_psrp(psrp_client_real):
    psrp_client_real.open_shell()

    try:
        test_script = """$DebugPreference = 'Continue'
            $VerbosePreference = 'Continue'
            $a = 'Test'
            Write-Host $a
            Write-Debug 'debug stream'
            Write-Verbose 'verbose stream'
            Write-Error 'error stream'
            Write-Output 'output stream'
            Write-Warning 'warning stream'"""
        output = psrp_client_real.run_command(test_script)
        assert b'error stream\n   + CategoryInfo          : NotSpecified: (:) [Write-Error], WriteErrorException' in output.error
        assert b'error stream\n   + CategoryInfo          : NotSpecified: (:) [Write-Error], WriteErrorException' in output.stderr
        assert output.debug == b'debug stream\n'
        assert output.output == b'output stream\n'
        assert output.stdout == b'Test\n\nDEBUG: debug stream\nVERBOSE: verbose stream\noutput stream\nWARNING: warning stream\n'
        assert output.verbose == b'verbose stream\n'
        assert output.warning == b'warning stream\n'
        assert output.return_code == 0
    finally:
        psrp_client_real.close_shell()


def test_run_ps_with_parameters_psrp(psrp_client_real):
    psrp_client_real.open_shell()

    try:
        output = psrp_client_real.run_command('Test-Path', ['-Path C:\Windows'])
        assert output.error == b''
        assert output.stderr == b''
        assert output.debug == b''
        assert output.output == b'True\n'
        assert output.stdout == b'True\n'
        assert output.verbose == b''
        assert output.warning == b''
        assert output.return_code == 0
    finally:
        psrp_client_real.close_shell()


def test_run_ps_with_exit_code_psrp(psrp_client_real):
    psrp_client_real.open_shell()

    try:
        output = psrp_client_real.run_command('exit 1')
        assert output.error == b''
        assert output.stderr == b''
        assert output.debug == b''
        assert output.output == b''
        assert output.stdout == b'\n'
        assert output.verbose == b''
        assert output.warning == b''
        assert output.return_code == 1
    finally:
        psrp_client_real.close_shell()


def test_run_ps_with_error_stop_psrp(psrp_client_real):
    psrp_client_real.open_shell()

    try:
        output = psrp_client_real.run_command("$ErrorActionPreference = 'Stop'; Write-Error test")
        assert b'Write-Error test : test' in output['error']
        assert b'Write-Error test : test' in output['stderr']
        assert output.debug == b''
        assert output.output == b''
        assert output.stdout == b''
        assert output.verbose == b''
        assert output.warning == b''
        assert output.return_code == 5
    finally:
        psrp_client_real.close_shell()


def test_run_ps_with_input_psrp(psrp_client_real):
    psrp_client_real.open_shell()

    try:
        test_script = "$a = Read-Host -Prompt message; Write-Host $a; $b = Read-Host -Prompt message2; Write-Host $b"
        output = psrp_client_real.run_command(test_script, responses=['first prompt', 'second prompt'])
        assert output.error == b''
        assert output.stderr == b''
        assert output.debug == b''
        assert output.output == b''
        assert output.stdout == b'first prompt\n\nsecond prompt\n\n'
        assert output.verbose == b''
        assert output.warning == b''
        assert output.return_code == 0
    finally:
        psrp_client_real.close_shell()


def test_run_with_multiple_fragments_psrp(psrp_client_real):
    psrp_client_real.open_shell()

    try:
        long_string = 'Long String' * 500000
        output = psrp_client_real.run_command('Write-Host', [long_string])
        assert output.error == b''
        assert output.stderr == b''
        assert output.debug == b''
        assert output.output == b''
        assert output.stdout == long_string.encode() + b'\n\n'
        assert output.verbose == b''
        assert output.warning == b''
        assert output.return_code == 0
    finally:
        psrp_client_real.close_shell()
