import mock
import pytest
import uuid
import xmltodict

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from tests.conftest import xml_str_compare
from winrm.contants import PsrpMessageType
from winrm.exceptions import WinRMError
from winrm.psrp.message_objects import Message, PsrpObject, PrimitiveMessage, \
    SessionCapability, InitRunspacePool, RunspacePoolState, CreatePipeline, \
    ApplicationPrivateData, PipelineState, PipelineHostResponse, PipelineInput, \
    EndOfPipelineInput


def mock_uuid():
    return uuid.UUID('11111111-1111-1111-1111-111111111111')


def test_create_message():
    expected = b'\x01\x00\x00\x00\x02\x00\x01\x00' \
               b'\x11\x11\x11\x11\x11\x11\x11\x11' \
               b'\x11\x11\x11\x11\x11\x11\x11\x11' \
               b'\x11\x11\x11\x11\x11\x11\x11\x11' \
               b'\x11\x11\x11\x11\x11\x11\x11\x11' \
               b'\xef\xbb\xbf<S>A</S>'
    actual = Message(Message.DESTINATION_CLIENT, mock_uuid(), mock_uuid(),
                     PrimitiveMessage(PsrpMessageType.SESSION_CAPABILITY, {"S": "A"}))
    assert actual.create_message() == expected


def test_create_message_no_data():
    expected = b'\x01\x00\x00\x00\x03\x10\x04\x00' \
               b'\x11\x11\x11\x11\x11\x11\x11\x11' \
               b'\x11\x11\x11\x11\x11\x11\x11\x11' \
               b'\x11\x11\x11\x11\x11\x11\x11\x11' \
               b'\x11\x11\x11\x11\x11\x11\x11\x11'
    actual = Message(Message.DESTINATION_CLIENT, mock_uuid(), mock_uuid(),
                     PrimitiveMessage(PsrpMessageType.END_OF_PIPELINE_INPUT, ""))
    a = actual.create_message()
    assert actual.create_message() == expected


def test_parse_message():
    test_message = b'\x01\x00\x00\x00\x02\x00\x01\x00' \
                   b'\x11\x11\x11\x11\x11\x11\x11\x11' \
                   b'\x11\x11\x11\x11\x11\x11\x11\x11' \
                   b'\x11\x11\x11\x11\x11\x11\x11\x11' \
                   b'\x11\x11\x11\x11\x11\x11\x11\x11' \
                   b'\xef\xbb\xbf<S>A</S>'
    actual = Message.parse_message(test_message)

    assert actual.destination == Message.DESTINATION_CLIENT
    assert actual.message_type == PsrpMessageType.SESSION_CAPABILITY
    assert actual.rpid == mock_uuid()
    assert actual.pid == mock_uuid()
    assert actual.data == {"S": "A"}


@mock.patch('uuid.uuid4', side_effect=mock_uuid)
def test_create_coordinate(mock_uuid):
    expected = """
        <Obj N="Value" RefId="286331153">
            <MS>
                <S N="T">System.Management.Automation.Host.Coordinates</S>
                <Obj N="V" RefId="286331153">
                    <MS>
                        <I32 N="x">1</I32>
                        <I32 N="y">2</I32>
                    </MS>
                </Obj>
            </MS>
        </Obj>"""
    actual = xmltodict.unparse(PsrpObject.create_coordinate("1", "2"), pretty=True, full_document=False)
    assert xml_str_compare(actual, expected)


@mock.patch('uuid.uuid4', side_effect=mock_uuid)
def test_create_size(mock_uuid):
    expected = """
        <Obj N="Value" RefId="286331153">
            <MS>
                <S N="T">System.Management.Automation.Host.Size</S>
                <Obj N="V" RefId="286331153">
                    <MS>
                        <I32 N="width">1</I32>
                        <I32 N="height">2</I32>
                    </MS>
                </Obj>
            </MS>
        </Obj>"""
    actual = xmltodict.unparse(PsrpObject.create_size("1", "2"), pretty=True, full_document=False)
    assert xml_str_compare(actual, expected)


@mock.patch('uuid.uuid4', side_effect=mock_uuid)
def test_create_color(mock_uuid):
    expected = """
        <Obj N="Value" RefId="286331153">
            <MS>
                <S N="T">System.ConsoleColor</S>
                <I32 N="V">1</I32>
            </MS>
        </Obj>"""
    actual = xmltodict.unparse(PsrpObject.create_color("1"), pretty=True, full_document=False)
    assert xml_str_compare(actual, expected)


@mock.patch('uuid.uuid4', side_effect=mock_uuid)
def test_create_ps_thread_option(mock_uuid):
    expected = """
        <Obj N="PSThreadOptions" RefId="286331153">
            <TN RefId="286331153">
                <T>System.Management.Automation.Runspaces.PSThreadOptions</T>
                <T>System.Enum</T>
                <T>System.ValueType</T>
                <T>System.Object</T>
            </TN>
            <ToString>Default</ToString>
            <I32>0</I32>
        </Obj>"""
    actual = xmltodict.unparse(PsrpObject.create_ps_thread_option(), pretty=True, full_document=False)
    assert xml_str_compare(actual, expected)


@mock.patch('uuid.uuid4', side_effect=mock_uuid)
def test_create_apartment_state(mock_uuid):
    expected = """
        <Obj N="ApartmentState" RefId="286331153">
            <TN RefId="286331153">
                <T>System.Threading.ApartmentState</T>
                <T>System.Enum</T>
                <T>System.ValueType</T>
                <T>System.Object</T>
            </TN>
            <ToString>Unknown</ToString>
            <I32>2</I32>
        </Obj>"""
    actual = xmltodict.unparse(PsrpObject.create_apartment_state(), pretty=True, full_document=False)
    assert xml_str_compare(actual, expected)


@mock.patch('uuid.uuid4', side_effect=mock_uuid)
def test_create_remote_stream_options(mock_uuid):
    expected = """
        <Obj N="RemoteStreamOptions" RefId="286331153">
            <TN RefId="286331153">
                <T>System.Management.Automation.RemoteStreamOptions</T>
                <T>System.Enum</T>
                <T>System.ValueType</T>
                <T>System.Object</T>
            </TN>
            <ToString>0</ToString>
            <I32>0</I32>
        </Obj>"""
    actual = xmltodict.unparse(PsrpObject.create_remote_stream_options(), pretty=True, full_document=False)
    assert xml_str_compare(actual, expected)


@mock.patch('uuid.uuid4', side_effect=mock_uuid)
def test_create_pipeline(mock_uuid):
    expected = """
        <Obj N="PowerShell" RefId="286331153">
            <MS>
                <Obj N="Cmds" RefId="286331153">
                    <TN RefId="286331153">
                        <T>System.Collections.Generic.List`1[[System.Management.Automation.PSObject, System.Management.Automation, Version=3.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35]]</T>
                        <T>System.Object</T>
                    </TN>
                    <LST>
                        <Obj>A</Obj>
                        <Obj>B</Obj>
                    </LST>
                </Obj>
                <B N="IsNested">false</B>
                <B N="RedirectShellErrorOutputPipe">true</B>
                <Nil N="History"></Nil>
            </MS>
        </Obj>"""
    actual = xmltodict.unparse(PsrpObject.create_pipeline([{"Obj": "A"}, {"Obj": "B"}]), pretty=True, full_document=False)
    assert xml_str_compare(actual, expected)


@mock.patch('uuid.uuid4', side_effect=mock_uuid)
def test_create_command_no_parameters(mock_uuid):
    expected = """
        <Obj RefId="286331153">
            <MS>
                <S N="Cmd">New-Item</S>
                <B N="IsScript">true</B>
                <Nil N="UseLocalScope"></Nil>
                <Obj N="MergeMyResult" RefId="286331153">
                    <TN RefId="286331153">
                        <T>System.Management.Automation.Runspaces.PipelineResultTypes</T>
                        <T>System.Enum</T>
                        <T>System.ValueType</T>
                        <T>System.Object</T>
                    </TN>
                    <ToString>None</ToString>
                    <I32>0</I32>
                </Obj>
                <Obj N="MergeToResult" RefId="286331153">
                    <TNRef RefId="286331153"></TNRef>
                    <ToString>None</ToString>
                    <I32>0</I32>
                </Obj>
                <Obj N="MergePreviousResults" RefId="286331153">
                    <TNRef RefId="286331153"></TNRef>
                    <ToString>None</ToString>
                    <I32>0</I32>
                </Obj>
                <Obj N="MergeError" RefId="286331153">
                    <TNRef RefId="286331153"></TNRef>
                    <ToString>None</ToString>
                    <I32>0</I32>
                </Obj>
                <Obj N="MergeWarning" RefId="286331153">
                    <TNRef RefId="286331153"></TNRef>
                    <ToString>None</ToString>
                    <I32>0</I32>
                </Obj>
                <Obj N="MergeVerbose" RefId="286331153">
                    <TNRef RefId="286331153"></TNRef>
                    <ToString>None</ToString>
                    <I32>0</I32>
                </Obj>
                <Obj N="MergeDebug" RefId="286331153">
                    <TNRef RefId="286331153"></TNRef>
                    <ToString>None</ToString>
                    <I32>0</I32>
                </Obj>
                <Obj N="Args" RefId="286331153">
                    <TN RefId="286331153">
                        <T>System.Collections.Generic.List`1[[System.Management.Automation.PSObject, System.Management.Automation, Version=3.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35]]</T>
                        <T>System.Object</T>
                    </TN>
                    <LST></LST>
                </Obj>
            </MS>
        </Obj>"""
    actual = xmltodict.unparse(PsrpObject.create_command('New-Item'), pretty=True, full_document=False)
    assert xml_str_compare(actual, expected)


@mock.patch('uuid.uuid4', side_effect=mock_uuid)
def test_create_command_with_one_parameter(mock_uuid):
    expected = """
        <Obj RefId="286331153">
            <MS>
                <S N="Cmd">New-Item</S>
                <B N="IsScript">false</B>
                <Nil N="UseLocalScope"></Nil>
                <Obj N="MergeMyResult" RefId="286331153">
                    <TN RefId="286331153">
                        <T>System.Management.Automation.Runspaces.PipelineResultTypes</T>
                        <T>System.Enum</T>
                        <T>System.ValueType</T>
                        <T>System.Object</T>
                    </TN>
                    <ToString>None</ToString>
                    <I32>0</I32>
                </Obj>
                <Obj N="MergeToResult" RefId="286331153">
                    <TNRef RefId="286331153"></TNRef>
                    <ToString>None</ToString>
                    <I32>0</I32>
                </Obj>
                <Obj N="MergePreviousResults" RefId="286331153">
                    <TNRef RefId="286331153"></TNRef>
                    <ToString>None</ToString>
                    <I32>0</I32>
                </Obj>
                <Obj N="MergeError" RefId="286331153">
                    <TNRef RefId="286331153"></TNRef>
                    <ToString>None</ToString>
                    <I32>0</I32>
                </Obj>
                <Obj N="MergeWarning" RefId="286331153">
                    <TNRef RefId="286331153"></TNRef>
                    <ToString>None</ToString>
                    <I32>0</I32>
                </Obj>
                <Obj N="MergeVerbose" RefId="286331153">
                    <TNRef RefId="286331153"></TNRef>
                    <ToString>None</ToString>
                    <I32>0</I32>
                </Obj>
                <Obj N="MergeDebug" RefId="286331153">
                    <TNRef RefId="286331153"></TNRef>
                    <ToString>None</ToString>
                    <I32>0</I32>
                </Obj>
                <Obj N="Args" RefId="286331153">
                    <TN RefId="286331153">
                        <T>System.Collections.Generic.List`1[[System.Management.Automation.PSObject, System.Management.Automation, Version=3.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35]]</T>
                        <T>System.Object</T>
                    </TN>
                    <LST>
                        <Obj RefId="286331153">
                            <MS>
                                <S N="N">-Path</S>
                                <Nil N="V"></Nil>
                            </MS>
                        </Obj>
                        <Obj RefId="286331153">
                            <MS>
                                <Nil N="N"></Nil>
                                <S N="V">test</S>
                            </MS>
                        </Obj>
                    </LST>
                </Obj>
            </MS>
        </Obj>"""
    actual = xmltodict.unparse(PsrpObject.create_command('New-Item', ['-Path test']), pretty=True, full_document=False)
    assert xml_str_compare(actual, expected)


@mock.patch('uuid.uuid4', side_effect=mock_uuid)
def test_create_command_with_one_parameter_no_key(mock_uuid):
    expected = """
        <Obj RefId="286331153">
            <MS>
                <S N="Cmd">New-Item</S>
                <B N="IsScript">false</B>
                <Nil N="UseLocalScope"></Nil>
                <Obj N="MergeMyResult" RefId="286331153">
                    <TN RefId="286331153">
                        <T>System.Management.Automation.Runspaces.PipelineResultTypes</T>
                        <T>System.Enum</T>
                        <T>System.ValueType</T>
                        <T>System.Object</T>
                    </TN>
                    <ToString>None</ToString>
                    <I32>0</I32>
                </Obj>
                <Obj N="MergeToResult" RefId="286331153">
                    <TNRef RefId="286331153"></TNRef>
                    <ToString>None</ToString>
                    <I32>0</I32>
                </Obj>
                <Obj N="MergePreviousResults" RefId="286331153">
                    <TNRef RefId="286331153"></TNRef>
                    <ToString>None</ToString>
                    <I32>0</I32>
                </Obj>
                <Obj N="MergeError" RefId="286331153">
                    <TNRef RefId="286331153"></TNRef>
                    <ToString>None</ToString>
                    <I32>0</I32>
                </Obj>
                <Obj N="MergeWarning" RefId="286331153">
                    <TNRef RefId="286331153"></TNRef>
                    <ToString>None</ToString>
                    <I32>0</I32>
                </Obj>
                <Obj N="MergeVerbose" RefId="286331153">
                    <TNRef RefId="286331153"></TNRef>
                    <ToString>None</ToString>
                    <I32>0</I32>
                </Obj>
                <Obj N="MergeDebug" RefId="286331153">
                    <TNRef RefId="286331153"></TNRef>
                    <ToString>None</ToString>
                    <I32>0</I32>
                </Obj>
                <Obj N="Args" RefId="286331153">
                    <TN RefId="286331153">
                        <T>System.Collections.Generic.List`1[[System.Management.Automation.PSObject, System.Management.Automation, Version=3.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35]]</T>
                        <T>System.Object</T>
                    </TN>
                    <LST>
                        <Obj RefId="286331153">
                            <MS>
                                <Nil N="N"></Nil>
                                <S N="V">test</S>
                            </MS>
                        </Obj>
                    </LST>
                </Obj>
            </MS>
        </Obj>"""
    actual = xmltodict.unparse(PsrpObject.create_command('New-Item', ['test']), pretty=True, full_document=False)
    assert xml_str_compare(actual, expected)


@mock.patch('uuid.uuid4', side_effect=mock_uuid)
def test_create_command_with_two_parameters(mock_uuid):
    expected = """
        <Obj RefId="286331153">
            <MS>
                <S N="Cmd">New-Item</S>
                <B N="IsScript">false</B>
                <Nil N="UseLocalScope"></Nil>
                <Obj N="MergeMyResult" RefId="286331153">
                    <TN RefId="286331153">
                        <T>System.Management.Automation.Runspaces.PipelineResultTypes</T>
                        <T>System.Enum</T>
                        <T>System.ValueType</T>
                        <T>System.Object</T>
                    </TN>
                    <ToString>None</ToString>
                    <I32>0</I32>
                </Obj>
                <Obj N="MergeToResult" RefId="286331153">
                    <TNRef RefId="286331153"></TNRef>
                    <ToString>None</ToString>
                    <I32>0</I32>
                </Obj>
                <Obj N="MergePreviousResults" RefId="286331153">
                    <TNRef RefId="286331153"></TNRef>
                    <ToString>None</ToString>
                    <I32>0</I32>
                </Obj>
                <Obj N="MergeError" RefId="286331153">
                    <TNRef RefId="286331153"></TNRef>
                    <ToString>None</ToString>
                    <I32>0</I32>
                </Obj>
                <Obj N="MergeWarning" RefId="286331153">
                    <TNRef RefId="286331153"></TNRef>
                    <ToString>None</ToString>
                    <I32>0</I32>
                </Obj>
                <Obj N="MergeVerbose" RefId="286331153">
                    <TNRef RefId="286331153"></TNRef>
                    <ToString>None</ToString>
                    <I32>0</I32>
                </Obj>
                <Obj N="MergeDebug" RefId="286331153">
                    <TNRef RefId="286331153"></TNRef>
                    <ToString>None</ToString>
                    <I32>0</I32>
                </Obj>
                <Obj N="Args" RefId="286331153">
                    <TN RefId="286331153">
                        <T>System.Collections.Generic.List`1[[System.Management.Automation.PSObject, System.Management.Automation, Version=3.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35]]</T>
                        <T>System.Object</T>
                    </TN>
                    <LST>
                        <Obj RefId="286331153">
                            <MS>
                                <S N="N">-Path</S>
                                <Nil N="V"></Nil>
                            </MS>
                        </Obj>
                        <Obj RefId="286331153">
                            <MS>
                                <Nil N="N"></Nil>
                                <S N="V">test</S>
                            </MS>
                        </Obj>
                        <Obj RefId="286331153">
                            <MS>
                                <S N="N">-Type</S>
                                <Nil N="V"></Nil>
                            </MS>
                        </Obj>
                        <Obj RefId="286331153">
                            <MS>
                                <Nil N="N"></Nil>
                                <S N="V">file</S>
                            </MS>
                        </Obj>
                    </LST>
                </Obj>
            </MS>
        </Obj>"""
    actual = xmltodict.unparse(PsrpObject.create_command('New-Item', ['-Path test', '-Type file']), pretty=True, full_document=False)
    assert xml_str_compare(actual, expected)


@mock.patch('uuid.uuid4', side_effect=mock_uuid)
def test_create_command_with_parameter_key(mock_uuid):
    expected = """
        <Obj RefId="286331153">
            <MS>
                <S N="Cmd">New-Item</S>
                <B N="IsScript">false</B>
                <Nil N="UseLocalScope"></Nil>
                <Obj N="MergeMyResult" RefId="286331153">
                    <TN RefId="286331153">
                        <T>System.Management.Automation.Runspaces.PipelineResultTypes</T>
                        <T>System.Enum</T>
                        <T>System.ValueType</T>
                        <T>System.Object</T>
                    </TN>
                    <ToString>None</ToString>
                    <I32>0</I32>
                </Obj>
                <Obj N="MergeToResult" RefId="286331153">
                    <TNRef RefId="286331153"></TNRef>
                    <ToString>None</ToString>
                    <I32>0</I32>
                </Obj>
                <Obj N="MergePreviousResults" RefId="286331153">
                    <TNRef RefId="286331153"></TNRef>
                    <ToString>None</ToString>
                    <I32>0</I32>
                </Obj>
                <Obj N="MergeError" RefId="286331153">
                    <TNRef RefId="286331153"></TNRef>
                    <ToString>None</ToString>
                    <I32>0</I32>
                </Obj>
                <Obj N="MergeWarning" RefId="286331153">
                    <TNRef RefId="286331153"></TNRef>
                    <ToString>None</ToString>
                    <I32>0</I32>
                </Obj>
                <Obj N="MergeVerbose" RefId="286331153">
                    <TNRef RefId="286331153"></TNRef>
                    <ToString>None</ToString>
                    <I32>0</I32>
                </Obj>
                <Obj N="MergeDebug" RefId="286331153">
                    <TNRef RefId="286331153"></TNRef>
                    <ToString>None</ToString>
                    <I32>0</I32>
                </Obj>
                <Obj N="Args" RefId="286331153">
                    <TN RefId="286331153">
                        <T>System.Collections.Generic.List`1[[System.Management.Automation.PSObject, System.Management.Automation, Version=3.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35]]</T>
                        <T>System.Object</T>
                    </TN>
                    <LST>
                        <Obj RefId="286331153">
                            <MS>
                                <S N="N">-Force</S>
                                <Nil N="V"></Nil>
                            </MS>
                        </Obj>
                    </LST>
                </Obj>
            </MS>
        </Obj>"""
    actual = xmltodict.unparse(PsrpObject.create_command('New-Item', ['-Force']), pretty=True, full_document=False)
    assert xml_str_compare(actual, expected)


@mock.patch('uuid.uuid4', side_effect=mock_uuid)
def test_create_host_info(mock_uuid):
    expected = """
        <Obj N="HostInfo" RefId="286331153">
            <MS>
                <Obj N="_hostDefaultData" RefId="286331153">
                    <MS>
                        <Obj N="data" RefId="286331153">
                            <TN RefId="286331153">
                                <T>System.Collections.Hashtable</T>
                                <T>System.Object</T>
                            </TN>
                            <DCT>
                                <En>
                                    <I32 N="Key">0</I32>
                                    <Obj N="Value" RefId="286331153">
                                        <MS>
                                            <S N="T">System.ConsoleColor</S>
                                            <I32 N="V">7</I32>
                                        </MS>
                                    </Obj>
                                </En>
                                <En>
                                    <I32 N="Key">1</I32>
                                    <Obj N="Value" RefId="286331153">
                                        <MS>
                                            <S N="T">System.ConsoleColor</S>
                                            <I32 N="V">9</I32>
                                        </MS>
                                    </Obj>
                                </En>
                                <En>
                                    <I32 N="Key">2</I32>
                                    <Obj N="Value" RefId="286331153">
                                        <MS>
                                            <S N="T">System.Management.Automation.Host.Coordinates</S>
                                            <Obj N="V" RefId="286331153">
                                                <MS>
                                                    <I32 N="x">0</I32>
                                                    <I32 N="y">4</I32>
                                                </MS>
                                            </Obj>
                                        </MS>
                                    </Obj>
                                </En>
                                <En>
                                    <I32 N="Key">3</I32>
                                    <Obj N="Value" RefId="286331153">
                                        <MS>
                                            <S N="T">System.Management.Automation.Host.Coordinates</S>
                                            <Obj N="V" RefId="286331153">
                                                <MS>
                                                    <I32 N="x">0</I32>
                                                    <I32 N="y">0</I32>
                                                </MS>
                                            </Obj>
                                        </MS>
                                    </Obj>
                                </En>
                                <En>
                                    <I32 N="Key">4</I32>
                                    <Obj N="Value" RefId="286331153">
                                        <MS>
                                            <S N="T">System.Int32</S>
                                            <I32 N="V">25</I32>
                                        </MS>
                                    </Obj>
                                </En>
                                <En>
                                    <I32 N="Key">5</I32>
                                    <Obj N="Value" RefId="286331153">
                                        <MS>
                                            <S N="T">System.Management.Automation.Host.Size</S>
                                            <Obj N="V" RefId="286331153">
                                                <MS>
                                                    <I32 N="width">120</I32>
                                                    <I32 N="height">3000</I32>
                                                </MS>
                                            </Obj>
                                        </MS>
                                    </Obj>
                                </En>
                                <En>
                                    <I32 N="Key">6</I32>
                                    <Obj N="Value" RefId="286331153">
                                        <MS>
                                            <S N="T">System.Management.Automation.Host.Size</S>
                                            <Obj N="V" RefId="286331153">
                                                <MS>
                                                    <I32 N="width">120</I32>
                                                    <I32 N="height">79</I32>
                                                </MS>
                                            </Obj>
                                        </MS>
                                    </Obj>
                                </En>
                                <En>
                                    <I32 N="Key">7</I32>
                                    <Obj N="Value" RefId="286331153">
                                        <MS>
                                            <S N="T">System.Management.Automation.Host.Size</S>
                                            <Obj N="V" RefId="286331153">
                                                <MS>
                                                    <I32 N="width">120</I32>
                                                    <I32 N="height">98</I32>
                                                </MS>
                                            </Obj>
                                        </MS>
                                    </Obj>
                                </En>
                                <En>
                                    <I32 N="Key">8</I32>
                                    <Obj N="Value" RefId="286331153">
                                        <MS>
                                            <S N="T">System.Management.Automation.Host.Size</S>
                                            <Obj N="V" RefId="286331153">
                                                <MS>
                                                    <I32 N="width">181</I32>
                                                    <I32 N="height">98</I32>
                                                </MS>
                                            </Obj>
                                        </MS>
                                    </Obj>
                                </En>
                                <En>
                                    <I32 N="Key">9</I32>
                                    <Obj N="Value" RefId="286331153">
                                        <MS>
                                            <S N="T">System.String</S>
                                            <S N="V">Pywinrm PSRP</S>
                                        </MS>
                                    </Obj>
                                </En>
                            </DCT>
                        </Obj>
                    </MS>
                </Obj>
                <B N="_isHostNull">false</B>
                <B N="_isHostUINull">false</B>
                <B N="_isHostRawUINull">false</B>
                <B N="_useRunspaceHost">false</B>
            </MS>
        </Obj>"""
    actual = xmltodict.unparse(PsrpObject.create_host_info(), pretty=True, full_document=False)
    assert xml_str_compare(actual, expected)


@mock.patch('uuid.uuid4', side_effect=mock_uuid)
def test_create_host_method_identifier(mock_uuid):
    expected = """
        <Obj RefId="286331153" N="mi">
            <TN RefId="286331153">
                <T>System.Management.Automation.Remoting.RemoteHostMethodId</T>
                <T>System.Enum</T>
                <T>System.ValueType</T>
                <T>System.Object</T>
            </TN>
            <ToString>Prompt</ToString>
            <I32>32</I32>
        </Obj>"""
    actual = xmltodict.unparse(PsrpObject.create_host_method_identifier("Prompt", "32"), pretty=True, full_document=False)
    assert xml_str_compare(actual, expected)


@mock.patch('uuid.uuid4', side_effect=mock_uuid)
def test_create_session_capability(mock_uuid):
    expected = """
        <Obj RefId="286331153">
            <MS>
                <Version N="PSVersion">2.0</Version>
                <Version N="protocolversion">2.2</Version>
                <Version N="SerializationVersion">1.1.0.1</Version>
            </MS>
        </Obj>"""
    actual = xmltodict.unparse(SessionCapability("2.0", "2.2", "1.1.0.1").create_message_data(), pretty=True, full_document=False)
    assert xml_str_compare(actual, expected)


def test_parse_session_capability():
    message = xmltodict.parse("""
        <Obj RefId="286331153">
            <MS>
                <Version N="PSVersion">2.0</Version>
                <Version N="protocolversion">2.2</Version>
                <Version N="SerializationVersion">1.1.0.1</Version>
            </MS>
        </Obj>""")
    actual = SessionCapability.parse_message_data(
        Message(1, mock_uuid(), mock_uuid(), PrimitiveMessage(PsrpMessageType.SESSION_CAPABILITY, message)))
    assert actual.ps_version == "2.0"
    assert actual.protocol_version == "2.2"
    assert actual.serialization_version == "1.1.0.1"


def test_parse_session_capability_fail():
    with pytest.raises(WinRMError) as excinfo:
        message = xmltodict.parse("""
            <Obj RefId="286331153">
                <MS>
                    <Version N="ShouldntBeHere">1</Version>
                    <Version N="PSVersion">2.0</Version>
                    <Version N="protocolversion">2.2</Version>
                    <Version N="SerializationVersion">1.1.0.1</Version>
                </MS>
            </Obj>""")
        SessionCapability.parse_message_data(
            Message(1, mock_uuid(), mock_uuid(), PrimitiveMessage(PsrpMessageType.SESSION_CAPABILITY, message)))

    assert str(excinfo.value) == 'Expecting 3 version properties in SESSION_CAPAIBLITY, actual: 4'


@mock.patch('uuid.uuid4', side_effect=mock_uuid)
def test_init_runspace_pool(mock_uuid):
    expected = """
        <Obj RefId="286331153">
            <MS>
                <I32 N="MinRunspaces">1</I32>
                <I32 N="MaxRunspaces">1</I32>
                <Obj N="PSThreadOptions" RefId="286331153">
                    <TN RefId="286331153">
                        <T>System.Management.Automation.Runspaces.PSThreadOptions</T>
                        <T>System.Enum</T>
                        <T>System.ValueType</T>
                        <T>System.Object</T>
                    </TN>
                    <ToString>Default</ToString>
                    <I32>0</I32>
                </Obj>
                <Obj N="ApartmentState" RefId="286331153">
                    <TN RefId="286331153">
                        <T>System.Threading.ApartmentState</T>
                        <T>System.Enum</T>
                        <T>System.ValueType</T>
                        <T>System.Object</T>
                    </TN>
                    <ToString>Unknown</ToString>
                    <I32>2</I32>
                </Obj>
                <Obj N="HostInfo" RefId="286331153">
                    <MS>
                        <Obj N="_hostDefaultData" RefId="286331153">
                            <MS>
                                <Obj N="data" RefId="286331153">
                                    <TN RefId="286331153">
                                        <T>System.Collections.Hashtable</T>
                                        <T>System.Object</T>
                                    </TN>
                                    <DCT>
                                        <En>
                                            <I32 N="Key">0</I32>
                                            <Obj N="Value" RefId="286331153">
                                                <MS>
                                                    <S N="T">System.ConsoleColor</S>
                                                    <I32 N="V">7</I32>
                                                </MS>
                                            </Obj>
                                        </En>
                                        <En>
                                            <I32 N="Key">1</I32>
                                            <Obj N="Value" RefId="286331153">
                                                <MS>
                                                    <S N="T">System.ConsoleColor</S>
                                                    <I32 N="V">9</I32>
                                                </MS>
                                            </Obj>
                                        </En>
                                        <En>
                                            <I32 N="Key">2</I32>
                                            <Obj N="Value" RefId="286331153">
                                                <MS>
                                                    <S N="T">System.Management.Automation.Host.Coordinates</S>
                                                    <Obj N="V" RefId="286331153">
                                                        <MS>
                                                            <I32 N="x">0</I32>
                                                            <I32 N="y">4</I32>
                                                        </MS>
                                                    </Obj>
                                                </MS>
                                            </Obj>
                                        </En>
                                        <En>
                                            <I32 N="Key">3</I32>
                                            <Obj N="Value" RefId="286331153">
                                                <MS>
                                                    <S N="T">System.Management.Automation.Host.Coordinates</S>
                                                    <Obj N="V" RefId="286331153">
                                                        <MS>
                                                            <I32 N="x">0</I32>
                                                            <I32 N="y">0</I32>
                                                        </MS>
                                                    </Obj>
                                                </MS>
                                            </Obj>
                                        </En>
                                        <En>
                                            <I32 N="Key">4</I32>
                                            <Obj N="Value" RefId="286331153">
                                                <MS>
                                                    <S N="T">System.Int32</S>
                                                    <I32 N="V">25</I32>
                                                </MS>
                                            </Obj>
                                        </En>
                                        <En>
                                            <I32 N="Key">5</I32>
                                            <Obj N="Value" RefId="286331153">
                                                <MS>
                                                    <S N="T">System.Management.Automation.Host.Size</S>
                                                    <Obj N="V" RefId="286331153">
                                                        <MS>
                                                            <I32 N="width">120</I32>
                                                            <I32 N="height">3000</I32>
                                                        </MS>
                                                    </Obj>
                                                </MS>
                                            </Obj>
                                        </En>
                                        <En>
                                            <I32 N="Key">6</I32>
                                            <Obj N="Value" RefId="286331153">
                                                <MS>
                                                    <S N="T">System.Management.Automation.Host.Size</S>
                                                    <Obj N="V" RefId="286331153">
                                                        <MS>
                                                            <I32 N="width">120</I32>
                                                            <I32 N="height">79</I32>
                                                        </MS>
                                                    </Obj>
                                                </MS>
                                            </Obj>
                                        </En>
                                        <En>
                                            <I32 N="Key">7</I32>
                                            <Obj N="Value" RefId="286331153">
                                                <MS>
                                                    <S N="T">System.Management.Automation.Host.Size</S>
                                                    <Obj N="V" RefId="286331153">
                                                        <MS>
                                                            <I32 N="width">120</I32>
                                                            <I32 N="height">98</I32>
                                                        </MS>
                                                    </Obj>
                                                </MS>
                                            </Obj>
                                        </En>
                                        <En>
                                            <I32 N="Key">8</I32>
                                            <Obj N="Value" RefId="286331153">
                                                <MS>
                                                    <S N="T">System.Management.Automation.Host.Size</S>
                                                    <Obj N="V" RefId="286331153">
                                                        <MS>
                                                            <I32 N="width">181</I32>
                                                            <I32 N="height">98</I32>
                                                        </MS>
                                                    </Obj>
                                                </MS>
                                            </Obj>
                                        </En>
                                        <En>
                                            <I32 N="Key">9</I32>
                                            <Obj N="Value" RefId="286331153">
                                                <MS>
                                                    <S N="T">System.String</S>
                                                    <S N="V">Pywinrm PSRP</S>
                                                </MS>
                                            </Obj>
                                        </En>
                                    </DCT>
                                </Obj>
                            </MS>
                        </Obj>
                        <B N="_isHostNull">false</B>
                        <B N="_isHostUINull">false</B>
                        <B N="_isHostRawUINull">false</B>
                        <B N="_useRunspaceHost">false</B>
                    </MS>
                </Obj>
                <Nil N="ApplicationArguments"></Nil>
            </MS>
        </Obj>"""
    actual = xmltodict.unparse(InitRunspacePool("1", "1").create_message_data(), pretty=True, full_document=False)
    assert xml_str_compare(actual, expected)


def test_parse_runspace_pool_state():
    message = xmltodict.parse("""
        <Obj RefId="1">
            <MS>
                <I32 N="RunspaceState">2</I32>
            </MS>
        </Obj>""")
    actual = RunspacePoolState.parse_message_data(
        Message(1, mock_uuid(), mock_uuid(), PrimitiveMessage(PsrpMessageType.RUNSPACEPOOL_STATE, message)))
    assert actual.state == '2'
    assert actual.friendly_state == 'OPENED'


def test_parse_runspace_pool_state_invalid_message():
    with pytest.raises(WinRMError) as excinfo:
        message = xmltodict.parse("""
            <Obj RefId="1">
                <MS>
                    <I32 N="OtherAttribute">2</I32>
                </MS>
            </Obj>""")
        RunspacePoolState.parse_message_data(
            Message(1, mock_uuid(), mock_uuid(), PrimitiveMessage(PsrpMessageType.RUNSPACEPOOL_STATE, message)))

    assert str(excinfo.value) == 'Invalid RUNSPACE_STATE message from the server'


def test_parse_runspace_pool_state_unknown_state():
    with pytest.raises(WinRMError) as excinfo:
        message = xmltodict.parse("""
            <Obj RefId="1">
                <MS>
                    <I32 N="RunspaceState">10</I32>
                </MS>
            </Obj>""")
        RunspacePoolState.parse_message_data(
            Message(1, mock_uuid(), mock_uuid(), PrimitiveMessage(PsrpMessageType.RUNSPACEPOOL_STATE, message)))

    assert str(excinfo.value) == 'Invalid RunspacePoolState value of 10'


@mock.patch('uuid.uuid4', side_effect=mock_uuid)
def test_create_create_pipeline(mock_uuid):
    expected = """
        <Obj RefId="286331153">
            <MS>
                <B N="NoInput">false</B>
                <B N="AddToHistory">true</B>
                <B N="IsNested">false</B>
                <Obj N="ApartmentState" RefId="286331153">
                    <TN RefId="286331153">
                        <T>System.Threading.ApartmentState</T>
                        <T>System.Enum</T>
                        <T>System.ValueType</T>
                        <T>System.Object</T>
                    </TN>
                    <ToString>Unknown</ToString>
                    <I32>2</I32>
                </Obj>
                <Obj N="RemoteStreamOptions" RefId="286331153">
                    <TN RefId="286331153">
                        <T>System.Management.Automation.RemoteStreamOptions</T>
                        <T>System.Enum</T>
                        <T>System.ValueType</T>
                        <T>System.Object</T>
                    </TN>
                    <ToString>0</ToString>
                    <I32>0</I32>
                </Obj>
                <Obj N="HostInfo" RefId="286331153">
                    <MS>
                        <Obj N="_hostDefaultData" RefId="286331153">
                            <MS>
                                <Obj N="data" RefId="286331153">
                                    <TN RefId="286331153">
                                        <T>System.Collections.Hashtable</T>
                                        <T>System.Object</T>
                                    </TN>
                                    <DCT>
                                        <En>
                                            <I32 N="Key">0</I32>
                                            <Obj N="Value" RefId="286331153">
                                                <MS>
                                                    <S N="T">System.ConsoleColor</S>
                                                    <I32 N="V">7</I32>
                                                </MS>
                                            </Obj>
                                        </En>
                                        <En>
                                            <I32 N="Key">1</I32>
                                            <Obj N="Value" RefId="286331153">
                                                <MS>
                                                    <S N="T">System.ConsoleColor</S>
                                                    <I32 N="V">9</I32>
                                                </MS>
                                            </Obj>
                                        </En>
                                        <En>
                                            <I32 N="Key">2</I32>
                                            <Obj N="Value" RefId="286331153">
                                                <MS>
                                                    <S N="T">System.Management.Automation.Host.Coordinates</S>
                                                    <Obj N="V" RefId="286331153">
                                                        <MS>
                                                            <I32 N="x">0</I32>
                                                            <I32 N="y">4</I32>
                                                        </MS>
                                                    </Obj>
                                                </MS>
                                            </Obj>
                                        </En>
                                        <En>
                                            <I32 N="Key">3</I32>
                                            <Obj N="Value" RefId="286331153">
                                                <MS>
                                                    <S N="T">System.Management.Automation.Host.Coordinates</S>
                                                    <Obj N="V" RefId="286331153">
                                                        <MS>
                                                            <I32 N="x">0</I32>
                                                            <I32 N="y">0</I32>
                                                        </MS>
                                                    </Obj>
                                                </MS>
                                            </Obj>
                                        </En>
                                        <En>
                                            <I32 N="Key">4</I32>
                                            <Obj N="Value" RefId="286331153">
                                                <MS>
                                                    <S N="T">System.Int32</S>
                                                    <I32 N="V">25</I32>
                                                </MS>
                                            </Obj>
                                        </En>
                                        <En>
                                            <I32 N="Key">5</I32>
                                            <Obj N="Value" RefId="286331153">
                                                <MS>
                                                    <S N="T">System.Management.Automation.Host.Size</S>
                                                    <Obj N="V" RefId="286331153">
                                                        <MS>
                                                            <I32 N="width">120</I32>
                                                            <I32 N="height">3000</I32>
                                                        </MS>
                                                    </Obj>
                                                </MS>
                                            </Obj>
                                        </En>
                                        <En>
                                            <I32 N="Key">6</I32>
                                            <Obj N="Value" RefId="286331153">
                                                <MS>
                                                    <S N="T">System.Management.Automation.Host.Size</S>
                                                    <Obj N="V" RefId="286331153">
                                                        <MS>
                                                            <I32 N="width">120</I32>
                                                            <I32 N="height">79</I32>
                                                        </MS>
                                                    </Obj>
                                                </MS>
                                            </Obj>
                                        </En>
                                        <En>
                                            <I32 N="Key">7</I32>
                                            <Obj N="Value" RefId="286331153">
                                                <MS>
                                                    <S N="T">System.Management.Automation.Host.Size</S>
                                                    <Obj N="V" RefId="286331153">
                                                        <MS>
                                                            <I32 N="width">120</I32>
                                                            <I32 N="height">98</I32>
                                                        </MS>
                                                    </Obj>
                                                </MS>
                                            </Obj>
                                        </En>
                                        <En>
                                            <I32 N="Key">8</I32>
                                            <Obj N="Value" RefId="286331153">
                                                <MS>
                                                    <S N="T">System.Management.Automation.Host.Size</S>
                                                    <Obj N="V" RefId="286331153">
                                                        <MS>
                                                            <I32 N="width">181</I32>
                                                            <I32 N="height">98</I32>
                                                        </MS>
                                                    </Obj>
                                                </MS>
                                            </Obj>
                                        </En>
                                        <En>
                                            <I32 N="Key">9</I32>
                                            <Obj N="Value" RefId="286331153">
                                                <MS>
                                                    <S N="T">System.String</S>
                                                    <S N="V">Pywinrm PSRP</S>
                                                </MS>
                                            </Obj>
                                        </En>
                                    </DCT>
                                </Obj>
                            </MS>
                        </Obj>
                        <B N="_isHostNull">false</B>
                        <B N="_isHostUINull">false</B>
                        <B N="_isHostRawUINull">false</B>
                        <B N="_useRunspaceHost">false</B>
                    </MS>
                </Obj>
                <Obj N="PowerShell" RefId="286331153">
                    <MS>
                        <Obj N="Cmds" RefId="286331153">
                            <TN RefId="286331153">
                                <T>System.Collections.Generic.List`1[[System.Management.Automation.PSObject, System.Management.Automation, Version=3.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35]]</T>
                                <T>System.Object</T>
                            </TN>
                            <LST>
                                <Obj>Test</Obj>
                            </LST>
                        </Obj>
                        <B N="IsNested">false</B>
                        <B N="RedirectShellErrorOutputPipe">true</B>
                        <Nil N="History"></Nil>
                    </MS>
                </Obj>
            </MS>
        </Obj>"""
    actual = xmltodict.unparse(CreatePipeline([{"Obj": "Test"}], False).create_message_data(), pretty=True, full_document=False)
    assert xml_str_compare(actual, expected)


def test_parse_application_private_data_win_2016():
    message = xmltodict.parse("""
        <Obj RefId="0">
            <MS>
                <Obj N="ApplicationPrivateData" RefId="1">
                    <TN RefId="0">
                        <T>System.Management.Automation.PSPrimitiveDictionary</T>
                        <T>System.Collections.Hashtable</T>
                        <T>System.Object</T>
                    </TN>
                    <DCT>
                        <En>
                            <S N="Key">PSVersionTable</S>
                            <Obj N="Value" RefId="2">
                                <TNRef RefId="0"></TNRef>
                                <DCT>
                                    <En>
                                        <S N="Key">PSVersion</S>
                                        <Version N="Value">5.1.14393.953</Version>
                                    </En>
                                    <En>
                                        <S N="Key">PSEdition</S>
                                        <S N="Value">Desktop</S>
                                    </En>
                                    <En>
                                        <S N="Key">PSCompatibleVersions</S>
                                        <Obj N="Value" RefId="3">
                                            <TN RefId="1">
                                                <T>System.Version[]</T>
                                                <T>System.Array</T>
                                                <T>System.Object</T>
                                            </TN>
                                            <LST>
                                                <Version>1.0</Version>
                                                <Version>2.0</Version>
                                                <Version>3.0</Version>
                                                <Version>4.0</Version>
                                                <Version>5.0</Version>
                                                <Version>5.1.14393.953</Version>
                                            </LST>
                                        </Obj>
                                    </En>
                                    <En>
                                        <S N="Key">CLRVersion</S>
                                        <Version N="Value">4.0.30319.42000</Version>
                                    </En>
                                    <En>
                                        <S N="Key">BuildVersion</S>
                                        <Version N="Value">10.0.14393.953</Version>
                                    </En>
                                    <En>
                                        <S N="Key">WSManStackVersion</S>
                                        <Version N="Value">3.0</Version>
                                    </En>
                                    <En>
                                        <S N="Key">PSRemotingProtocolVersion</S>
                                        <Version N="Value">2.3</Version>
                                    </En>
                                    <En>
                                        <S N="Key">SerializationVersion</S>
                                        <Version N="Value">1.1.0.1</Version>
                                    </En>
                                </DCT>
                            </Obj>
                        </En>
                    </DCT>
                </Obj>
            </MS>
        </Obj>""")
    actual = ApplicationPrivateData.parse_message_data(
        Message(1, mock_uuid(), mock_uuid(), PrimitiveMessage(PsrpMessageType.APPLICATION_PRIVATE_DATA, message)))
    expected = {
        'PSVersionTable': {
            'BuildVersion': '10.0.14393.953',
            'CLRVersion': '4.0.30319.42000',
            'PSCompatibleVersions': [
                '1.0',
                '2.0',
                '3.0',
                '4.0',
                '5.0',
                '5.1.14393.953'
            ],
            'PSEdition': 'Desktop',
            'PSRemotingProtocolVersion': '2.3',
            'PSVersion': '5.1.14393.953',
            'SerializationVersion': '1.1.0.1',
            'WSManStackVersion': '3.0'
        }
    }
    assert actual.application_info == expected


def test_parse_application_private_data_win_2012():
    message = xmltodict.parse("""
        <Obj RefId="0">
            <MS>
                <Obj N="ApplicationPrivateData" RefId="1">
                    <TN RefId="0">
                        <T>System.Management.Automation.PSPrimitiveDictionary</T>
                        <T>System.Collections.Hashtable</T>
                        <T>System.Object</T>
                    </TN>
                    <DCT>
                        <En>
                            <S N="Key">DebugMode</S>
                            <I32 N="Value">1</I32>
                        </En>
                        <En>
                            <S N="Key">DebugStop</S>
                            <B N="Value">false</B>
                        </En>
                        <En>
                            <S N="Key">PSVersionTable</S>
                            <Obj N="Value" RefId="2">
                                <TNRef RefId="0"></TNRef>
                                <DCT>
                                    <En>
                                        <S N="Key">PSVersion</S>
                                        <Version N="Value">2.0</Version>
                                    </En>
                                    <En>
                                        <S N="Key">PSCompatibleVersions</S>
                                        <Obj N="Value" RefId="3">
                                            <TN RefId="1">
                                                <T>System.Version[]</T>
                                                <T>System.Array</T>
                                                <T>System.Object</T>
                                            </TN>
                                            <LST>
                                                <Version>1.0</Version>
                                                <Version>2.0</Version>
                                                <Version>3.0</Version>
                                                <Version>4.0</Version>
                                            </LST>
                                        </Obj>
                                    </En>
                                    <En>
                                        <S N="Key">BuildVersion</S>
                                        <Version N="Value">6.3.9600.17400</Version>
                                    </En>
                                    <En>
                                        <S N="Key">CLRVersion</S>
                                        <Version N="Value">4.0.30319.42000</Version>
                                    </En>
                                    <En>
                                        <S N="Key">WSManStackVersion</S>
                                        <Version N="Value">3.0</Version>
                                    </En>
                                    <En>
                                        <S N="Key">PSRemotingProtocolVersion</S>
                                        <Version N="Value">2.2</Version>
                                    </En>
                                    <En>
                                        <S N="Key">SerializationVersion</S>
                                        <Version N="Value">1.1.0.1</Version>
                                    </En>
                                </DCT>
                            </Obj>
                        </En>
                        <En>
                            <S N="Key">DebugBreakpointCount</S>
                            <I32 N="Value">0</I32>
                        </En>
                    </DCT>
                </Obj>
            </MS>
        </Obj>""")
    actual = ApplicationPrivateData.parse_message_data(
        Message(1, mock_uuid(), mock_uuid(), PrimitiveMessage(PsrpMessageType.APPLICATION_PRIVATE_DATA, message)))
    expected = {
        'DebugBreakpointCount': '0',
        'DebugMode': '1',
        'DebugStop': 'false',
        'PSVersionTable': {
            'BuildVersion': '6.3.9600.17400',
            'CLRVersion': '4.0.30319.42000',
            'PSCompatibleVersions': [
                '1.0',
                '2.0',
                '3.0',
                '4.0'
            ],
            'PSRemotingProtocolVersion': '2.2',
            'PSVersion': '2.0',
            'SerializationVersion': '1.1.0.1',
            'WSManStackVersion': '3.0'
        }
    }
    assert actual.application_info == expected


def test_create_pipeline_input():
    expected = "<S>test input</S>"
    actual = xmltodict.unparse(PipelineInput("test input").create_message_data(), pretty=True, full_document=False)
    assert xml_str_compare(actual, expected)


def test_create_end_of_pipeline_input():
    expected = ""
    actual = EndOfPipelineInput().create_message_data()
    assert actual == expected


def test_parse_application_private_data_invalid_message():
    with pytest.raises(WinRMError) as excinfo:
        message = xmltodict.parse("<S>Fail</S>")
        ApplicationPrivateData.parse_message_data(
            Message(1, mock_uuid(), mock_uuid(), PrimitiveMessage(PsrpMessageType.APPLICATION_PRIVATE_DATA, message)))

    assert str(excinfo.value) == 'Invalid APPLICATION_PRIVATE_DATA message from the server'


def test_parse_pipeline_state():
    message = xmltodict.parse("""
        <Obj RefId="0">
            <MS>
                <I32 N="PipelineState">3</I32>
                <Obj N="ExceptionAsErrorRecord" RefId="1">
                    <TN RefId="0">
                        <T>System.Management.Automation.ErrorRecord</T>
                        <T>System.Object</T>
                    </TN>
                    <ToString>The pipeline has been stopped.</ToString>
                    <MS>
                        <Obj N="Exception" RefId="2">
                            <TN RefId="1">
                                <T>System.Management.Automation.PipelineStoppedException</T>
                                <T>System.Management.Automation.RuntimeException</T>
                                <T>System.SystemException</T>
                                <T>System.Exception</T>
                                <T>System.Object</T>
                            </TN>
                            <ToString>System.Management.Automation.PipelineStoppedException: The pipeline has been stopped._x000D__x000A_ at System.Management.Automation.Internal.PipelineProcessor.SynchronousExecuteEnumerate(Object input, Hashtable errorResults, Boolean enumerate) in c:\\e\\win7_powershell\\admin\\monad\\src\\engine\\pipeline.cs:line 586</ToString>
                            <Props>
                                <S N="ErrorRecord">The pipeline has been stopped.</S>
                                <S N="StackTrace"> at System.Management.Automation.Internal.PipelineProcessor.SynchronousExecuteEnumerate(Object input, Hashtable errorResults, Boolean enumerate) in c:\\e\\win7_powershell\\admin\\monad\\src\\engine\\pipeline.cs:line 586</S>
                                <S N="Message">The pipeline has been stopped.</S>
                                <Obj N="Data" RefId="3">
                                    <TN RefId="2">
                                        <T>System.Collections.ListDictionaryInternal</T>
                                        <T>System.Object</T>
                                    </TN>
                                    <DCT/>
                                </Obj>
                                <Nil N="InnerException"/>
                                <S N="TargetSite">System.Array SynchronousExecuteEnumerate(System.Object, System.Collections.Hashtable, Boolean)</S>
                                <Nil N="HelpLink"/>
                                <S N="Source">System.Management.Automation</S>
                            </Props>
                        </Obj>
                        <Nil N="TargetObject"/>
                        <S N="FullyQualifiedErrorId">PipelineStopped</S>
                        <Nil N="InvocationInfo"/>
                        <I32 N="ErrorCategory_Category">14</I32>
                        <S N="ErrorCategory_Activity"/>
                        <S N="ErrorCategory_Reason">PipelineStoppedException</S>
                        <S N="ErrorCategory_TargetName"/>
                        <S N="ErrorCategory_TargetType"/>
                        <S N="ErrorCategory_Message">OperationStopped: (:) [], PipelineStoppedException</S>
                        <B N="SerializeExtendedInfo">false</B>
                    </MS>
                </Obj>
            </MS>
        </Obj>""")
    actual = PipelineState.parse_message_data(
        Message(1, mock_uuid(), mock_uuid(), PrimitiveMessage(PsrpMessageType.PIPELINE_STATE, message)))
    assert actual.state == '3'
    assert actual.friendly_state == 'STOPPED'
    assert actual.exception_as_error_record['ToString'] == 'The pipeline has been stopped.'
    assert actual.exception_as_error_record['@N'] == 'ExceptionAsErrorRecord'


@mock.patch('uuid.uuid4', side_effect=mock_uuid)
def test_create_pipeline_host_response(mock_uuid):
    expected = """
        <Obj RefId="286331153">
            <MS>
                <Obj RefId="286331153" N="mr">
                    <TN RefId="286331153">
                        <T>System.Collections.Hashtable</T>
                        <T>System.Object</T>
                    </TN>
                    <DCT>
                        <En>
                            <S N="Key">Enter Info</S>
                            <S N="Value">Inof</S>
                        </En>
                    </DCT>
                </Obj>
                <Obj RefId="286331153" N="mi">
                    <TN RefId="286331153">
                        <T>System.Management.Automation.Remoting.RemoteHostMethodId</T>
                        <T>System.Enum</T>
                        <T>System.ValueType</T>
                        <T>System.Object</T>
                    </TN>
                    <ToString>Prompt</ToString>
                    <I32>1</I32>
                </Obj>
                <I64 N="ci">1</I64>
            </MS>
        </Obj>"""
    actual = xmltodict.unparse(PipelineHostResponse("1", "1", "Prompt", "Enter Info", "Inof").create_message_data(), pretty=True, full_document=False)
    assert xml_str_compare(actual, expected)
