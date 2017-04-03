import pytest

from requests.models import Response

from winrm.exceptions import InvalidCredentialsError, WinRMError, WinRMTransportError, WinRMOperationTimeoutError
from winrm.transport import Transport


def test_server_cert_validation_choices():
    actual = Transport(auth_method='basic', username='test', password='test')
    assert actual.server_cert_validation == 'validate'

    actual_ignore = Transport(server_cert_validation='ignore', auth_method='basic', username='test', password='test')
    assert actual_ignore.server_cert_validation == 'ignore'

    actual_validate = Transport(server_cert_validation='validate', auth_method='basic', username='test', password='test')
    assert actual_validate.server_cert_validation == 'validate'

    with pytest.raises(WinRMError) as excinfo:
        Transport(server_cert_validation='broken', auth_method='basic', username='test', password='test')

    assert str(excinfo.value) == 'invalid server_cert_validation mode: broken'


def test_defensive_parsing_of_bool():
    actual_true_string = Transport(kerberos_delegation='true', auth_method='basic', username='test', password='test')
    assert actual_true_string.kerberos_delegation

    actual_false_string = Transport(kerberos_delegation='false', auth_method='basic', username='test', password='test')
    assert not actual_false_string.kerberos_delegation

    actual_true = Transport(kerberos_delegation=True, auth_method='basic', username='test', password='test')
    assert actual_true.kerberos_delegation

    actual_false = Transport(kerberos_delegation=False, auth_method='basic', username='test', password='test')
    assert not actual_false.kerberos_delegation


def test_validate_invalid_auth_method():
    with pytest.raises(WinRMError) as excinfo:
        Transport(auth_method='broken')

    assert str(excinfo.value) == 'requested auth method is broken, but valid auth methods are ' \
                                 'basic kerberos ntlm certificate credssp plaintext ssl'


def test_certificate_use_deprecated_ssl():
    actual = Transport(auth_method='ssl', username='test', password='test')
    assert actual.auth_method == 'basic'


def test_basic_with_no_username_fail():
    with pytest.raises(InvalidCredentialsError) as excinfo:
        Transport(auth_method='basic', password='test')
    assert str(excinfo.value) == 'auth method basic requires a username'


def test_basic_with_no_password_fail():
    with pytest.raises(InvalidCredentialsError) as excinfo:
        Transport(auth_method='basic', username='test')
    assert str(excinfo.value) == 'auth method basic requires a password'


def test_raise_wsman_error_no_content():
    with pytest.raises(WinRMTransportError) as excinfo:
        test_response = Response()
        test_response.status_code = 404
        Transport._raise_wsman_error(test_response)

    exc_message = [excinfo.value.args[1] for x in excinfo.value.args][0]
    assert exc_message == 'Bad HTTP response returned from server. Code 404'


def test_raise_wsman_error_timeout_error():
    with pytest.raises(WinRMOperationTimeoutError) as excinfo:
        test_response = Response()
        test_response.status_code = 500
        test_response._content = """
            <s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope" xmlns:a="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:x="http://schemas.xmlsoap.org/ws/2004/09/transfer" xmlns:e="http://schemas.xmlsoap.org/ws/2004/08/eventing" xmlns:n="http://schemas.xmlsoap.org/ws/2004/09/enumeration" xmlns:w="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd" xmlns:p="http://schemas.microsoft.com/wbem/wsman/1/wsman.xsd" xml:lang="en-US">
                <s:Header>
                    <a:Action>http://schemas.dmtf.org/wbem/wsman/1/wsman/fault</a:Action>
                    <a:MessageID>uuid:9FF29193-13CD-4F91-A7B8-7A8256E34B8C</a:MessageID>
                    <p:ActivityId>16B19080-A221-0000-A4C6-B11621A2D201</p:ActivityId>
                    <a:To>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</a:To>
                    <a:RelatesTo>uuid:11111111-1111-1111-1111-111111111111</a:RelatesTo>
                </s:Header>
                <s:Body>
                    <s:Fault>
                        <s:Code>
                            <s:Value>s:Receiver</s:Value>
                            <s:Subcode>
                                <s:Value>w:TimedOut</s:Value>
                            </s:Subcode>
                        </s:Code>
                        <s:Reason>
                            <s:Text xml:lang="en-US">The WS-Management service cannot complete the operation within the time specified in OperationTimeout.  </s:Text>
                        </s:Reason>
                        <s:Detail>
                            <f:WSManFault xmlns:f="http://schemas.microsoft.com/wbem/wsman/1/wsmanfault" Code="2150858793" Machine="192.168.1.6">
                            <f:Message>The WS-Management service cannot complete the operation within the time specified in OperationTimeout.  </f:Message>
                        </f:WSManFault>
                    </s:Detail>
                </s:Fault>
                </s:Body>
            </s:Envelope>"""
        Transport._raise_wsman_error(test_response)


def test_raise_wsman_error_fault_error():
    with pytest.raises(WinRMTransportError) as excinfo:
        test_response = Response()
        test_response.status_code = 500
        test_response._content = """
            <s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope" xmlns:a="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:x="http://schemas.xmlsoap.org/ws/2004/09/transfer" xmlns:e="http://schemas.xmlsoap.org/ws/2004/08/eventing" xmlns:n="http://schemas.xmlsoap.org/ws/2004/09/enumeration" xmlns:w="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd" xmlns:p="http://schemas.microsoft.com/wbem/wsman/1/wsman.xsd" xml:lang="en-US">
            <s:Header>
                <a:Action>http://schemas.xmlsoap.org/ws/2004/08/addressing/fault</a:Action>
                <a:MessageID>uuid:99AB70AE-B305-4CC8-BCBE-D4EB3DD1F30E</a:MessageID>
                <a:To>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</a:To>
            </s:Header>
            <s:Body>
                <s:Fault>
                    <s:Code>
                        <s:Value>s:Sender</s:Value>
                        <s:Subcode>
                            <s:Value>a:InvalidMessageInformationHeader</s:Value>
                        </s:Subcode>
                    </s:Code>
                    <s:Reason>
                        <s:Text xml:lang="">The WS-Management service cannot process the request. The request contains one or more invalid SOAP headers. </s:Text>
                    </s:Reason>
                    <s:Detail>
                        <f:WSManFault xmlns:f="http://schemas.microsoft.com/wbem/wsman/1/wsmanfault" Code="2150858767" Machine="windows-host">
                        <f:Message>The WS-Management service cannot process the request. The SOAP packet that WS-Management received did not contain a valid Body element. </f:Message>
                    </f:WSManFault>
                </s:Detail>
            </s:Fault>
            </s:Body>
            </s:Envelope>
            """
        Transport._raise_wsman_error(test_response)

    exc_message = [excinfo.value.args[1] for x in excinfo.value.args][0]
    assert exc_message == 'Bad HTTP response returned from server. Code 500: WSMan Code; 2150858767, ' \
                          'Error: The WS-Management service cannot process the request. ' \
                          'The SOAP packet that WS-Management received did not contain a valid Body element.'


def test_raise_wsman_error_fault_error_psrp():
    with pytest.raises(WinRMTransportError) as excinfo:
        test_response = Response()
        test_response.status_code = 500
        test_response._content = """
            <s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope" xmlns:a="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:x="http://schemas.xmlsoap.org/ws/2004/09/transfer" xmlns:e="http://schemas.xmlsoap.org/ws/2004/08/eventing" xmlns:n="http://schemas.xmlsoap.org/ws/2004/09/enumeration" xmlns:w="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd" xmlns:p="http://schemas.microsoft.com/wbem/wsman/1/wsman.xsd" xml:lang="en-US">
            <s:Header>
                <a:Action>http://schemas.dmtf.org/wbem/wsman/1/wsman/fault</a:Action>
                <a:MessageID>uuid:01123A87-8F13-4CCA-9FE8-B3BEDCD20187</a:MessageID>
                <a:To>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</a:To>
                <a:RelatesTo>uuid:8AEBF35E-EA5D-4B30-B29E-4FE3249123D4</a:RelatesTo>
            </s:Header>
            <s:Body>
                <s:Fault>
                    <s:Code>
                        <s:Value>s:Receiver</s:Value>
                        <s:Subcode>
                            <s:Value>w:InternalError</s:Value>
                        </s:Subcode>
                    </s:Code>
                    <s:Reason>
                        <s:Text xml:lang="en-US"/>
                    </s:Reason>
                    <s:Detail>
                        <f:WSManFault xmlns:f="http://schemas.microsoft.com/wbem/wsman/1/wsmanfault" Code="2152992672" Machine="192.168.1.9">
                        <f:Message>
                            <f:ProviderFault provider="microsoft.powershell" path="C:\\Windows\\system32\\pwrshplugin.dll">Element 'creationXml' was not found. Line 1, position 2.\r\n</f:ProviderFault>
                        </f:Message>
                    </f:WSManFault>
                </s:Detail>
            </s:Fault>
            </s:Body>
            </s:Envelope>"""
        Transport._raise_wsman_error(test_response)

    exc_message = [excinfo.value.args[1] for x in excinfo.value.args][0]
    assert exc_message == 'Bad HTTP response returned from server. Code 500: WSMan Code: 2152992672, ' \
                          'Provider: microsoft.powershell, Path: C:\Windows\system32\pwrshplugin.dll, ' \
                          'Error: Element \'creationXml\' was not found. Line 1, position 2.'


def test_raise_wsman_error_unknown_error_valid_xml():
    with pytest.raises(WinRMTransportError) as excinfo:
        test_response = Response()
        test_response.status_code = 500
        test_response._content = '<S>error</S>'
        Transport._raise_wsman_error(test_response)

    exc_message = [excinfo.value.args[1] for x in excinfo.value.args][0]
    assert exc_message == 'Bad HTTP response returned from server. Code 500: Error: Unknown <S>error</S>'


def test_raise_wsman_error_unknown_error_invalid_xml():
    with pytest.raises(WinRMTransportError) as excinfo:
        test_response = Response()
        test_response.status_code = 500
        test_response._content = 'different error content than a WSMan fault'
        Transport._raise_wsman_error(test_response)

    exc_message = [excinfo.value.args[1] for x in excinfo.value.args][0]
    assert exc_message == 'Bad HTTP response returned from server. Code 500: Error: ' \
                          'Unknown different error content than a WSMan fault'
