import uuid

class RunspaceStates(object):
    """
    [MS-PSRP] v16.0 2016-07-14
    2.2.3.4 RunspacePoolState

    This data type represents the state of a RunspacePool. This data type is a
    signed int with the following allowed values

    XML Element: <I32>
    Example: <I32>-2147483648</I32>
    """
    BEFORE_OPEN             = 0
    OPENING                 = 1
    OPENED                  = 2
    CLOSED                  = 3
    CLOSING                 = 4
    BROKEN                  = 5
    NEGOTIATION_SENT        = 6
    NEGOTIATION_SUCCEEDED   = 7
    CONNECTING              = 8
    DISCONNECTED            = 9

class GlobalData(object):
    """
    [MS-PSRP] v16.0 2016-07-14
    3.1.1.1 Global Data
    """

    def __init__(self):
        self.runspace_pools = {}
        self.pipelines = {}
        self.public_key_pair = None

class RunspacePool(object):
    def __init__(self):
        """
        [MS-PSRP] v16.0 2016-07-14
        3.1.1.2 RunspacePool Data
        """
        self.guid = None
        self.state = None

    def create_runspace(self):
        if self.state is None:
            raise Exception("Cannot create new runspace when state has been initialiased {0}".format(self.state))

        # Assign a new GUID and set the state to OPENING
        self.guid = uuid.uuid4()
        self.state = RunspaceStates.OPENING