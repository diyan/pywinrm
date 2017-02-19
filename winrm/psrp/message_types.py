import xmltodict

from winrm.psrp.property_types import SignedInt, Version

class MessageType(object):
    """
    [MS-PSRP] v16.0 2016-07-14
    2.2.1 Powershell Remoting Protocol Message (Message Type)

    The type of message. The value of this field specifies what action MUST be
    taken by the client or server upon receipt. Possible values are listed in
    the following table.
    """

    # Valid message directions
    SERVER = 'Server'
    CLIENT = 'Client'

    # Valid message targets
    RUNSPACE_POOL = 'RunspacePool'
    PIPELINE = 'pipeline'

    def __init(self):
        # raw object of the message data
        self.data = None

    def __str__(self):
        if self.data is None:
            raise Exception("Cannot convert to xml string, data not intialised")

        data = {
            "Obj": {
                "@RefId": self.ref_id,
                "MS": {
                    self.data
                }
            }
        }
        return xmltodict.unparse(data, encoding="utf-8")

    def _create_xml_object(self, xml):
        return xmltodict.parse(xml, encoding="utf-8")


class SessionCapability(MessageType):

    def __init__(self):
        """
        [MS-PSRP] v16.0 2016-07-14
        2.2.2.1 SESSION_CAPABILITY Message
        """
        self.id = 0x00010002
        self.valid_directions = [self.SERVER, self.CLIENT]
        self.target = self.RUNSPACE_POOL
        self.ref_id = 0

    def create(self, ps_version, protocol_version, serialization_version):
        self.ps_version = Version(ps_version, "N", "PSVersion")
        self.protocol_version = Version(protocol_version, "N", "protocolversion")
        self.serialization_version = Version(serialization_version, "N", "SerializationVersion")

        self.data = {
            "Version": [
                self.ps_version.get_data(),
                self.protocol_version.get_data(),
                self.serialization_version.get_data()
            ]
            # TODO: Add support for optional timezone
        }

    def parse(self, xml):
        data = self._create_xml_object(xml)
        self.data = data
        raw_version_elements = data["Obj"]["MS"]["Version"]

        if len(raw_version_elements) != 3:
            raise Exception("Expecting 3 elements in version node: found %d" % len(raw_version_elements))

        elements = ["PSVersion", "protocolversion", "SerializationVersion"]
        version_values = {}
        for element in elements:
            raw_value = [d for d in raw_version_elements if d["@N"] == element]

            if len(raw_value) != 1:
                raise Exception("Expecting 1 element in version node with attribute of '%s', found %d" %
                                (element, len(raw_value)))

            version = Version()
            version.parse_data(raw_value[0], "N")
            version_values[element] = version

        self.ps_version = version_values.get("PSVersion")
        self.protocol_version = version_values.get("protocolversion")
        self.serialization_version = version_values.get("SerializationVersion")

        # TODO: Add support for timezone

class InitRunspacePool(MessageType):

    def __init__(self):
        """
        [MS-PSRP] v16.0 2016-07-14
        2.2.2.2 INIT_RUNSPACEPOOL Message
        """
        self.id = 0x00010004
        self.valid_directions = [self.SERVER]
        self.target = self.RUNSPACE_POOL
        self.ref_id = 1

    def create(self, min_runspaces, max_runspaces, ps_thread_options, apartment_state, host_info, application_arguments):
        self.min_runspaces = SignedInt(min_runspaces, "N", "MinRunspaces")
        self.max_runspaces = SignedInt(max_runspaces, "N", "MaxRunspaces")
        self.ps_thread_options = ps_thread_options
        self.apartment_stat = apartment_state
        self.host_info = host_info
        self.application_arguments = application_arguments
        self.data = {
            self.min_runspaces.get_data(),
            self.max_runspaces.get_data(),
            self.ps_thread_options.get_data(),
            self.apartment_stat.get_data(),
            self.host_info.get_data(),
            self.application_arguments.get_data(),
        }
        a = ''

    def parse(self, xml):
        a = ''