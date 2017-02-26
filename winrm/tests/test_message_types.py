import pytest
import xmltodict

from winrm.psrp.messages import ApplicationPrivateData, InitRunspacePool, RunspaceState, \
    RunspacePoolStates, SessionCapability


def test_create_session_capability():
    session_capability = SessionCapability()

    actual_xml = session_capability.create_message_data("2.2", "2.0", "1.1.0.1")
    actual = xmltodict.parse(actual_xml)
    actual_ref_id = actual["Obj"]["@RefId"]

    assert session_capability.message_type == 65538
    assert session_capability.ps_version == "2.2"
    assert session_capability.protocol_version == "2.0"
    assert session_capability.serialization_version == "1.1.0.1"
    assert actual == {
        'Obj': {
            '@RefId': actual_ref_id,
            'MS': {
                'Version': [
                    {'#text': '2.2', '@N': 'PSVersion'},
                    {'#text': '2.0', '@N': 'protocolversion'},
                    {'#text': '1.1.0.1', '@N': 'SerializationVersion'}
                ]
            }
        }
    }


def test_parse_session_capability():
    test_message = """
    <Obj RefId="0">
        <MS>
            <Version N="protocolversion">2.2</Version>
            <Version N="PSVersion">2.0</Version>
            <Version N="SerializationVersion">1.1.0.1</Version>
        </MS>
    </Obj>
    """

    session_capability = SessionCapability()
    session_capability.parse_message_data(test_message)

    assert session_capability.message_type == 65538
    assert session_capability.ps_version == "2.0"
    assert session_capability.protocol_version == "2.2"
    assert session_capability.serialization_version == "1.1.0.1"


def test_parse_session_capability_already_initialised():
    with pytest.raises(Exception) as excinfo:
        session_capability = SessionCapability()
        session_capability.create_message_data("2.0", "2.2", "1.1.0.1")
        session_capability.parse_message_data("")

    assert "Cannot parse message data on an already initialised object" in str(excinfo.value)


def test_parse_session_capability_wrong_version_count():
    with pytest.raises(Exception) as excinfo:
        test_message = """
        <Obj RefId="0">
            <MS>
                <Version N="protocolversion">2.2</Version>
                <Version N="PSVersion">2.0</Version>
            </MS>
        </Obj>
        """
        session_capability = SessionCapability()
        session_capability.parse_message_data(test_message)

    assert "Expecting 3 version properties in SESSION_CAPAIBLITY, actual: 2" in str(excinfo.value)


def test_parse_session_capability_wrong_version_attribute():
    with pytest.raises(Exception) as excinfo:
        test_message = """
        <Obj RefId="0">
            <MS>
                <Version N="protocolversion">2.2</Version>
                <Version N="PSVersion">2.0</Version>
                <Version N="fake">1.1.0.1</Version>
            </MS>
        </Obj>
        """
        session_capability = SessionCapability()
        session_capability.parse_message_data(test_message)

    assert "Invalid attribute value 'fake'" in str(excinfo.value)


def test_create_init_runspace_pool():
    init_runspace_pool = InitRunspacePool()

    actual_xml = init_runspace_pool.create_message_data("1", "2")
    actual = xmltodict.parse(actual_xml)

    assert init_runspace_pool.message_type == 65540
    assert init_runspace_pool.min_runspaces == "1"
    assert init_runspace_pool.max_runspaces == "2"
    assert actual["Obj"]["MS"]["I32"] == [
        {"@N": "MinRunspaces", "#text": "1"},
        {"@N": "MaxRunspaces", "#text": "2"}
    ]


def test_parse_runspace_pool_state():
    test_xml = '<Obj RefId="1"><MS><I32 N="RunspaceState">2</I32></MS></Obj>'
    runspace_state = RunspaceState()
    runspace_state.parse_message_data(test_xml)

    assert runspace_state.message_type == 135173
    assert runspace_state.state == RunspacePoolStates.OPENED
    assert runspace_state.friendly_state == 'OPENED'


def test_parse_runspace_pool_invalid_state():
    with pytest.raises(Exception) as excinfo:
        test_xml = '<Obj RefId="1"><MS><I32 N="RunspaceState">10</I32></MS></Obj>'
        runspace_state = RunspaceState()
        runspace_state.parse_message_data(test_xml)

    assert "Invalid RunspacePoolState value of 10" in str(excinfo.value)


def test_parse_runspace_pool_invalid_message():
    with pytest.raises(Exception) as excinfo:
        test_xml = '<Obj RefId="1"><MS><I32 N="Other">2</I32></MS></Obj>'
        runspace_state = RunspaceState()
        runspace_state.parse_message_data(test_xml)

    assert "Invalid RUNSPACE_STATE message from the server" in str(excinfo.value)


def test_parse_application_private_data():
    test_xml = """<Obj RefId="0">
        <MS>
            <Obj N="ApplicationPrivateData" RefId="1">
                <TN RefId="0">
                    <T>System.Management.Automation.PSPrimitiveDictionary</T>
                    <T>System.Collections.Hashtable</T>
                    <T>System.Object</T>
                </TN>
                <DCT>
                    <En>
                        <S N="Key">BashPrivateData</S>
                        <Obj N="Value" RefId="2">
                            <TNRef RefId="0" />
                            <DCT>
                                <En>
                                    <S N="Key">BashVersion</S>
                                    <Version N="Value">2.0</Version>
                                </En>
                            </DCT>
                        </Obj>
                    </En>
                </DCT>
            </Obj>
        </MS>
    </Obj>"""

    private_data = ApplicationPrivateData()
    private_data.parse_message_data(test_xml)

    assert private_data.message_type == 135177
    assert private_data.bash_version == "2.0"


def test_parse_malformed_application_private_data():
    with pytest.raises(Exception) as excinfo:
        test_xml = '<Obj></Obj>'
        private_data = ApplicationPrivateData()
        private_data.parse_message_data(test_xml)

    assert "Invalid APPLICATION_PRIVATE_DATA message from the server" in str(excinfo.value)
