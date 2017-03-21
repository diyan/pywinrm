'''
def test_run_ps_script():
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
