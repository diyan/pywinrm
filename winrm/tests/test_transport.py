from winrm import transport
import mock


def test_transport_send_success(mocked_requests):
    # Return a 200 and make sure the text is returned.
    mocked_requests.start_mock()
    mocked_requests.session_send_mock.return_value = mocked_requests.get_request_response(status_code=200,
                                                                                          text=b'success')
    test_transport = transport.Transport('testendpoint', username='fakeusername', password='fakepassword',
                                         auth_method='basic')
    result = test_transport.send_message('test')
    assert result == 'success'
    mocked_requests.stop_mock()


def test_transport_send_401(mocked_requests):
    # Return a 401 and make a InvalidCredentialsError exception is raised
    mocked_requests.start_mock()
    mocked_requests.session_send_mock.return_value = mocked_requests.get_request_response(status_code=401,
                                                                                          text=b'auth failure')
    expected_exception = None
    try:
        test_transport = transport.Transport('testendpoint', username='fakeusername', password='fakepassword',
                                             auth_method='basic')
        result = test_transport.send_message('test')
    except transport.InvalidCredentialsError as exc:
        expected_exception = exc

    assert isinstance(expected_exception, transport.InvalidCredentialsError)
    mocked_requests.stop_mock()


def test_transport_send_operation_timeout(mocked_requests):
    # Make sure we can raise an Operation Timeout exception properly
    mocked_requests.start_mock()
    mocked_requests.session_send_mock.return_value = mocked_requests.get_request_response(status_code=500,
                                                                                          text=b'Code="2150858793"')
    expected_exception = None
    try:
        test_transport = transport.Transport('testendpoint', username='fakeusername', password='fakepassword',
                                             auth_method='basic')
        result = test_transport.send_message('asdfhttp://schemas.microsoft.com/wbem/wsman/1/windows/shell/Receiveasdf')
    except transport.WinRMOperationTimeoutError as exc:
        expected_exception = exc

    assert isinstance(expected_exception, transport.WinRMOperationTimeoutError)
    mocked_requests.stop_mock()


def test_transport_send_random_error(mocked_requests):
    # With a random error returned, make sure we are able to view the details of the error if needed.
    mocked_requests.start_mock()
    mocked_requests.set_closed_session_error()
    expected_exception = None
    try:
        test_transport = transport.Transport('testendpoint', username='fakeusername', password='fakepassword',
                                             auth_method='basic')
        result = test_transport.send_message('fake_message')
    except transport.WinRMTransportError as exc:
        expected_exception = exc

    assert isinstance(expected_exception, transport.WinRMTransportError)
    assert expected_exception.fault_code() == "s:Sender"
    assert expected_exception.fault_subcode() == "w:InvalidSelectors"
    assert 'service cannot process the request' in expected_exception.fault_reason()
    mocked_requests.stop_mock()


def test_transport_send_nocontent(mocked_requests):
    # Test a random error with no content.
    mocked_requests.start_mock()
    mocked_requests.session_send_mock.return_value = mocked_requests.get_request_response(status_code=500, text=None)
    expected_exception = None
    try:
        test_transport = transport.Transport('testendpoint', username='fakeusername', password='fakepassword',
                                             auth_method='basic')
        result = test_transport.send_message('asdfhttp://schemas.microsoft.com/wbem/wsman/1/windows/shell/Receiveasdf')
    except transport.WinRMTransportError as exc:
        expected_exception = exc

    assert isinstance(expected_exception, transport.WinRMTransportError)
    assert expected_exception.fault_code() is None
    assert expected_exception.fault_subcode() is None
    assert expected_exception.fault_reason() is None
    assert expected_exception.dict_response() is None
    mocked_requests.stop_mock()
