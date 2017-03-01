class WsmvConstant(object):
    EMPTY_UUID = '00000000-0000-0000-0000-000000000000'
    DEFAULT_ENCODING = 'utf-8'
    DEFAULT_OPERATION_TIMEOUT_SEC = 20
    DEFAULT_READ_TIMEOUT_SEC = DEFAULT_OPERATION_TIMEOUT_SEC + 10
    DEFAULT_LOCALE = 'en-US'
    DEFAULT_MAX_ENVELOPE_SIZE = 153600

    # [MS-WSMV] v30.0 2016-07-14 2.2.1 Namespaces
    NAMESPACES = {
        "s": "http://www.w3.org/2003/05/soap-envelope",
        "xs": "http://www.w3.org/2001/XMLSchema",
        "xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "a": "http://schemas.xmlsoap.org/ws/2004/08/addressing",
        "w": "http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd",
        "wsmid": "http://schemas.dmtf.org/wbem/wsman/identify/1/wsmanidentity.xsd",
        "wsmanfault": "http://schemas.microsoft.com/wbem/wsman/1/wsmanfault",
        "cim": "http://schemas.dmtf.org/wbem/wscim/1/common",
        "p": "http://schemas.microsoft.com/wbem/wsman/1/wsman.xsd",
        "cfg": "http://schemas.microsoft.com/wbem/wsman/1/config",
        "sub": "http://schemas.microsoft.com/wbem/wsman/1/subscription",
        "rsp": "http://schemas.microsoft.com/wbem/wsman/1/windows/shell",
        "m": "http://schemas.microsoft.com/wbem/wsman/1/machineid",
        "cert": "http://schemas.microsoft.com/wbem/wsman/1/config/service/certmapping",
        "plugin": "http://schemas.microsoft.com/wbem/wsman/1/config/PluginConfiguration",
        "wsen": "http://schemas.xmlsoap.org/ws/2004/09/enumeration",
        "wsdl": "http://schemas.xmlsoap.org/wsdl",
        "wsp": "http://schemas.xmlsoap.org/ws/2004/09/policy",
        "wse": "http://schemas.xmlsoap.org/ws/2004/08/eventing",
        "i": "http://schemas.microsoft.com/wbem/wsman/1/cim/interactive.xsd"
    }

class WsmvAction(object):
    GET = 'http://schemas.xmlsoap.org/ws/2004/09/transfer/Get'
    PUT = 'http://schemas.xmlsoap.org/ws/2004/09/transfer/Put'
    DELETE = 'http://schemas.xmlsoap.org/ws/2004/09/transfer/Delete'
    CREATE = 'http://schemas.xmlsoap.org/ws/2004/09/transfer/Create'
    SUBSCRIBE = 'http://schemas.xmlsoap.org/ws/2004/08/eventing/Subscribe'
    UNSUBSCRIBE = 'http://schemas.xmlsoap.org/ws/2004/08/eventing/Unsubscribe'
    ENUMERATE = 'http://schemas.xmlsoap.org/ws/2004/09/enumeration/Enumerate'
    PULL = 'http://schemas.xmlsoap.org/ws/2004/09/enumeration/Pull'
    RELEASE = 'http://schemas.xmlsoap.org/ws/2004/09/enumeration/Release'
    COMMAND = 'http://schemas.microsoft.com/wbem/wsman/1/windows/shell/Command'
    SIGNAL = 'http://schemas.microsoft.com/wbem/wsman/1/windows/shell/Signal'
    SEND = 'http://schemas.microsoft.com/wbem/wsman/1/windows/shell/Send'
    RECEIVE = 'http://schemas.microsoft.com/wbem/wsman/1/windows/shell/Receive'
    DISCONNECT = 'http://schemas.microsoft.com/wbem/wsman/1/windows/shell/Disconnect'
    RECONNECT = 'http://schemas.microsoft.com/wbem/wsman/1/windows/shell/Reconnect'
    CONNECT = 'http://schemas.microsoft.com/wbem/wsman/1/windows/shell/Connect'
    ACKNOWLEDGE = 'http://schemas.microsoft.com/wbem/wsman/1/wsman/Acknowledge'
    END = 'http://schemas.microsoft.com/wbem/wsman/1/wsman/End'
    CANCEL = 'http://schemas.microsoft.com/wbem/wsman/1/wsman/Cancel'


class WsmvSignal(object):
    CTRL_BREAK = 'http://schemas.microsoft.com/wbem/wsman/1/windows/shell/signal/ctrl_break'
    CTRL_C = 'http://schemas.microsoft.com/wbem/wsman/1/windows/shell/signal/ctrl_c'
    TERMINATE = 'http://schemas.microsoft.com/wbem/wsman/1/windows/shell/signal/terminate'

class WsmvResourceURI(object):
    SHELL_CMD = 'http://schemas.microsoft.com/wbem/wsman/1/windows/shell/cmd'
    SHELL_POWERSHELL = 'http://schemas.microsoft.com/powershell/Microsoft.PowerShell'
    CONFIG = 'http://schemas.microsoft.com/wbem/wsman/1/config'


class PsrpMessageType(object):
    """
    [MS-PSRP] v16.0 2016-07-14
    2.2.1 PowerShell Remoting Protocol Message

    Valid Message types
    """
    SESSION_CAPABILITY = 0x00010002
    INIT_RUNSPACEPOOL = 0x00010004
    PUBLIC_KEY = 0x00010005
    ENCRYPTED_SESSION_KEY = 0x00010006
    PUBLIC_KEY_REQUEST = 0x00010007
    CONNECT_RUNSPACEPOOL = 0x00010008
    RUNSPACEPOOL_INIT_DATA = 0x002100B
    RESET_RUNSPACE_STATE = 0x0002100C
    SET_MAX_RUNSPACES = 0x00021002
    SET_MIN_RUNSPACES = 0x00021003
    RUNSPACE_AVAILABILITY = 0x00021004
    RUNSPACEPOOL_STATE = 0x00021005
    CREATE_PIPELINE = 0x00021006
    GET_AVAILABLE_RUNSPACES = 0x00021007
    USER_EVENT = 0x00021008
    APPLICATION_PRIVATE_DATA = 0x00021009
    GET_COMMAND_METADATA = 0x0002100A
    RUNSPACEPOOL_HOST_CALL = 0x00021100
    RUNSPACEPOOL_HOST_RESPONSE = 0x00021101
    PIPELINE_INPUT = 0x00041002
    END_OF_PIPELINE_INPUT = 0x00041003
    PIPELINE_OUTPUT = 0x00041004
    ERROR_RECORD = 0x00041005
    PIPELINE_STATE = 0x00041006
    DEBUG_RECORD = 0x00041007
    VERBOSE_RECORD = 0x00041008
    WARNING_RECORD = 0x00041009
    PROGRESS_RECORD = 0x00041010
    INFORMATION_RECORD = 0x00041011
    PIPELINE_HOST_CALL = 0x00041100
    PIPELINE_HOST_RESPONSE = 0x00041101


class PsrpColor(object):
    """
    [MS-PSRP] v16.0 2016-07-14
    2.2.3.3 Color

    Valid colors when setting up the Color object
    """
    DARK_BLUE = '1'
    DARK_GREEN = '2'
    DARK_CYAN = '3'
    DARK_RED = '4'
    DARK_MAGENTA = '5'
    DARK_YELLOW = '6'
    GRAY = '7'
    DARK_GREY = '8'
    BLUE = '9'
    GREEN = '10'
    CYAN = '11'
    RED = '12'
    MAGENTA = '13'
    YELLOW = '14'
    WHITE = '15'


class PsrpRunspacePoolState(object):
    """
    [MS-PSRP] v16.0 2016-07-14
    2.2.3.4 RunspacePoolState

    This data type represents the state of a RunspacePool
    """
    BEFORE_OPEN = "0"
    OPENING = "1"
    OPENED = "2"
    CLOSED = "3"
    CLOSING = "4"
    BROKEN = "5"
    NEGOTIATION_SENT = "6"
    NEGOTIATION_SUCCEEDED = "7"
    CONNECTING = "8"
    DISCONNECTED = "9"
