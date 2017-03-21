import xmltodict

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from tests.conftest import xml_str_compare
from winrm.wsmv.message_objects import WsmvObject


def test_command_line_without_id():
    expected = """
        <rsp:CommandLine>
            <rsp:Command>ipconfig</rsp:Command>
            <rsp:Arguments>/all</rsp:Arguments>
        </rsp:CommandLine>"""
    actual = xmltodict.unparse(WsmvObject.command_line('ipconfig', ['/all']), pretty=True, full_document=False)

    assert xml_str_compare(expected, actual)


def test_command_line_with_id():
    expected = """
        <rsp:CommandLine CommandId="1111-1111">
            <rsp:Arguments>/r</rsp:Arguments>
            <rsp:Arguments>/f</rsp:Arguments>
            <rsp:Command>test</rsp:Command>
        </rsp:CommandLine>"""
    actual = xmltodict.unparse(WsmvObject.command_line('test', ['/r', '/f'], '1111-1111'), pretty=True, full_document=False)

    assert xml_str_compare(expected, actual)


def test_receive_without_id():
    expected = """
        <rsp:Receive>
            <rsp:DesiredStream>stdout</rsp:DesiredStream>
        </rsp:Receive>"""
    actual = xmltodict.unparse(WsmvObject.receive('stdout'), pretty=True, full_document=False)

    assert xml_str_compare(expected, actual)


def test_receive_with_id():
    expected = """
        <rsp:Receive>
            <rsp:DesiredStream CommandId="1111-1111">pr</rsp:DesiredStream>
        </rsp:Receive>"""
    actual = xmltodict.unparse(WsmvObject.receive('pr', '1111-1111'), pretty=True, full_document=False)

    assert xml_str_compare(expected, actual)


def test_send_not_end():
    expected = """
        <rsp:Send>
            <rsp:Stream Name="stdin" CommandId="1111-1111">stream</rsp:Stream>
        </rsp:Send>"""
    actual = xmltodict.unparse(WsmvObject.send('stdin', '1111-1111', 'stream'), pretty=True, full_document=False)

    assert xml_str_compare(expected, actual)


def test_send_at_end():
    expected = """
        <rsp:Send>
            <rsp:Stream Name="pr" CommandId="1111-1111" End="true">AADD==</rsp:Stream>
        </rsp:Send>"""
    actual = xmltodict.unparse(WsmvObject.send('pr', '1111-1111', 'AADD==', True), pretty=True, full_document=False)

    assert xml_str_compare(expected, actual)


def test_shell_with_basics():
    expected = """
        <rsp:Shell>
            <rsp:InputStreams>stdin</rsp:InputStreams>
            <rsp:OutputStreams>stdout stderr</rsp:OutputStreams>
        </rsp:Shell>"""
    actual = xmltodict.unparse(WsmvObject.shell(), pretty=True, full_document=False)

    assert xml_str_compare(expected, actual)


def test_with_full_opts():
    expected = """
        <rsp:Shell ShellId="1111-1111">
            <rsp:InputStreams>stdin pr</rsp:InputStreams>
            <rsp:OutputStreams>stdout pr</rsp:OutputStreams>
            <rsp:Environment>
                <rsp:Variable Name="key1">value1</rsp:Variable>
            </rsp:Environment>
            <rsp:WorkingDirectory>D:\\test</rsp:WorkingDirectory>
            <rsp:Lifetime>P2WT7H55M53S</rsp:Lifetime>
            <rsp:IdleTimeOut>P6DT12H4M25S</rsp:IdleTimeOut>
        </rsp:Shell>"""
    actual = xmltodict.unparse(WsmvObject.shell(shell_id='1111-1111',
                                                environment={"key1": "value1"},
                                                working_directory='D:\\test',
                                                lifetime='1238153',
                                                idle_time_out='561865',
                                                input_streams='stdin pr',
                                                output_streams='stdout pr'), pretty=True, full_document=False)

    assert xml_str_compare(expected, actual)


def test_shell_with_multiple_environment_args():
    expected = """
        <rsp:Shell>
            <rsp:InputStreams>stdin</rsp:InputStreams>
            <rsp:OutputStreams>stdout stderr</rsp:OutputStreams>
            <rsp:Environment>
                <rsp:Variable Name="key1">value1</rsp:Variable>
                <rsp:Variable Name="key2">value2</rsp:Variable>
            </rsp:Environment>
        </rsp:Shell>"""
    actual = xmltodict.unparse(WsmvObject.shell(
        environment=OrderedDict([("key1", "value1"), ("key2", "value2")])
    ), pretty=True, full_document=False)

    assert xml_str_compare(expected, actual)


def test_shell_with_open_content():
    expected = """
        <rsp:Shell>
            <rsp:InputStreams>stdin</rsp:InputStreams>
            <rsp:OutputStreams>stdout stderr</rsp:OutputStreams>
            <creationXml xmlns="http://schemas.microsoft.com/powershell">test</creationXml>
        </rsp:Shell>"""
    actual = xmltodict.unparse(WsmvObject.shell(
        open_content={'creationXml': {'@xmlns': 'http://schemas.microsoft.com/powershell', '#text': 'test'}}
    ), pretty=True, full_document=False)

    assert xml_str_compare(expected, actual)


def test_signal_without_id():
    expected = """
        <rsp:Signal>
            <rsp:Code>stop</rsp:Code>
        </rsp:Signal>"""
    actual = xmltodict.unparse(WsmvObject.signal('stop'), pretty=True, full_document=False)

    assert xml_str_compare(expected, actual)


def test_signal_with_id():
    expected = """
        <rsp:Signal CommandId="1111-1111">
            <rsp:Code>stop</rsp:Code>
        </rsp:Signal>"""
    actual = xmltodict.unparse(WsmvObject.signal('stop', '1111-1111'), pretty=True, full_document=False)

    assert xml_str_compare(expected, actual)
