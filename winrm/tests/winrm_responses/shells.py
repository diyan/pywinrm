OPEN_SHELL_REQUEST = """
<env:Envelope xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
              xmlns:rsp="http://schemas.microsoft.com/wbem/wsman/1/windows/shell" xmlns:p="http://schemas.microsoft.com/wbem/wsman/1/wsman.xsd"
              xmlns:w="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd" xmlns:x="http://schemas.xmlsoap.org/ws/2004/09/transfer"
              xmlns:a="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:b="http://schemas.dmtf.org/wbem/wsman/1/cimbinding.xsd"
              xmlns:env="http://www.w3.org/2003/05/soap-envelope" xmlns:cfg="http://schemas.microsoft.com/wbem/wsman/1/config"
              xmlns:n="http://schemas.xmlsoap.org/ws/2004/09/enumeration">
    <env:Header>
        <w:OperationTimeout>PT20S</w:OperationTimeout>
        <a:To>http://windows-host:5985/wsman</a:To>
        <w:OptionSet>
            <w:Option Name="WINRS_NOPROFILE">FALSE</w:Option>
            <w:Option Name="WINRS_CODEPAGE">437</w:Option>
        </w:OptionSet>
        <w:MaxEnvelopeSize mustUnderstand="true">153600</w:MaxEnvelopeSize>
        <w:ResourceURI mustUnderstand="true">http://schemas.microsoft.com/wbem/wsman/1/windows/shell/cmd</w:ResourceURI>
        <a:Action mustUnderstand="true">http://schemas.xmlsoap.org/ws/2004/09/transfer/Create</a:Action>
        <p:DataLocale mustUnderstand="false" xml:lang="en-US"></p:DataLocale>
        <a:ReplyTo>
            <a:Address mustUnderstand="true">http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</a:Address>
        </a:ReplyTo>
        <a:MessageID>uuid:63acc10b-c16f-44e6-a1f8-45798c58f63d</a:MessageID>
        <w:Locale mustUnderstand="false" xml:lang="en-US"></w:Locale>
    </env:Header>
    <env:Body>
        <rsp:Shell>
            <rsp:InputStreams>stdin</rsp:InputStreams>
            <rsp:OutputStreams>stdout stderr</rsp:OutputStreams>
        </rsp:Shell>
    </env:Body>
</env:Envelope>
"""

OPEN_SHELL_RESPONSE = """
<s:Envelope xml:lang="en-US" xmlns:s="http://www.w3.org/2003/05/soap-envelope" xmlns:a="http://schemas.xmlsoap.org/ws/2004/08/addressing"
            xmlns:x="http://schemas.xmlsoap.org/ws/2004/09/transfer" xmlns:w="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd"
            xmlns:rsp="http://schemas.microsoft.com/wbem/wsman/1/windows/shell" xmlns:p="http://schemas.microsoft.com/wbem/wsman/1/wsman.xsd">
    <s:Header>
        <a:Action>http://schemas.xmlsoap.org/ws/2004/09/transfer/CreateResponse</a:Action>
        <a:MessageID>uuid:BF99E0E5-4604-4FBE-A3F9-3C2251E2655E</a:MessageID>
        <a:To>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</a:To>
        <a:RelatesTo>uuid:63acc10b-c16f-44e6-a1f8-45798c58f63d</a:RelatesTo>
    </s:Header>
    <s:Body>
        <x:ResourceCreated>
            <a:Address>http://windows-host:5985/wsman</a:Address>
            <a:ReferenceParameters>
                <w:ResourceURI>http://schemas.microsoft.com/wbem/wsman/1/windows/shell/cmd</w:ResourceURI>
                <w:SelectorSet>
                    <w:Selector Name="ShellId">5207F2DF-E6CA-4D10-8C7F-5380F01D6FDE</w:Selector>
                </w:SelectorSet>
            </a:ReferenceParameters>
        </x:ResourceCreated>
        <rsp:Shell xmlns:rsp="http://schemas.microsoft.com/wbem/wsman/1/windows/shell">
            <rsp:ShellId>5207F2DF-E6CA-4D10-8C7F-5380F01D6FDE</rsp:ShellId>
            <rsp:ResourceUri>http://schemas.microsoft.com/wbem/wsman/1/windows/shell/cmd</rsp:ResourceUri>
            <rsp:Owner>SERVER-01\\Administrator</rsp:Owner>
            <rsp:ClientIP>192.168.0.1</rsp:ClientIP>
            <rsp:IdleTimeOut>PT7200.000S</rsp:IdleTimeOut>
            <rsp:InputStreams>stdin</rsp:InputStreams>
            <rsp:OutputStreams>stdout stderr</rsp:OutputStreams>
            <rsp:ShellRunTime>P0DT0H0M0S</rsp:ShellRunTime>
            <rsp:ShellInactivity>P0DT0H0M0S</rsp:ShellInactivity>
        </rsp:Shell>
    </s:Body>
</s:Envelope>
"""

CLOSE_SHELL_REQUEST = """
<?xml version="1.0" encoding="utf-8"?>
<env:Envelope xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
              xmlns:rsp="http://schemas.microsoft.com/wbem/wsman/1/windows/shell" xmlns:p="http://schemas.microsoft.com/wbem/wsman/1/wsman.xsd"
              xmlns:w="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd" xmlns:x="http://schemas.xmlsoap.org/ws/2004/09/transfer"
              xmlns:a="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:b="http://schemas.dmtf.org/wbem/wsman/1/cimbinding.xsd"
              xmlns:env="http://www.w3.org/2003/05/soap-envelope" xmlns:cfg="http://schemas.microsoft.com/wbem/wsman/1/config"
              xmlns:n="http://schemas.xmlsoap.org/ws/2004/09/enumeration">
    <env:Header>
        <w:OperationTimeout>PT20S</w:OperationTimeout>
        <a:To>http://windows-host:5985/wsman</a:To>
        <w:SelectorSet>
            <w:Selector Name="ShellId">B5235B70-E451-4378-BFB4-53C1ABACCAD2</w:Selector>
        </w:SelectorSet>
        <w:MaxEnvelopeSize mustUnderstand="true">153600</w:MaxEnvelopeSize>
        <w:ResourceURI mustUnderstand="true">http://schemas.microsoft.com/wbem/wsman/1/windows/shell/cmd</w:ResourceURI>
        <a:Action mustUnderstand="true">http://schemas.xmlsoap.org/ws/2004/09/transfer/Delete</a:Action>
        <p:DataLocale mustUnderstand="false" xml:lang="en-US"></p:DataLocale>
        <a:ReplyTo>
            <a:Address mustUnderstand="true">http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</a:Address>
        </a:ReplyTo>
        <a:MessageID>uuid:5fc69899-bbc7-4179-a7a2-f6bb62fe2860</a:MessageID>
        <w:Locale mustUnderstand="false" xml:lang="en-US"></w:Locale>
    </env:Header>
    <env:Body></env:Body>
</env:Envelope>
"""

CLOSE_SHELL_RESPONSE = """
<s:Envelope xml:lang="en-US" xmlns:s="http://www.w3.org/2003/05/soap-envelope" xmlns:a="http://schemas.xmlsoap.org/ws/2004/08/addressing"
            xmlns:w="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd" xmlns:p="http://schemas.microsoft.com/wbem/wsman/1/wsman.xsd">
    <s:Header>
        <a:Action>http://schemas.xmlsoap.org/ws/2004/09/transfer/DeleteResponse</a:Action>
        <a:MessageID>uuid:C20C16C3-D163-45B4-9821-8A11C4ED1E42</a:MessageID>
        <a:To>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</a:To>
        <a:RelatesTo>uuid:5fc69899-bbc7-4179-a7a2-f6bb62fe2860</a:RelatesTo>
    </s:Header>
    <s:Body></s:Body>
</s:Envelope>
"""

# Status code: 500
CLOSE_SHELL_RESPONSE_ALREADY_CLOSED = """
<s:Envelope xml:lang="en-US" xmlns:s="http://www.w3.org/2003/05/soap-envelope" xmlns:a="http://schemas.xmlsoap.org/ws/2004/08/addressing"
            xmlns:x="http://schemas.xmlsoap.org/ws/2004/09/transfer" xmlns:e="http://schemas.xmlsoap.org/ws/2004/08/eventing"
            xmlns:n="http://schemas.xmlsoap.org/ws/2004/09/enumeration" xmlns:w="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd"
            xmlns:p="http://schemas.microsoft.com/wbem/wsman/1/wsman.xsd">
    <s:Header>
        <a:Action>http://schemas.dmtf.org/wbem/wsman/1/wsman/fault</a:Action>
        <a:MessageID>uuid:C0005351-7407-4B75-BE76-2A80BA45B7BF</a:MessageID>
        <a:To>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</a:To>
        <a:RelatesTo>uuid:fe945306-d7ce-4126-b168-c704bad7588c</a:RelatesTo>
    </s:Header>
    <s:Body>
        <s:Fault>
            <s:Code>
                <s:Value>s:Sender</s:Value>
                <s:Subcode>
                    <s:Value>w:InvalidSelectors</s:Value>
                </s:Subcode>
            </s:Code>
            <s:Reason>
                <s:Text xml:lang="en-US">The WS-Management service cannot process the request because the request contained invalid selectors for the
                    resource.
                </s:Text>
            </s:Reason>
            <s:Detail>
                <w:FaultDetail>http://schemas.dmtf.org/wbem/wsman/1/wsman/faultDetail/UnexpectedSelectors</w:FaultDetail>
                <f:WSManFault xmlns:f="http://schemas.microsoft.com/wbem/wsman/1/wsmanfault" Code="2150858843" Machine="windows-host">
                    <f:Message>The request for the Windows Remote Shell with ShellId B387C9DF-58ED-4E97-AE80-4117D8D12116 failed because the shell was not found
                        on the server. Possible causes are: the specified ShellId is incorrect or the shell no longer exists on the server. Provide the correct
                        ShellId or create a new shell and retry the operation.
                    </f:Message>
                </f:WSManFault>
            </s:Detail>
        </s:Fault>
    </s:Body>
</s:Envelope>
"""
