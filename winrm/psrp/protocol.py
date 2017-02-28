import uuid
import xmltodict

from winrm.contants import WsmvConstant, WsmvResourceURI, WsmvAction, PsrpMessageType, PsrpRunspacePoolState
from winrm.exceptions import WinRMError, WinRMTransportError, WinRMOperationTimeoutError

from winrm.wsmv.objects import WsmvObject
from winrm.wsmv.protocol import WsmvProtocol

from winrm.psrp.fragmenter import Fragmenter
from winrm.psrp.messages import SessionCapability, InitRunspacePool, Message

class PsrpProtocol(object):
    def __init__(
            self, transport,
            read_timeout_sec=WsmvConstant.DEFAULT_READ_TIMEOUT_SEC,
            operation_timeout_sec=WsmvConstant.DEFAULT_OPERATION_TIMEOUT_SEC,
            locale=WsmvConstant.DEFAULT_LOCALE,
            encoding=WsmvConstant.DEFAULT_ENCODING):

        self.wsmv_protocol = WsmvProtocol(transport, read_timeout_sec, operation_timeout_sec, locale, encoding)
        self.max_envelope_size = self.wsmv_protocol.max_envelope_size
        self.fragmenter = Fragmenter(self.wsmv_protocol)
        self.runspace_pool_state = PsrpRunspacePoolState.BEFORE_OPEN

    def create_runspace_pool(self):
        self.runspace_pool_state = PsrpRunspacePoolState.OPENING
        session_capability = SessionCapability()
        session_capability_msg = session_capability.create_message_data("2.2", "2.0", "1.1.0.1")

        init_runspace_pool = InitRunspacePool()
        init_runspace_pool_msg= init_runspace_pool.create_message_data("1", "2")

        sc_msg = Message()
        sc = sc_msg.create_message(Message.DESTINATION_SERVER, PsrpMessageType.SESSION_CAPABILITY, uuid.uuid4(), uuid.uuid4(), session_capability_msg)

        init_pool_msg = Message()
        init_pool = init_pool_msg.create_message(Message.DESTINATION_SERVER, PsrpMessageType.INIT_RUNSPACEPOOL, uuid.uuid4(), uuid.uuid4(), init_runspace_pool_msg)

        fragments = self.fragmenter.fragment_messages([sc, init_pool])

        for fragment in fragments:
            open_content = {
                'creationXml': {
                    '@xmlns': 'http://schemas.microsoft.com/powershell',
                    '#text': fragment
                }
            }
            shell_body = WsmvObject.shell(shell_id=uuid.uuid4(), input_streams='pr', output_streams='stdout', open_content=open_content, max_envelope_size=self.max_envelope_size)
            option_set = {
                'protocolversion': '2.2'
            }
            res = self.wsmv_protocol.send(WsmvAction.CREATE, WsmvResourceURI.SHELL_POWERSHELL, body=shell_body, option_set=option_set)
            shell_id = res['s:Envelope']['s:Body']['rsp:Shell']['rsp:ShellId']

        self.runspace_pool_state = PsrpRunspacePoolState.NEGOTIATION_SENT
        receive_body = WsmvObject.receive('stdout')
        option_set = {
            'WSMAN_CMDSHELL_OPTION_KEEPALIVE': 'TRUE'
        }

        selector_set = {
            'ShellId': shell_id
        }

        while self.runspace_pool_state != PsrpRunspacePoolState.OPENED:
            a = ''
            receive_response = self.wsmv_protocol.send(WsmvAction.RECEIVE, WsmvResourceURI.SHELL_POWERSHELL, receive_body, selector_set, option_set)
            b = ''

        # Expect a session capability message

        self.runspace_pool_state = PsrpRunspacePoolState.NEGOTIATION_SUCCEEDED

        # Expect private data

        # Expect RUNSPACEPOOL_STATE

        self.runspace_pool_state = PsrpRunspacePoolState.OPENED

        # runspace is opened

        a = ''

