import struct
import uuid
import xmltodict

from winrm.contants import PsrpRunspacePoolState, PsrpColor


class Message(object):
    DESTINATION_CLIENT = 0x00000001
    DESTINATION_SERVER = 0x00000002

    def __init__(self):
        self.destination = None
        self.message_type = None
        self.rpid = None
        self.pid = None
        self.data = None

    def create_message(self, destination, message_type, rpid, pid, data):
        self.destination = destination
        self.message_type = message_type
        self.rpid = rpid
        self.pid = pid
        self.data = data

        message = struct.pack("<I", self.destination)
        message += struct.pack("<I", self.message_type)
        message += rpid.bytes
        message += pid.bytes
        message += data

        return message

    def parse_message(self, message):
        self.destination = struct.unpack("<I", message[0:4])[0]
        self.message_type = struct.unpack("<I", message[4:8])[0]
        self.rpid = self._unpack_uuid(message[8:24])
        self.pid = self._unpack_uuid(message[24:40])
        self.data = message[40:]

    def _unpack_uuid(self, bytes):
        a, b = struct.unpack('>QQ', bytes)
        uuid_int = (a << 64) | b
        return uuid.UUID(int=uuid_int)


class ObjectTypes(object):
    @staticmethod
    def create_coordinate(x, y):
        """
        [MS-PSRP] v16.0 2016-07-14
        2.2.3.1 Coordinates

        This data type represents a position in the screen buffer area of a user interface

        :param x: String - x coordinate
        :param y: String - y coordinate
        :return: dict of the Coordinate object
        """
        coordinate = {
            "Obj": {
                "@N": "Value",
                "@RefId": ObjectTypes.get_random_ref_id(),
                "MS": {
                    "S": {"@N": "T", "#text": "System.Management.Automation.Host.Coordinates"},
                    "Obj": {
                        "@N": "V",
                        "@RefId": ObjectTypes.get_random_ref_id(),
                        "MS": {
                            "I32": [
                                {"@N": "x", "#text": x},
                                {"@N": "y","#text": y}
                            ]
                        }
                    }
                }
            }
        }
        return coordinate

    @staticmethod
    def create_size(width, height):
        """
        [MS-PSRP] v16.0 2016-07-14
        2.2.3.2 Size

        This data type represents a size of a screen buffer area of a user interface

        :param width: String - width of the area
        :param height: String - height of the area
        :return: dict of the Size object
        """
        size = {
            "Obj": {
                "@N": "Value",
                "@RefId": ObjectTypes.get_random_ref_id(),
                "MS": {
                    "S": {"@N": "T", "#text": "System.Management.Automation.Host.Size"},
                    "Obj": {
                        "@N": "V",
                        "@RefId": ObjectTypes.get_random_ref_id(),
                        "MS": {
                            "I32": [
                                {"@N": "width", "#text": width},
                                {"@N": "height", "#text": height}
                            ]
                        }
                    }
                }
            }
        }
        return size

    @staticmethod
    def create_color(color):
        """
        [MS-PSRP] v16.0 2016-07-14
        2.2.3.3 Color

        This data type represents a color used in a user interface

        :param color: The color value, use Colors()
        :return: dict of the Color object
        """
        color = {
            "Obj": {
                "@N": "Value",
                "@RefId": ObjectTypes.get_random_ref_id(),
                "MS": {
                    "S": {"@N": "T", "#text": "System.ConsoleColor"},
                    "I32": {"@N": "V", "#text": color}
                }
            }
        }
        return color

    @staticmethod
    def create_ps_thread_option():
        """
        [MS-PSRP] v16.0 2016-07-14
        2.2.3.6 PSThreadOptions

        This data type represents thread options for an application or a
        higher-layer protocol on the server.


        :return: dict of the PSThreadOption object
        """
        object_ref_id = ObjectTypes.get_random_ref_id()
        ps_thread_options = {
            "Obj": {
                "@N": "PSThreadOptions",
                "@RefId": object_ref_id,
                "TN": {
                    "@RefId": ObjectTypes.get_random_ref_id(),
                    "T": [
                        "System.Management.Automation.Runspaces.PSThreadOptions"
                        "System.Enum"
                        "System.ValueType"
                        "System.Object"
                    ]
                },
                "ToString": "Default",
                "I32": object_ref_id
            }
        }
        return ps_thread_options

    @staticmethod
    def create_apartment_state():
        """
        [MS-PSRP] v16.0 2016-07-14
        2.2.3.7 ApartmentState

        This data type represents the apartment state of an application or
        higher-layer protocol build on top of the PowerShell Remoting
        Protocol.

        :return: dict of the ApartmentState object
        """
        object_ref_id = ObjectTypes.get_random_ref_id()
        apartment_state = {
            "Obj": {
                "@N": "ApartmentState",
                "@RefId": object_ref_id,
                "TN": {
                    "@RefId": ObjectTypes.get_random_ref_id(),
                    "T": [
                        "System.Threading.ApartmentState",
                        "System.Enum",
                        "System.ValueType",
                        "System.Object"
                    ]
                },
                "ToString": "MTA",
                "I32": object_ref_id
            }
        }
        return apartment_state

    @staticmethod
    def create_host_info():
        """
        [MS-PSRP] v16.0 2016-07-14
        2.2.3.14 HostInfo

        This data type represents host information

        :return: dict of the HostInfo object
        """
        host_info = {
            "Obj": {
                "@N": "HostInfo",
                "@RefId": ObjectTypes.get_random_ref_id(),
                "MS": {
                    "Obj": {
                        "@N": "_hostDefaultData",
                        "@RefId": ObjectTypes.get_random_ref_id(),
                        "MS": {
                            "Obj": {
                                "@N": "data",
                                "@RefId": ObjectTypes.get_random_ref_id(),
                                "TN": {
                                    "@RefId": ObjectTypes.get_random_ref_id(),
                                    "T": ["System.Collections.Hashtable", "System.Object"]
                                },
                                "DCT": {
                                    "EN": [
                                        {
                                            "I32": { "@N": "Key", "#text": "0"},
                                            "Obj": ObjectTypes.create_color(PsrpColor.GRAY)["Obj"]
                                        }, {
                                            "I32": {"@N": "Key", "#text": "1"},
                                            "Obj": ObjectTypes.create_color(PsrpColor.BLUE)["Obj"]
                                        }, {
                                            "I32": {"@N": "Key", "#text": "2"},
                                            "Obj": ObjectTypes.create_coordinate("0", "4")["Obj"]
                                        }, {
                                            "I32": {"@N": "Key", "#text": "3"},
                                            "Obj": ObjectTypes.create_coordinate("0", "0")["Obj"]
                                        }, {
                                            "I32": {"@N": "Key", "#text": "4"},
                                            "Obj": {
                                                "@N": "Value",
                                                "@RefId": ObjectTypes.get_random_ref_id(),
                                                "MS": {
                                                    "S": {"@N": "T", "#text": "System.Int32"},
                                                    "I32": {"@N": "V", "#text": "25"}
                                                }
                                            }
                                        }, {
                                            "I32": {"@N": "Key", "#text": "5"},
                                            "Obj": ObjectTypes.create_size("120", "3000")["Obj"]
                                        }, {
                                            "I32": {"@N": "Key", "#text": "6"},
                                            "Obj": ObjectTypes.create_size("120", "79")["Obj"]
                                        }, {
                                            "I32": {"@N": "Key", "#text": "7"},
                                            "Obj": ObjectTypes.create_size("120", "98")["Obj"]
                                        }, {
                                            "I32": {"@N": "Key", "#text": "8"},
                                            "Obj": ObjectTypes.create_size("181", "98")["Obj"]
                                        }, {
                                            "I32": {"@N": "Key", "#text": "9"},
                                            "Obj": {
                                                "@N": "Value",
                                                "@RefId": ObjectTypes.get_random_ref_id(),
                                                "MS": {
                                                    "S": [
                                                        {"@N": "T", "#text": "System.String"},
                                                        {"@N": "V", "#text": "Pywinrm PSRP"}
                                                    ]
                                                }
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    },
                    "B": [
                        {"@N": "_isHostNull", "#text": "false"},
                        {"@N": "_isHostUINull", "#text": "false"},
                        {"@N": "_isHostRawUINull", "#text": "false"},
                        {"@N": "_useRunspaceHost", "#text": "false"},
                    ]
                }
            }
        }
        return host_info

    @staticmethod
    def get_random_ref_id():
        return str(uuid.uuid4().int & (1<<32)-1)


class SessionCapability(object):
    def __init__(self):
        """
        [MS-PSRP] v16.0 2016-07-14
        2.2.2.1 SESSION_CAPABILITY Message

        Session capability
        Direction: Bidirectional
        Target: RunspacePool
        """
        self.message_type = 0x00010002
        self.initialised = False

    def create_message_data(self, ps_version, protocol_version, serialization_version):
        self.ps_version = ps_version
        self.protocol_version = protocol_version
        self.serialization_version = serialization_version

        message_data = {
            "Obj": {
                "@RefId": ObjectTypes.get_random_ref_id(),
                "MS": {
                    "Version": [
                        {"@N": "PSVersion", "#text": ps_version},
                        {"@N": "protocolversion", "#text": protocol_version},
                        {"@N": "SerializationVersion", "#text": serialization_version},
                    ]
                }
            }
        }
        message_xml = xmltodict.unparse(message_data, full_document=False)
        # TODO: Add timezone support
        self.initialised = True

        return message_xml.encode()

    def parse_message_data(self, xml):
        if self.initialised:
            raise Exception("Cannot parse message data on an already initialised object")

        message_data = xmltodict.parse(xml)
        version_values = message_data["Obj"]["MS"]["Version"]

        if len(version_values) != 3:
            raise Exception("Expecting 3 version properties in SESSION_CAPAIBLITY, actual: %d" % len(version_values))

        for version in version_values:
            attribute_value = version['@N']
            if attribute_value == 'PSVersion':
                self.ps_version = version['#text']
            elif attribute_value == 'protocolversion':
                self.protocol_version = version['#text']
            elif attribute_value == 'SerializationVersion':
                self.serialization_version = version['#text']
            else:
                raise Exception("Invalid attribute value '%s'" % attribute_value)


class InitRunspacePool(object):
    def __init__(self):
        """
        [MS-PSRP] v16.0 2016-07-14
        2.2.2.2 INIT_RUNSPACEPOOL Message

        Initialize RunspacePool
        Direction: Client to Server
        Target: RunspacePool
        """
        self.message_type = 0x00010004

    def create_message_data(self, min_runspaces, max_runspaces):
        self.min_runspaces = min_runspaces
        self.max_runspaces = max_runspaces
        self.ps_thread_options = ObjectTypes.create_ps_thread_option()
        self.apartment_state = ObjectTypes.create_apartment_state()
        self.host_info = ObjectTypes.create_host_info()
        self.application_arguments = None

        message_data = {
            "Obj": {
                "@RefId": ObjectTypes.get_random_ref_id(),
                "MS": {
                    "I32": [
                        {"@N": "MinRunspaces", "#text": min_runspaces},
                        {"@N": "MaxRunspaces", "#text": max_runspaces}
                    ],
                    "Obj": [
                        self.ps_thread_options["Obj"],
                        self.apartment_state["Obj"],
                        self.host_info["Obj"]
                    ],
                    "Nil": {"@N": "ApplicationArguments"}
                }
            }
        }
        message_xml = xmltodict.unparse(message_data, full_document=False)

        return message_xml.encode()


class RunspaceState(object):
    def __init__(self):
        """
        [MS-PSRP] v16.0 2016-07-14
        2.2.2.9 RUNSPACEPOOL_STATE Message

        State information of a RunspacePool
        Direction: Server to Client
        Target: RunspacePool
        """
        self.message_type = 0x00021005

    def parse_message_data(self, xml):
        message_data = xmltodict.parse(xml)
        raw_state = message_data["Obj"]["MS"]["I32"]
        attribute = raw_state["@N"]
        raw_value = raw_state["#text"]

        if attribute != 'RunspaceState':
            raise Exception("Invalid RUNSPACE_STATE message from the server")

        actual_state = None
        for key, value in PsrpRunspacePoolState.__dict__.items():
            if value == raw_value:
                actual_state = key

        if actual_state is None:
            raise Exception("Invalid RunspacePoolState value of %s" % raw_value)
        self.state = raw_value
        self.friendly_state = actual_state


class ApplicationPrivateData(object):
    def __init__(self):
        """
        [MS-PSRP] v16.0 2016-07-14
        2.2.2.13 APPLICATION_PRIVATE_DATA Message

        Data private to the application using the Powershell Remoting Protocol
        on the server and client, which is passed by the protocol without
        interruption
        Direction: Server to Client
        Target: RunspacePool
        """
        self.message_type = 0x00021009

    def parse_message_data(self, xml):
        message_data = xmltodict.parse(xml)
        try:
            self.bash_version = message_data["Obj"]["MS"]["Obj"]["DCT"]["En"]["Obj"]["DCT"]["En"]["Version"]["#text"]
        except TypeError:
            raise Exception("Invalid APPLICATION_PRIVATE_DATA message from the server")
