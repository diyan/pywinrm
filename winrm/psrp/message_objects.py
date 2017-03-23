import struct
import uuid
import xmltodict

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from winrm.client import get_value_of_attribute
from winrm.contants import PsrpRunspacePoolState, PsrpPSInvocationState, PsrpColor, PsrpMessageType
from winrm.exceptions import WinRMError


class Message(object):
    DESTINATION_CLIENT = 0x00000001
    DESTINATION_SERVER = 0x00000002
    BYTE_ORDER_MARK = b'\xef\xbb\xbf'

    def __init__(self, destination, rpid, pid, message):
        self.destination = destination
        self.message_type = message.message_type
        self.rpid = rpid
        self.pid = pid
        self.data = message.create_message_data()

    def create_message(self):
        message = struct.pack("<I", self.destination)
        message += struct.pack("<I", self.message_type)
        message += self.rpid.bytes
        message += self.pid.bytes
        if self.data != "":
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

        return Message(destination, rpid, pid, PrimitiveMessage(message_type, data))


class PsrpObject(object):
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
        coordinate = OrderedDict([
            ("Obj", OrderedDict([
                ("@N", "Value"),
                ("@RefId", PsrpObject.get_random_ref_id()),
                ("MS", OrderedDict([
                    ("S", {"@N": "T", "#text": "System.Management.Automation.Host.Coordinates"}),
                    ("Obj", OrderedDict([
                        ("@N", "V"),
                        ("@RefId", PsrpObject.get_random_ref_id()),
                        ("MS", {"I32": [{"@N": "x", "#text": x}, {"@N": "y", "#text": y}]})
                    ]))
                ]))
            ]))
        ])

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
        size = OrderedDict([
            ("Obj", OrderedDict([
                ("@N", "Value"),
                ("@RefId", PsrpObject.get_random_ref_id()),
                ("MS", OrderedDict([
                    ("S", {"@N": "T", "#text": "System.Management.Automation.Host.Size"}),
                    ("Obj", OrderedDict([
                        ("@N", "V"),
                        ("@RefId", PsrpObject.get_random_ref_id()),
                        ("MS", {"I32": [{"@N": "width", "#text": width}, {"@N": "height", "#text": height}]})
                    ]))
                ]))
            ]))
        ])
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
        color = OrderedDict([
            ("Obj", OrderedDict([
                ("@N", "Value"),
                ("@RefId", PsrpObject.get_random_ref_id()),
                ("MS", OrderedDict([
                    ("S", {"@N": "T", "#text": "System.ConsoleColor"}),
                    ("I32", {"@N": "V", "#text": color})
                ]))
            ]))
        ])
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
        ps_thread_options = OrderedDict([
            ("Obj", OrderedDict([
                ("@N", "PSThreadOptions"),
                ("@RefId", PsrpObject.get_random_ref_id()),
                ("TN", OrderedDict([
                    ("@RefId", PsrpObject.get_random_ref_id()),
                    ("T", [
                        "System.Management.Automation.Runspaces.PSThreadOptions",
                        "System.Enum",
                        "System.ValueType",
                        "System.Object"
                    ])
                ])),
                ("ToString", "Default"),
                ("I32", "0")
            ]))
        ])
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
        apartment_state = OrderedDict([
            ("Obj", OrderedDict([
                ("@N", "ApartmentState"),
                ("@RefId", PsrpObject.get_random_ref_id()),
                ("TN", OrderedDict([
                    ("@RefId", PsrpObject.get_random_ref_id()),
                    ("T", [
                        "System.Threading.ApartmentState",
                        "System.Enum",
                        "System.ValueType",
                        "System.Object"
                    ])
                ])),
                ("ToString", "Unknown"),
                ("I32", "2")
            ]))
        ])
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
        remote_stream_options = OrderedDict([
            ("Obj", OrderedDict([
                ("@N", "RemoteStreamOptions"),
                ("@RefId", PsrpObject.get_random_ref_id()),
                ("TN", OrderedDict([
                    ("@RefId", PsrpObject.get_random_ref_id()),
                    ("T", [
                        "System.Management.Automation.RemoteStreamOptions",
                        "System.Enum",
                        "System.ValueType",
                        "System.Object"
                    ])
                ])),
                ("ToString", "0"),
                ("I32", "0")
            ]))
        ])
        return remote_stream_options

    @staticmethod
    def create_pipeline(commands):
        """
        [MS-PSRP] v16.0 2016-07-14
        2.2.3.11 Pipeline

        This data type represents a pipeline to be executed

        :param commands: A list of commands created by create_command you wish to run
        :return: dict of the Pipeline object
        """
        pipeline = OrderedDict([
            ("Obj", OrderedDict([
                ("@N", "PowerShell"),
                ("@RefId", PsrpObject.get_random_ref_id()),
                ("MS", OrderedDict([
                    ("Obj", OrderedDict([
                        ("@N", "Cmds"),
                        ("@RefId", PsrpObject.get_random_ref_id()),
                        ("TN", OrderedDict([
                            ("@RefId", PsrpObject.get_random_ref_id()),
                            ("T", [
                                "System.Collections.Generic.List`1[[System.Management.Automation.PSObject, System.Management.Automation, Version=3.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35]]",
                                "System.Object"
                            ])
                        ])),
                        ("LST", {"Obj": []})
                    ])),
                    ("B", [
                        {"@N": "IsNested", "#text": "false"},
                        {"@N": "RedirectShellErrorOutputPipe", "#text": "true"}
                    ]),
                    ("Nil", {"@N": "History"})
                ]))
            ]))
        ])
        for command in commands:
            pipeline['Obj']['MS']['Obj']['LST']['Obj'].append(command['Obj'])

        return pipeline

    @staticmethod
    def create_command(command, parameters=()):
        """
        [MS-PSRP] v16.0 2016-07-14
        2.2.3.12 Command

        This data type represents a command in a pipeline

        :param command: The command you wish to run
        :param parameters: A list of parameters to run with the command, must be in the format -Key Value
        :return: dict of the Command object
        """
        merge_reference_id = PsrpObject.get_random_ref_id()
        arguments = []
        for parameter in parameters:
            if parameter.startswith('-'):
                parameter_split = parameter.split(' ', 1)
                arguments.append(OrderedDict([
                    ("@RefId", PsrpObject.get_random_ref_id()),
                    ("MS", OrderedDict([
                        ("S", {"@N": "N", "#text": parameter_split[0]}),
                        ("Nil", {"@N": "V"})

                    ]))
                ]))
                if len(parameter_split) > 1:
                    arguments.append(OrderedDict([
                        ("@RefId", PsrpObject.get_random_ref_id()),
                        ("MS", OrderedDict([
                            ("Nil", {"@N": "N"}),
                            ("S", {"@N": "V", "#text": parameter_split[1]})
                        ]))
                    ]))
            else:
                arguments.append(OrderedDict([
                    ("@RefId", PsrpObject.get_random_ref_id()),
                    ("MS", OrderedDict([
                        ("Nil", {"@N": "N"}),
                        ("S", {"@N": "V", "#text": parameter})
                    ]))
                ]))

        args_element = OrderedDict([
            ("@N", "Args"),
            ("@RefId", PsrpObject.get_random_ref_id()),
            ("TN", OrderedDict([
                ("@RefId", PsrpObject.get_random_ref_id()),
                ("T", [
                    "System.Collections.Generic.List`1[[System.Management.Automation.PSObject, System.Management.Automation, Version=3.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35]]",
                    "System.Object"
                ])
            ])),
            ("LST", {})
        ])
        if len(arguments) > 0:
            args_element['LST'] = {'Obj': arguments}
            is_script = "false"
        else:
            is_script = "true"

        command_dict = OrderedDict([
            ("Obj", OrderedDict([
                ("@RefId", PsrpObject.get_random_ref_id()),
                ("MS", OrderedDict([
                    ("S", {"@N": "Cmd", "#text": command}),
                    ("B", {"@N": "IsScript","#text": is_script}),
                    ("Nil", {"@N": "UseLocalScope"}),
                    ("Obj", [
                        OrderedDict([
                            ("@N", "MergeMyResult"),
                            ("@RefId", PsrpObject.get_random_ref_id()),
                            ("TN", OrderedDict([
                                ("@RefId", merge_reference_id),
                                ("T", [
                                    "System.Management.Automation.Runspaces.PipelineResultTypes",
                                    "System.Enum",
                                    "System.ValueType",
                                    "System.Object"
                                ])
                            ])),
                            ("ToString", "None"),
                            ("I32", "0")
                        ]), OrderedDict([
                            ("@N", "MergeToResult"),
                            ("@RefId", PsrpObject.get_random_ref_id()),
                            ("TNRef", {"@RefId": merge_reference_id}),
                            ("ToString", "None"),
                            ("I32", "0")
                        ]), OrderedDict([
                            ("@N", "MergePreviousResults"),
                            ("@RefId", PsrpObject.get_random_ref_id()),
                            ("TNRef", {"@RefId": merge_reference_id}),
                            ("ToString", "None"),
                            ("I32", "0")
                        ]), OrderedDict([
                            ("@N", "MergeError"),
                            ("@RefId", PsrpObject.get_random_ref_id()),
                            ("TNRef", {"@RefId": merge_reference_id}),
                            ("ToString", "None"),
                            ("I32", "0")
                        ]), OrderedDict([
                            ("@N", "MergeWarning"),
                            ("@RefId", PsrpObject.get_random_ref_id()),
                            ("TNRef", {"@RefId": merge_reference_id}),
                            ("ToString", "None"),
                            ("I32", "0")
                        ]), OrderedDict([
                            ("@N", "MergeVerbose"),
                            ("@RefId", PsrpObject.get_random_ref_id()),
                            ("TNRef", {"@RefId": merge_reference_id}),
                            ("ToString", "None"),
                            ("I32", "0")
                        ]), OrderedDict([
                            ("@N", "MergeDebug"),
                            ("@RefId", PsrpObject.get_random_ref_id()),
                            ("TNRef", {"@RefId": merge_reference_id}),
                            ("ToString", "None"),
                            ("I32", "0")
                        ]), args_element
                    ])
                ]))
            ]))
        ])

        return command_dict

    @staticmethod
    def create_host_info():
        """
        [MS-PSRP] v16.0 2016-07-14
        2.2.3.14 HostInfo

        This data type represents host information

        :return: dict of the HostInfo object
        """
        host_info = OrderedDict([
            ("Obj", OrderedDict([
                ("@N", "HostInfo"),
                ("@RefId", PsrpObject.get_random_ref_id()),
                ("MS", OrderedDict([
                    ("Obj", OrderedDict([
                        ("@N", "_hostDefaultData"),
                        ("@RefId", PsrpObject.get_random_ref_id()),
                        ("MS", OrderedDict([
                            ("Obj", OrderedDict([
                                ("@N", "data"),
                                ("@RefId", PsrpObject.get_random_ref_id()),
                                ("TN", OrderedDict([
                                    ("@RefId", PsrpObject.get_random_ref_id()),
                                    ("T", ["System.Collections.Hashtable", "System.Object"])
                                ])),
                                ("DCT", OrderedDict([
                                    ("En", [
                                        OrderedDict([
                                            ("I32", {"@N": "Key", "#text": "0"}),
                                            ("Obj", PsrpObject.create_color(PsrpColor.GRAY)["Obj"])
                                        ]),
                                        OrderedDict([
                                            ("I32", {"@N": "Key", "#text": "1"}),
                                            ("Obj", PsrpObject.create_color(PsrpColor.BLUE)["Obj"])
                                        ]),
                                        OrderedDict([
                                            ("I32", {"@N": "Key", "#text": "2"}),
                                            ("Obj", PsrpObject.create_coordinate("0", "4")["Obj"])
                                        ]),
                                        OrderedDict([
                                            ("I32", {"@N": "Key", "#text": "3"}),
                                            ("Obj", PsrpObject.create_coordinate("0", "0")["Obj"])
                                        ]),
                                        OrderedDict([
                                            ("I32", {"@N": "Key", "#text": "4"}),
                                            ("Obj", OrderedDict([
                                                ("@N", "Value"),
                                                ("@RefId", PsrpObject.get_random_ref_id()),
                                                ("MS", OrderedDict([
                                                    ("S", {"@N": "T", "#text": "System.Int32"}),
                                                    ("I32", {"@N": "V", "#text": "25"})
                                                ]))
                                            ]))
                                        ]),
                                        OrderedDict([
                                            ("I32", {"@N": "Key", "#text": "5"}),
                                            ("Obj", PsrpObject.create_size("120", "3000")["Obj"])
                                        ]),
                                        OrderedDict([
                                            ("I32", {"@N": "Key", "#text": "6"}),
                                            ("Obj", PsrpObject.create_size("120", "79")["Obj"])
                                        ]),
                                        OrderedDict([
                                            ("I32", {"@N": "Key", "#text": "7"}),
                                            ("Obj", PsrpObject.create_size("120", "98")["Obj"])
                                        ]),
                                        OrderedDict([
                                            ("I32", {"@N": "Key", "#text": "8"}),
                                            ("Obj", PsrpObject.create_size("181", "98")["Obj"])
                                        ]),
                                        OrderedDict([
                                            ("I32", {"@N": "Key", "#text": "9"}),
                                            ("Obj", OrderedDict([
                                                ("@N", "Value"),
                                                ("@RefId", PsrpObject.get_random_ref_id()),
                                                ("MS", OrderedDict([
                                                    ("S", [
                                                        {"@N": "T", "#text": "System.String"},
                                                        {"@N": "V", "#text": "Pywinrm PSRP"}
                                                    ])
                                                ]))
                                            ]))
                                        ])
                                    ])
                                ]))
                            ]))
                        ]))
                    ])),
                    ("B", [
                        {"@N": "_isHostNull", "#text": "false"},
                        {"@N": "_isHostUINull", "#text": "false"},
                        {"@N": "_isHostRawUINull", "#text": "false"},
                        {"@N": "_useRunspaceHost", "#text": "false"}
                    ])
                ]))
            ]))
        ])
        return host_info

    @staticmethod
    def create_host_method_identifier(method_type, method_id):
        """
        [MS-PSRP] v16.0 2016-07-14
        2.2.3.17 Host Method Identifier

        This data type represents a method to be executed on a host

        :param method_type: The name of the method
        :param method_id: The ID of the method
        :return: dict of the Host Method Identifier object
        """
        host_method_identifier = OrderedDict([
            ("Obj", OrderedDict([
                ("@RefId", PsrpObject.get_random_ref_id()),
                ("@N", "mi"),
                ("TN", OrderedDict([
                    ("@RefId", PsrpObject.get_random_ref_id()),
                    ("T", [
                        "System.Management.Automation.Remoting.RemoteHostMethodId",
                        "System.Enum",
                        "System.ValueType",
                        "System.Object"
                    ])
                ])),
                ("ToString", method_type),
                ("I32", method_id)
            ]))
        ])
        return host_method_identifier

    @staticmethod
    def get_random_ref_id():
        return str(uuid.uuid4().int & (1<<32)-1)


class PrimitiveMessage(object):

    def __init__(self, message_type, data):
        """
        Used as a primitive object when parsing messages from the server

        :param type: The message type
        :param data: The raw message dict
        """
        self.message_type = message_type
        self.data = data

    def create_message_data(self):
        return self.data


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
        message_data = OrderedDict([
            ("Obj", OrderedDict([
                ("@RefId", PsrpObject.get_random_ref_id()),
                ("MS", OrderedDict([
                    ("Version", [
                        {"@N": "PSVersion", "#text": self.ps_version},
                        {"@N": "protocolversion", "#text": self.protocol_version},
                        {"@N": "SerializationVersion", "#text": self.serialization_version}
                    ])
                ]))
            ]))
        ])
        # TODO: Add timezone support

        return message_data

    @staticmethod
    def parse_message_data(message):
        version_values = message.data["Obj"]["MS"]["Version"]

        if len(version_values) != 3:
            raise WinRMError("Expecting 3 version properties in SESSION_CAPAIBLITY, actual: %d" % len(version_values))

        ps_version = get_value_of_attribute(version_values, "N", "PSVersion", "#text")
        protocol_version = get_value_of_attribute(version_values, "N", "protocolversion", "#text")
        serialization_version = get_value_of_attribute(version_values, "N", "SerializationVersion", "#text")

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
        self.ps_thread_options = PsrpObject.create_ps_thread_option()
        self.apartment_state = PsrpObject.create_apartment_state()
        self.host_info = PsrpObject.create_host_info()
        self.application_arguments = None

    def create_message_data(self):
        message_data = OrderedDict([
            ("Obj", OrderedDict([
                ("@RefId", PsrpObject.get_random_ref_id()),
                ("MS", OrderedDict([
                    ("I32", [
                        {"@N": "MinRunspaces", "#text": self.min_runspaces},
                        {"@N": "MaxRunspaces", "#text": self.max_runspaces}
                    ]),
                    ("Obj", [
                        self.ps_thread_options["Obj"],
                        self.apartment_state["Obj"],
                        self.host_info["Obj"]
                    ]),
                    ("Nil", {"@N": "ApplicationArguments"})
                ]))
            ]))
        ])

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
            raise WinRMError("Invalid RUNSPACE_STATE message from the server")

        friendly_state = None
        for key, value in PsrpRunspacePoolState.__dict__.items():
            if value == state:
                friendly_state = key

        if friendly_state is None:
            raise WinRMError("Invalid RunspacePoolState value of %s" % state)

        return RunspacePoolState(state, friendly_state)


class CreatePipeline(object):
    def __init__(self, commands, no_input):
        """
        [MS-PSRP] v16.0 2016-07-14
        2.2.2.10 CREATE_PIPELINE Message

        Create a command pipeline and invoke it in the specified RunspacePool
        Direction: Client to Server
        Target: RunspacePool

        @param commands: A list of commands created by create_command you wish to run
        """
        self.message_type = PsrpMessageType.CREATE_PIPELINE

        self.no_input = no_input
        self.apartment_state = PsrpObject.create_apartment_state()
        self.remote_stream_options = PsrpObject.create_remote_stream_options()
        self.add_to_history = True
        self.host_info = PsrpObject.create_host_info()
        self.power_shell = PsrpObject.create_pipeline(commands)
        self.is_nested = False

    def create_message_data(self):
        message_data = OrderedDict([
            ("Obj", OrderedDict([
                ("@RefId", PsrpObject.get_random_ref_id()),
                ("MS", OrderedDict([
                    ("B", [
                        {"@N": "NoInput", "#text": str(self.no_input).lower()},
                        {"@N": "AddToHistory", "#text": str(self.add_to_history).lower()},
                        {"@N": "IsNested", "#text": str(self.is_nested).lower()}
                    ]),
                    ("Obj", [
                        self.apartment_state["Obj"],
                        self.remote_stream_options["Obj"],
                        self.host_info["Obj"],
                        self.power_shell["Obj"]
                    ])
                ]))
            ]))
        ])

        return message_data


class ApplicationPrivateData(object):
    def __init__(self, application_info):
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
        self.application_info = application_info

    @staticmethod
    def parse_message_data(message):
        try:
            raw_info = message.data["Obj"]["MS"]["Obj"]["DCT"]["En"]
            application_info = ApplicationPrivateData.parse_raw_application_raw_data(raw_info)
        except KeyError:
            raise WinRMError("Invalid APPLICATION_PRIVATE_DATA message from the server")

        return ApplicationPrivateData(application_info)

    @staticmethod
    def parse_raw_application_raw_data(raw_info):
        application_info = {}
        if isinstance(raw_info, dict):
            raw_info = [raw_info]
        for info in raw_info:
            key = None
            value = None

            for node in info:
                child_node = info[node]
                raw_key = get_value_of_attribute(child_node, 'N', 'Key', '#text')
                if raw_key:
                    key = raw_key
                raw_value = get_value_of_attribute(child_node, 'N', 'Value')
                if raw_value:
                    if '#text' in raw_value.keys():
                        value = raw_value['#text']
                    elif 'DCT' in raw_value.keys():
                        value = ApplicationPrivateData.parse_raw_application_raw_data(raw_value['DCT']['En'])
                    elif 'LST' in raw_value.keys():
                        value_key = next(iter(raw_value['LST']))
                        value = raw_value['LST'][value_key]
            if key:
                application_info[key] = value

        return application_info


class PipelineInput(object):

    def __init__(self, input):
        """
        [MS-PSRP] v16.0 2016-07-14
        2.2.2.17 PIPELINE_INPUT Message

        Input to a command pipeline on the server

        Direction: Client to Server
        Target: pipeline
        """
        self.message_type = PsrpMessageType.PIPELINE_INPUT
        self.input = input

    def create_message_data(self):
        message_data = {
            "S": self.input
        }

        return message_data


class EndOfPipelineInput(object):

    def __init__(self):
        """
        [MS-PSRP] v16.0 2016-07-14
        2.2.2.18 END_OF_PIPELINE_INPUT Message

        Close the input collection for the command pipeline on the server.

        Direction: Client to Server
        Target: pipeline
        """
        self.message_type = PsrpMessageType.END_OF_PIPELINE_INPUT

    def create_message_data(self):
        return ""


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


class PipelineHostResponse(object):

    def __init__(self, call_id, method_id, method_type, prompt_key, response):
        """
        [MS-PSRP] v16.0 2016-07-14
        2.2.2.28 PIPELINE_HOST_RESPONSE Message

        Response from a host call executed on the client's host

        Direction: Client to Server
        Target: pipeline
        """
        self.message_type = PsrpMessageType.PIPELINE_HOST_RESPONSE
        self.call_id = call_id
        self.method_identifier = PsrpObject.create_host_method_identifier(method_type, method_id)
        self.prompt_key = prompt_key
        self.response = response

    def create_message_data(self):
        message_data = OrderedDict([
            ("Obj", OrderedDict([
                ("@RefId", PsrpObject.get_random_ref_id()),
                ("MS", OrderedDict([
                    ("Obj", [
                        OrderedDict([
                            ("@RefId", PsrpObject.get_random_ref_id()),
                            ("@N", "mr"),
                            ("TN", OrderedDict([
                                ("@RefId", PsrpObject.get_random_ref_id()),
                                ("T", [
                                    "System.Collections.Hashtable",
                                    "System.Object"
                                ])
                            ])),
                            ("DCT", OrderedDict([
                                ("En", OrderedDict([
                                    ("S", [
                                        {"@N": "Key", "#text": self.prompt_key},
                                        {"@N": "Value", "#text": self.response}
                                    ])
                                ]))
                            ]))
                        ]),
                        self.method_identifier['Obj']
                    ]),
                    ("I64", {"@N": "ci", "#text": self.call_id})
                ]))
            ]))
        ])

        return message_data
