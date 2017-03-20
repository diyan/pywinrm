from winrm import Session


def test_run_cmd():
    s = Session(endpoint='windows-host', username='john.smith', password='secret')
    actual = s.run_cmd('ipconfig', ['/all'])

    assert actual['stderr'] == b''
    assert b'Windows IP Configuration' in actual['stdout']
    assert actual['return_code'] == 0


def test_run_cmd_fail():
    s = Session(endpoint='windows-host', username='john.smith', password='secret')
    actual = s.run_cmd('fake command')

    assert actual['stderr'] == b"'fake' is not recognized as an internal or external command,\r\noperable program or batch file.\r\n"
    assert actual['stdout'] == b''
    assert actual['return_code'] == 1


def test_run_ps_in_cmd():
    s = Session(endpoint='windows-host', username='john.smith', password='secret')
    actual = s.run_cmd('powershell.exe', ['Write-Host', 'testing'])

    assert actual['stderr'] == b''
    assert actual['stdout'] == b'testing\n'
    assert actual['return_code'] == 0


def test_run_ps_in_cmd_fail():
    s = Session(endpoint='windows-host', username='john.smith', password='secret')
    actual = s.run_cmd('powershell.exe', ['Write-Error', 'testing'])

    assert b'Write-Error testing : testing\r\n' in actual['stderr']
    assert actual['stdout'] == b''
    assert actual['return_code'] == 1


def test_run_ps_script():
    s = Session(endpoint='windows-host', username='john.smith', password='secret')
    test_script = """$DebugPreference = 'Continue'
        $VerbosePreference = 'Continue'
        $a = 'Test'
        Write-Host $a
        Write-Debug 'debug stream'
        Write-Verbose 'verbose stream'
        Write-Error 'error stream'
        Write-Output 'output stream'"""
    actual = s.run_ps(test_script)

    assert b'error stream\n   + CategoryInfo          : NotSpecified: (:) [Write-Error], WriteErrorException' in actual.error
    assert b'error stream\n   + CategoryInfo          : NotSpecified: (:) [Write-Error], WriteErrorException' in actual.stderr
    assert actual.debug == b'debug stream\n'
    assert actual.information == []
    assert actual.output == b'output stream\n'
    assert actual.stdout == b'Test\n\nDEBUG: debug stream\nVERBOSE: verbose stream\noutput stream\n'
    assert actual.verbose == b'verbose stream\n'
    assert actual.return_code == 0


def test_run_ps_with_parameters():
    s = Session(endpoint='windows-host', username='john.smith', password='secret')
    actual = s.run_ps('Test-Path', ['-Path C:\Windows'])

    assert actual.error == b''
    assert actual.stderr == b''
    assert actual.debug == b''
    assert actual.information == []
    assert actual.output == b'True\n'
    assert actual.stdout == b'True\n'
    assert actual.verbose == b''
    assert actual.return_code == 0


def test_run_ps_with_exit_code():
    s = Session(endpoint='windows-host', username='john.smith', password='secret')
    actual = s.run_ps('exit 1')

    assert actual.error == b''
    assert actual.stderr == b''
    assert actual.debug == b''
    assert actual.information == []
    assert actual.output == b''
    assert actual.stdout == b'\n'
    assert actual.verbose == b''
    assert actual.return_code == 1


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
