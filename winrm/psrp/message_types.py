import xmltodict

from winrm.psrp.property_types import SignedInt, Version

class MessageType(object):

    def __init__(self, object_id_counter=0, type_name_id_counter=0):
        self.object_id_counter = object_id_counter
        self.type_name_id_counter = type_name_id_counter
        self.type_names = []
        self.elements = []

    def __str__(self):
        if len(self.elements) == 0:
            raise Exception("Cannot convert to xml string, elements not intialised")

        data = {
            "Obj": {
                "@RefId": self.object_id_counter,
                "MS": self._unpack_elements(self.elements)
            }
        }
        self.object_id_counter += 1
        return xmltodict.unparse(data, encoding="utf-8")


    def _create_xml_object(self, xml):
        return xmltodict.parse(xml, encoding="utf-8")


    def _unpack_elements(self, elements):
        new_elements = {}
        for element in elements:
            type = element.type
            if type in new_elements:
                values = new_elements[type]
            else:
                values = []

            value = { "#text": element.value }
            if element.attribute_key is not None:
                value["@" + element.attribute_key] = element.attribute_value
            values.append(value)
            new_elements[type] = values

        return new_elements


class SessionCapability(MessageType):
    """
    [MS-PSRP] v16.0 2016-07-14
    2.2.2.1 SESSION_CAPABILITY Message
    """

    def create(self, ps_version, protocol_version, serialization_version):
        self.ps_version = Version(ps_version, "N", "PSVersion")
        self.protocol_version = Version(protocol_version, "N", "protocolversion")
        self.serialization_version = Version(serialization_version, "N", "SerializationVersion")

        self.elements = [
            self.ps_version,
            self.protocol_version,
            self.serialization_version
            # TODO: Add support for optional timezone
        ]

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
    """
    [MS-PSRP] v16.0 2016-07-14
    2.2.2.2 INIT_RUNSPACEPOOL Message
    """

    def create(self, min_runspaces, max_runspaces, ps_thread_options, apartment_state, host_info, application_arguments):
        self.min_runspaces = SignedInt(min_runspaces, "N", "MinRunspaces")
        self.max_runspaces = SignedInt(max_runspaces, "N", "MaxRunspaces")
        self.ps_thread_options = ps_thread_options
        self.apartment_stat = apartment_state
        self.host_info = host_info
        self.application_arguments = application_arguments

        self.elements = [
            self.min_runspaces,
            self.max_runspaces
        ]

    def parse(self, xml):
        a = ''

session_capability = SessionCapability()
session_capability.create("2.2", "2.0", "1.1")
print(str(session_capability))