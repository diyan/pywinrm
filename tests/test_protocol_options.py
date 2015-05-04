from winrm import Protocol


def test_change_default_timeout():
    protocol = Protocol(endpoint='http://windows-host:5985/wsman')

    header = protocol._get_soap_header()
    assert header['env:Header']['w:OperationTimeout'] == 'PT60S'
    protocol.timeout = 120
    header = protocol._get_soap_header()
    assert header['env:Header']['w:OperationTimeout'] == 'PT120S'


