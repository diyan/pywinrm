import struct
import uuid
import xmltodict

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from winrm.contants import PsrpRunspacePoolState, PsrpPSInvocationState, PsrpColor, PsrpMessageType


class Message(object):
    DESTINATION_CLIENT = 0x00000001
    DESTINATION_SERVER = 0x00000002
    BYTE_ORDER_MARK = b'\xef\xbb\xbf'

    def __init__(self, destination, message_type, rpid, pid, data):
        self.destination = destination
        self.message_type = message_type
        self.rpid = rpid
        self.pid = pid
        if isinstance(data, dict):
            self.data = data
        else:
            self.data = data.create_message_data()

    def create_message(self):
        message = struct.pack("<I", self.destination)
        message += struct.pack("<I", self.message_type)
        message += self.rpid.bytes
        message += self.pid.bytes
        message += self.BYTE_ORDER_MARK
        message += xmltodict.unparse(self.data, full_document=False, encoding='utf-8').encode()

        return message

    @staticmethod
    def parse_message(message):
        destination = struct.unpack("<I", message[0:4])[0]
        message_type = struct.unpack("<I", message[4:8])[0]
        rpid = uuid.UUID(bytes=message[8:24])
        pid = uuid.UUID(bytes=message[24:40])
        data = xmltodict.parse(message[43:])

        return Message(destination, message_type, rpid, pid, data)

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
                        "System.Management.Automation.Runspaces.PSThreadOptions",
                        "System.Enum",
                        "System.ValueType",
                        "System.Object",
                    ]
                },
                "ToString": "Default",
                "I32": "0"
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
                "ToString": "Unknown",
                "I32": "2"
            }
        }
        return apartment_state

    @staticmethod
    def create_remote_stream_options():
        """
        [MS-PSRP] v16.0 2016-07-14
        2.2.3.8 RemoteStreamOptions

        This data type represents a set of zero or more optoins of a remote
        stream.

        :return: dict of the RemoteStreamOptions object
        """
        remote_stream_options = {
            "Obj": {
                "@N": "RemoteStreamOptions",
                "@RefId": ObjectTypes.get_random_ref_id(),
                "TN": {
                    "@RefId": ObjectTypes.get_random_ref_id(),
                    "T": [
                        "System.Management.Automation.RemoteStreamOptions",
                        "System.Enum",
                        "System.ValueType",
                        "System.Object"
                    ]
                },
                "ToString": "0",
                "I32": "0"
            }
        }
        return remote_stream_options

    @staticmethod
    def create_pipeline(command):
        """
        [MS-PSRP] v16.0 2016-07-14
        2.2.3.11 Pipeline

        This data type represents a pipeline to be executed

        :param commands: The command you wish to run
        :return: dict of the Pipeline object
        """
        command = ObjectTypes.create_command(command)
        pipeline = {
            "Obj": {
                "@N": "PowerShell",
                "@RefId": ObjectTypes.get_random_ref_id(),
                "MS": {
                    "Obj": {
                        "@N": "Cmds",
                        "@RefId": ObjectTypes.get_random_ref_id(),
                        "TN": {
                            "@RefId": ObjectTypes.get_random_ref_id(),
                            "T": [
                                "System.Collections.Generic.List`1[[System.Management.Automation.PSObject, System.Management.Automation, Version=3.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35]]",
                                "System.Object"
                            ]
                        },
                        "LST": command
                    },
                    "B": [
                        {"@N": "IsNested", "#text": "false"},
                        {"@N": "RedirectShellErrorOutputPipe", "#text": "true"}
                    ],
                    "Nil": {"@N": "History"}
                }
            }
        }
        return pipeline

    @staticmethod
    def create_command(command):
        """
        [MS-PSRP] v16.0 2016-07-14
        2.2.3.12 Command

        This data type represents a command in a pipeline

        :param command: The command you wish to run
        :return: dict of the Command object
        """
        merge_reference_id = ObjectTypes.get_random_ref_id()

        command_dict = {
            "Obj": {
                "@RefId": ObjectTypes.get_random_ref_id(),
                "MS": {
                    "S": {"@N": "Cmd", "#text": "Invoke-Expression"},
                    "B": {"@N": "IsScript","#text": "false"},
                    "Nil": {"@N": "UseLocalScope"},
                    "Obj": [
                        {
                            "@N": "MergeMyResult",
                            "@RefId": ObjectTypes.get_random_ref_id(),
                            "TN": {
                                "@RefId": merge_reference_id,
                                "T": [
                                    "System.Management.Automation.Runspaces.PipelineResultTypes",
                                    "System.Enum",
                                    "System.ValueType",
                                    "System.Object"
                                ],
                            },
                            "ToString": "None",
                            "I32": "0"
                        }, {
                            "@N": "MergeToResult",
                            "@RefId": ObjectTypes.get_random_ref_id(),
                            "TNRef": {"@RefId": merge_reference_id},
                            "ToString": "None",
                            "I32": "0"
                        }, {
                            "@N": "MergePreviousResults",
                            "@RefId": ObjectTypes.get_random_ref_id(),
                            "TNRef": {"@RefId": merge_reference_id},
                            "ToString": "None",
                            "I32": "0"
                        }, {
                            "@N": "MergeError",
                            "@RefId": ObjectTypes.get_random_ref_id(),
                            "TNRef": {"@RefId": merge_reference_id},
                            "ToString": "None",
                            "I32": "0"
                        }, {
                            "@N": "MergeWarning",
                            "@RefId": ObjectTypes.get_random_ref_id(),
                            "TNRef": {"@RefId": merge_reference_id},
                            "ToString": "None",
                            "I32": "0"
                        }, {
                            "@N": "MergeVerbose",
                            "@RefId": ObjectTypes.get_random_ref_id(),
                            "TNRef": {"@RefId": merge_reference_id},
                            "ToString": "None",
                            "I32": "0"
                        }, {
                            "@N": "MergeDebug",
                            "@RefId": ObjectTypes.get_random_ref_id(),
                            "TNRef": {"@RefId": merge_reference_id},
                            "ToString": "None",
                            "I32": "0"
                        }, {
                            "@N": "Args",
                            "@RefId": ObjectTypes.get_random_ref_id(),
                            "TN": {
                                "@RefId": ObjectTypes.get_random_ref_id(),
                                "T": [
                                    "System.Collections.Generic.List`1[[System.Management.Automation.PSObject, System.Management.Automation, Version=3.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35]]",
                                    "System.Object"
                                ]
                            },
                            "LST": {
                                "Obj": [
                                    {
                                        "@RefId": ObjectTypes.get_random_ref_id(),
                                        "MS": {
                                            "Nil": {"@N": "V"},
                                            "S": {"@N": "N", "#text": "-Command"}
                                        }
                                    }, {
                                        "@RefId": ObjectTypes.get_random_ref_id(),
                                        "MS": {
                                            "Nil": {"@N": "N"},
                                            "S": {"@N": "V", "#text": command}
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }
            }
        }
        return command_dict

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
                                    "En": [
                                        # DCT entries need to keep their order where the key is first
                                        # Using OrderedDict to do this
                                        OrderedDict([
                                            ("I32", {"@N": "Key", "#text": "0"}),
                                            ("Obj", ObjectTypes.create_color(PsrpColor.GRAY)["Obj"])
                                        ]),
                                        OrderedDict([
                                            ("I32", {"@N": "Key", "#text": "1"}),
                                            ("Obj", ObjectTypes.create_color(PsrpColor.BLUE)["Obj"])
                                        ]),
                                        OrderedDict([
                                            ("I32", {"@N": "Key", "#text": "2"}),
                                            ("Obj", ObjectTypes.create_coordinate("0", "4")["Obj"])
                                        ]),
                                        OrderedDict([
                                            ("I32", {"@N": "Key", "#text": "3"}),
                                            ("Obj", ObjectTypes.create_coordinate("0", "0")["Obj"])
                                        ]),
                                        OrderedDict([
                                            ("I32", {"@N": "Key", "#text": "4"}),
                                            ("Obj", {
                                                "@N": "Value",
                                                "@RefId": ObjectTypes.get_random_ref_id(),
                                                "MS": {
                                                    "S": {"@N": "T", "#text": "System.Int32"},
                                                    "I32": {"@N": "V", "#text": "25"}
                                                }
                                            })
                                        ]),
                                        OrderedDict([
                                            ("I32", {"@N": "Key", "#text": "5"}),
                                            ("Obj", ObjectTypes.create_size("120", "3000")["Obj"])
                                        ]),
                                        OrderedDict([
                                            ("I32", {"@N": "Key", "#text": "6"}),
                                            ("Obj", ObjectTypes.create_size("120", "79")["Obj"])
                                        ]),
                                        OrderedDict([
                                            ("I32", {"@N": "Key", "#text": "7"}),
                                            ("Obj", ObjectTypes.create_size("120", "98")["Obj"])
                                        ]),
                                        OrderedDict([
                                            ("I32", {"@N": "Key", "#text": "8"}),
                                            ("Obj", ObjectTypes.create_size("181", "98")["Obj"])
                                        ]),
                                        OrderedDict([
                                            ("I32", {"@N": "Key", "#text": "9"}),
                                            ("Obj", {
                                                "@N": "Value",
                                                "@RefId": ObjectTypes.get_random_ref_id(),
                                                "MS": {
                                                    "S": [
                                                        {"@N": "T", "#text": "System.String"},
                                                        {"@N": "V", "#text": "Pywinrm PSRP"}
                                                    ]
                                                }
                                            })
                                        ])
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
    def __init__(self, ps_version, protocol_version, serialization_version):
        """
        [MS-PSRP] v16.0 2016-07-14
        2.2.2.1 SESSION_CAPABILITY Message

        Session capability
        Direction: Bidirectional
        Target: RunspacePool
        """
        self.message_type = PsrpMessageType.SESSION_CAPABILITY

        self.ps_version = ps_version
        self.protocol_version = protocol_version
        self.serialization_version = serialization_version

    def create_message_data(self):
        message_data = {
            "Obj": {
                "@RefId": ObjectTypes.get_random_ref_id(),
                "MS": {
                    "Version": [
                        {"@N": "PSVersion", "#text": self.ps_version},
                        {"@N": "protocolversion", "#text": self.protocol_version},
                        {"@N": "SerializationVersion", "#text": self.serialization_version},
                    ]
                }
            }
        }
        # TODO: Add timezone support

        return message_data

    @staticmethod
    def parse_message_data(message):
        version_values = message.data["Obj"]["MS"]["Version"]

        if len(version_values) != 3:
            raise Exception("Expecting 3 version properties in SESSION_CAPAIBLITY, actual: %d" % len(version_values))

        ps_version = None
        protocol_version = None
        serialization_version = None
        for version in version_values:
            attribute_value = version['@N']
            if attribute_value == 'PSVersion':
                ps_version = version['#text']
            elif attribute_value == 'protocolversion':
                protocol_version = version['#text']
            elif attribute_value == 'SerializationVersion':
                serialization_version = version['#text']
            else:
                raise Exception("Invalid attribute value '%s'" % attribute_value)

        return SessionCapability(ps_version, protocol_version, serialization_version)


class InitRunspacePool(object):
    def __init__(self, min_runspaces, max_runspaces):
        """
        [MS-PSRP] v16.0 2016-07-14
        2.2.2.2 INIT_RUNSPACEPOOL Message

        Initialize RunspacePool
        Direction: Client to Server
        Target: RunspacePool
        """
        self.message_type = PsrpMessageType.INIT_RUNSPACEPOOL

        self.min_runspaces = min_runspaces
        self.max_runspaces = max_runspaces
        self.ps_thread_options = ObjectTypes.create_ps_thread_option()
        self.apartment_state = ObjectTypes.create_apartment_state()
        self.host_info = ObjectTypes.create_host_info()
        self.application_arguments = None

    def create_message_data(self):
        message_data = {
            "Obj": {
                "@RefId": ObjectTypes.get_random_ref_id(),
                "MS": {
                    "I32": [
                        {"@N": "MinRunspaces", "#text": self.min_runspaces},
                        {"@N": "MaxRunspaces", "#text": self.max_runspaces}
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

        return message_data


class RunspacePoolState(object):
    def __init__(self, state, friendly_state):
        """
        [MS-PSRP] v16.0 2016-07-14
        2.2.2.9 RUNSPACEPOOL_STATE Message

        State information of a RunspacePool
        Direction: Server to Client
        Target: RunspacePool
        """
        self.message_type = PsrpMessageType.RUNSPACEPOOL_STATE

        self.state = state
        self.friendly_state = friendly_state

    @staticmethod
    def parse_message_data(message):
        raw_state = message.data["Obj"]["MS"]["I32"]
        attribute = raw_state["@N"]
        state = raw_state["#text"]

        if attribute != 'RunspaceState':
            raise Exception("Invalid RUNSPACE_STATE message from the server")

        friendly_state = None
        for key, value in PsrpRunspacePoolState.__dict__.items():
            if value == state:
                friendly_state = key

        if friendly_state is None:
            raise Exception("Invalid RunspacePoolState value of %s" % state)

        return RunspacePoolState(state, friendly_state)


class CreatePipeline(object):
    def __init__(self, command):
        """
        [MS-PSRP] v16.0 2016-07-14
        2.2.2.10 CREATE_PIPELINE Message

        Create a command pipeline and invoke it in the specified RunspacePool
        Direction: Client to Server
        Target: RunspacePool
        """
        self.message_type = PsrpMessageType.CREATE_PIPELINE

        self.no_input = True
        self.apartment_state = ObjectTypes.create_apartment_state()
        self.remote_stream_options = ObjectTypes.create_remote_stream_options()
        self.add_to_history = True
        self.host_info = ObjectTypes.create_host_info()
        self.power_shell = ObjectTypes.create_pipeline(command)
        self.is_nested = False

    def create_message_data(self):
        message_data = {
            "Obj": {
                "@RefId": ObjectTypes.get_random_ref_id(),
                "MS": {
                    "B": [
                        {"@N": "NoInput", "#text": str(self.no_input).lower()},
                        {"@N": "AddToHistory", "#text": str(self.add_to_history).lower()},
                        {"@N": "IsNested", "#text": str(self.is_nested).lower()}
                    ],
                    "Obj": [
                        self.apartment_state["Obj"],
                        self.remote_stream_options["Obj"],
                        self.host_info["Obj"],
                        self.power_shell["Obj"]
                    ]
                }
            }
        }

        return message_data


class ApplicationPrivateData(object):
    def __init__(self, bash_version):
        """
        [MS-PSRP] v16.0 2016-07-14
        2.2.2.13 APPLICATION_PRIVATE_DATA Message

        Data private to the application using the Powershell Remoting Protocol
        on the server and client, which is passed by the protocol without
        interruption
        Direction: Server to Client
        Target: RunspacePool
        """
        self.message_type = PsrpMessageType.APPLICATION_PRIVATE_DATA

        self.bash_version = bash_version

    @staticmethod
    def parse_message_data(message):
        try:
            bash_version = message.data["Obj"]["MS"]["Obj"]["DCT"]["En"]["Obj"]["DCT"]["En"]["Version"]["#text"]
        except TypeError:
            raise Exception("Invalid APPLICATION_PRIVATE_DATA message from the server")

        return ApplicationPrivateData(bash_version)


class PipelineState(object):
    def __init__(self, state, friendly_state, exception_as_error_record):
        """
        [MS-PSRP] v16.0 2016-07-14
        2.2.2.21 PIPELINE_STATE Message

        State information of a command pipeline on the server

        Direction: Server to Client
        Target: pipeline or RunspacePool
        """
        self.message_type = PsrpMessageType.PIPELINE_STATE

        self.state = state
        self.friendly_state = friendly_state
        self.exception_as_error_record = exception_as_error_record

    @staticmethod
    def parse_message_data(message):
        state = message.data['Obj']['MS']['I32']['#text']

        friendly_state = None
        for key, value in PsrpPSInvocationState.__dict__.items():
            if value == state:
                friendly_state = key

        exception_as_error_record = message.data['Obj']['MS'].get('Obj', None)

        return PipelineState(state, friendly_state, exception_as_error_record)
