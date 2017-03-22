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
