from winrm import Session


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


def test_target_as_hostname_and_http_port():
    test_host = 'windows-host:5985'
    expected = 'http://windows-host:5985/wsman'
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
