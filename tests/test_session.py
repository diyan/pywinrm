from __future__ import unicode_literals

from winrm import Session


def test_run_cmd(protocol_fake):
    s = Session('windows-host', auth=('john.smith', 'secret'))
    r = s.run_cmd('ipconfig', ['/all'])

    assert r.status_code == 0
    assert 'Windows IP Configuration' in r.std_out
    assert len(r.std_err) == 0


def test_run_ps(protocol_fake):
    s = Session('windows-host', auth=('john.smith', 'secret'))
    r = s.run_ps('hostname')

    assert r.status_code == 0
    assert 'Windows IP Configuration' in r.std_out
    assert len(r.std_err) == 0


def test_run_ps_with_error(protocol_fake):
    # TODO test code in Session._clean_error_msg method
    pass


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
