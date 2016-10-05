from winrm import Session


def test_run_cmd(protocol_fake):
    # TODO this test should cover __init__ method
    s = Session('windows-host', auth=('john.smith', 'secret'))
    s.protocol = protocol_fake

    r = s.run_cmd('ipconfig', ['/all'])

    assert r.status_code == 0
    assert b'Windows IP Configuration' in r.std_out
    assert len(r.std_err) == 0


def test_run_ps(protocol_fake):
    s = Session('windows-host', auth=('john.smith', 'secret'))
    s.protocol = protocol_fake

    script = """
        $strComputer = $Host
        Clear
        $RAM = WmiObject Win32_ComputerSystem
        $MB = 1048576

        "Installed Memory: " + [int]($RAM.TotalPhysicalMemory /$MB) + " MB"
    """
    r = s.run_ps(script)

    assert r.status_code == 0
    assert b'Installed Memory: 2044 MB' in r.std_out
    assert len(r.std_err) == 0


def test_target_as_hostname():
    s = Session('windows-host', auth=('john.smith', 'secret'))
    assert s.url == 'http://windows-host:5985/wsman'


def test_target_as_hostname_then_port():
    s = Session('windows-host:1111', auth=('john.smith', 'secret'))
    assert s.url == 'http://windows-host:1111/wsman'


def test_target_as_schema_then_hostname():
    s = Session('http://windows-host', auth=('john.smith', 'secret'))
    assert s.url == 'http://windows-host:5985/wsman'


def test_target_as_schema_then_hostname_then_port():
    s = Session('http://windows-host:1111', auth=('john.smith', 'secret'))
    assert s.url == 'http://windows-host:1111/wsman'


def test_target_as_full_url():
    s = Session('http://windows-host:1111/wsman', auth=(
        'john.smith', 'secret'))
    assert s.url == 'http://windows-host:1111/wsman'


def test_target_with_dots():
    s = Session('windows-host.example.com', auth=('john.smith', 'secret'))
    assert s.url == 'http://windows-host.example.com:5985/wsman'
