def test_change_default_timeout(protocol_fake):
    header = protocol_fake._get_soap_header()
    assert header['env:Header']['w:OperationTimeout'] == 'PT60S'
    protocol_fake.timeout = 120
    header = protocol_fake._get_soap_header()
    assert header['env:Header']['w:OperationTimeout'] == 'PT120S'


