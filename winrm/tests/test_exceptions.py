import pytest

from winrm.exceptions import (
    WinRMOperationTimeoutError,
    WinRMTransportError,
    WSManFaultError,
)


def raise_exc(exc: Exception) -> None:
    raise exc


def test_wsman_fault_must_understand(protocol_fake):
    xml_text = r"""<s:Envelope xml:lang="en-US"
    xmlns:s="http://www.w3.org/2003/05/soap-envelope"
    xmlns:a="http://schemas.xmlsoap.org/ws/2004/08/addressing"
    xmlns:x="http://schemas.xmlsoap.org/ws/2004/09/transfer"
    xmlns:e="http://schemas.xmlsoap.org/ws/2004/08/eventing"
    xmlns:n="http://schemas.xmlsoap.org/ws/2004/09/enumeration"
    xmlns:w="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd"
    xmlns:rsp="http://schemas.microsoft.com/wbem/wsman/1/windows/shell"
    xmlns:p="http://schemas.microsoft.com/wbem/wsman/1/wsman.xsd">
    <s:Header>
        <a:Action>http://schemas.xmlsoap.org/ws/2004/08/addressing/fault</a:Action>
        <a:MessageID>uuid:4DB571F9-F8DE-48FD-872C-2AF08D996249</a:MessageID>
        <a:To>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</a:To>
        <a:RelatesTo>uuid:eaa98952-3188-458f-b265-b03ace115f20</a:RelatesTo>
        <s:NotUnderstood qname="wsman:ResourceUri"
            xmlns:wsman="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd" />
    </s:Header>
    <s:Body>
        <s:Fault>
            <s:Code>
                <s:Value>s:MustUnderstand</s:Value>
            </s:Code>
            <s:Reason>
                <s:Text xml:lang=""> Test reason. </s:Text>
            </s:Reason>
        </s:Fault>
    </s:Body>
</s:Envelope>"""

    protocol_fake.transport.send_message = lambda m: raise_exc(WinRMTransportError("http", 500, xml_text))

    with pytest.raises(WSManFaultError, match="Test reason\\.") as exc:
        protocol_fake.open_shell()

    assert isinstance(exc.value, WSManFaultError)
    assert exc.value.code == 500
    assert exc.value.response == xml_text
    assert exc.value.fault_code == "s:MustUnderstand"
    assert exc.value.fault_subcode is None
    assert exc.value.wsman_fault_code is None
    assert exc.value.wmierror_code is None


def test_wsman_fault_no_reason(protocol_fake):
    xml_text = r"""<s:Envelope xml:lang="en-US"
    xmlns:s="http://www.w3.org/2003/05/soap-envelope"
    xmlns:a="http://schemas.xmlsoap.org/ws/2004/08/addressing"
    xmlns:x="http://schemas.xmlsoap.org/ws/2004/09/transfer"
    xmlns:e="http://schemas.xmlsoap.org/ws/2004/08/eventing"
    xmlns:n="http://schemas.xmlsoap.org/ws/2004/09/enumeration"
    xmlns:w="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd"
    xmlns:rsp="http://schemas.microsoft.com/wbem/wsman/1/windows/shell"
    xmlns:p="http://schemas.microsoft.com/wbem/wsman/1/wsman.xsd">
    <s:Header>
        <a:Action>http://schemas.xmlsoap.org/ws/2004/08/addressing/fault</a:Action>
        <a:MessageID>uuid:4DB571F9-F8DE-48FD-872C-2AF08D996249</a:MessageID>
        <a:To>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</a:To>
        <a:RelatesTo>uuid:eaa98952-3188-458f-b265-b03ace115f20</a:RelatesTo>
        <s:NotUnderstood qname="wsman:ResourceUri"
            xmlns:wsman="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd" />
    </s:Header>
    <s:Body>
        <s:Fault>
            <s:Code>
                <s:Value>s:Unknown</s:Value>
            </s:Code>
        </s:Fault>
    </s:Body>
</s:Envelope>"""

    protocol_fake.transport.send_message = lambda m: raise_exc(WinRMTransportError("http", 501, xml_text))

    with pytest.raises(WSManFaultError, match="no error message in fault") as exc:
        protocol_fake.open_shell()

    assert isinstance(exc.value, WSManFaultError)
    assert exc.value.code == 501
    assert exc.value.response == xml_text
    assert exc.value.fault_code == "s:Unknown"
    assert exc.value.fault_subcode is None
    assert exc.value.wsman_fault_code is None
    assert exc.value.wmierror_code is None


def test_wsman_fault_known_fault(protocol_fake):
    xml_text = r"""<s:Envelope xml:lang="en-US"
    xmlns:s="http://www.w3.org/2003/05/soap-envelope"
    xmlns:a="http://schemas.xmlsoap.org/ws/2004/08/addressing"
    xmlns:x="http://schemas.xmlsoap.org/ws/2004/09/transfer"
    xmlns:e="http://schemas.xmlsoap.org/ws/2004/08/eventing"
    xmlns:n="http://schemas.xmlsoap.org/ws/2004/09/enumeration"
    xmlns:w="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd"
    xmlns:p="http://schemas.microsoft.com/wbem/wsman/1/wsman.xsd">
    <s:Header>
        <a:Action>http://schemas.dmtf.org/wbem/wsman/1/wsman/fault</a:Action>
        <a:MessageID>uuid:D7C4A9B1-9A18-4048-B346-248D62A6078D</a:MessageID>
        <a:To>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</a:To>
        <a:RelatesTo>uuid:7340FE92-C302-42E5-A337-1918908654F8</a:RelatesTo>
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
                <f:WSManFault
                    xmlns:f="http://schemas.microsoft.com/wbem/wsman/1/wsmanfault" Code="2150858793" Machine="server2022.domain.test">
                    <f:Message>The WS-Management service cannot complete the operation within the time specified in OperationTimeout.  </f:Message>
                </f:WSManFault>
            </s:Detail>
        </s:Fault>
    </s:Body>
</s:Envelope>"""

    protocol_fake.transport.send_message = lambda m: raise_exc(WinRMTransportError("http", 500, xml_text))

    with pytest.raises(WinRMOperationTimeoutError):
        protocol_fake.open_shell()


def test_wsman_fault_with_wsmanfault(protocol_fake):
    xml_text = r"""<s:Envelope xml:lang="en-US"
    xmlns:s="http://www.w3.org/2003/05/soap-envelope"
    xmlns:a="http://schemas.xmlsoap.org/ws/2004/08/addressing"
    xmlns:x="http://schemas.xmlsoap.org/ws/2004/09/transfer"
    xmlns:e="http://schemas.xmlsoap.org/ws/2004/08/eventing"
    xmlns:n="http://schemas.xmlsoap.org/ws/2004/09/enumeration"
    xmlns:w="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd"
    xmlns:p="http://schemas.microsoft.com/wbem/wsman/1/wsman.xsd">
    <s:Header>
        <a:Action>http://schemas.dmtf.org/wbem/wsman/1/wsman/fault</a:Action>
        <a:MessageID>uuid:EE71C444-1658-4B3F-916D-54CE43B68BC9</a:MessageID>
        <a:To>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</a:To>
        <a:RelatesTo>uuid.761ca906-0bf0-41bb-a9d9-4cbbca986aeb</a:RelatesTo>
    </s:Header>
    <s:Body>
        <s:Fault>
            <s:Code>
                <s:Value>s:Sender</s:Value>
                <s:Subcode>
                    <s:Value>w:SchemaValidationError</s:Value>
                </s:Subcode>
            </s:Code>
            <s:Reason>
                <s:Text xml:lang="">Reason text.</s:Text>
            </s:Reason>
            <s:Detail>
                <f:WSManFault
                    xmlns:f="http://schemas.microsoft.com/wbem/wsman/1/wsmanfault" Code="2150858817" Machine="SERVER2008.domain.local">
                    <f:Message>Detail message.</f:Message>
                </f:WSManFault>
            </s:Detail>
        </s:Fault>
    </s:Body>
</s:Envelope>"""

    protocol_fake.transport.send_message = lambda m: raise_exc(WinRMTransportError("http", 500, xml_text))

    with pytest.raises(WSManFaultError, match="Reason text\\.") as exc:
        protocol_fake.open_shell()

    assert isinstance(exc.value, WSManFaultError)
    assert exc.value.code == 500
    assert exc.value.response == xml_text
    assert exc.value.fault_code == "s:Sender"
    assert exc.value.fault_subcode == "w:SchemaValidationError"
    assert exc.value.wsman_fault_code == 0x80338041
    assert exc.value.wmierror_code is None


def test_wsman_fault_wmi_error_detail(protocol_fake):
    xml_text = r"""<s:Envelope xml:lang="en-US"
    xmlns:s="http://www.w3.org/2003/05/soap-envelope"
    xmlns:a="http://schemas.xmlsoap.org/ws/2004/08/addressing"
    xmlns:x="http://schemas.xmlsoap.org/ws/2004/09/transfer"
    xmlns:e="http://schemas.xmlsoap.org/ws/2004/08/eventing"
    xmlns:n="http://schemas.xmlsoap.org/ws/2004/09/enumeration"
    xmlns:w="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd"
    xmlns:p="http://schemas.microsoft.com/wbem/wsman/1/wsman.xsd">
    <s:Header>
        <a:Action>http://schemas.dmtf.org/wbem/wsman/1/wsman/fault</a:Action>
        <a:MessageID>uuid:A832545B-9F5C-46AA-BB6A-5E4270D5E530</a:MessageID>
        <a:To>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</a:To>
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
                <s:Text xml:lang="en-US">Reason text. </s:Text>
            </s:Reason>
            <s:Detail>
                <p:MSFT_WmiError b:IsCIM_Error="true"
                    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                    xmlns:b="http://schemas.dmtf.org/wbem/wsman/1/cimbinding.xsd"
                    xmlns:p="http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/MSFT_WmiError"
                    xmlns:cim="http://schemas.dmtf.org/wbem/wscim/1/common" xsi:type="p:MSFT_WmiError_Type">
                    <p:CIMStatusCode xsi:type="cim:cimUnsignedInt">27</p:CIMStatusCode>
                    <p:CIMStatusCodeDescription xsi:type="cim:cimString" xsi:nil="true" />
                    <p:ErrorSource xsi:type="cim:cimString" xsi:nil="true" />
                    <p:ErrorSourceFormat xsi:type="cim:cimUnsignedShort">0</p:ErrorSourceFormat>
                    <p:ErrorType xsi:type="cim:cimUnsignedShort">0</p:ErrorType>
                    <p:Message xsi:type="cim:cimString">WMI Message. </p:Message>
                    <p:MessageID xsi:type="cim:cimString">HRESULT 0x803381a6</p:MessageID>
                    <p:OtherErrorSourceFormat xsi:type="cim:cimString" xsi:nil="true" />
                    <p:OtherErrorType xsi:type="cim:cimString" xsi:nil="true" />
                    <p:OwningEntity xsi:type="cim:cimString" xsi:nil="true" />
                    <p:PerceivedSeverity xsi:type="cim:cimUnsignedShort">0</p:PerceivedSeverity>
                    <p:ProbableCause xsi:type="cim:cimUnsignedShort">0</p:ProbableCause>
                    <p:ProbableCauseDescription xsi:type="cim:cimString" xsi:nil="true" />
                    <p:error_Category xsi:type="cim:cimUnsignedInt">30</p:error_Category>
                    <p:error_Code xsi:type="cim:cimUnsignedInt">2150859174</p:error_Code>
                    <p:error_Type xsi:type="cim:cimString">HRESULT</p:error_Type>
                    <p:error_WindowsErrorMessage xsi:type="cim:cimString">Windows Error message. </p:error_WindowsErrorMessage>
                </p:MSFT_WmiError>
            </s:Detail>
        </s:Fault>
    </s:Body>
</s:Envelope>"""

    protocol_fake.transport.send_message = lambda m: raise_exc(WinRMTransportError("http", 500, xml_text))

    with pytest.raises(WSManFaultError, match="Reason text\\.") as exc:
        protocol_fake.open_shell()

    assert isinstance(exc.value, WSManFaultError)
    assert exc.value.code == 500
    assert exc.value.response == xml_text
    assert exc.value.fault_code == "s:Receiver"
    assert exc.value.fault_subcode == "w:InternalError"
    assert exc.value.wsman_fault_code is None
    assert exc.value.wmierror_code == 0x803381A6
