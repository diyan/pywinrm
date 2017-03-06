import re
import uuid
import xmltodict

from winrm.contants import WsmvConstant, WsmvResourceURI, WsmvAction, WsmvSignal, PsrpMessageType, PsrpRunspacePoolState, PsrpConstant, PsrpPSInvocationState
from winrm.exceptions import WinRMError, WinRMTransportError, WinRMOperationTimeoutError

from winrm.wsmv.objects import WsmvObject
from winrm.wsmv.protocol import WsmvProtocol

from winrm.psrp.response_reader import Reader
from winrm.psrp.fragmenter import Fragment, Fragmenter, Defragmenter
from winrm.psrp.messages import CreatePipeline, SessionCapability, InitRunspacePool, Message, RunspacePoolState, PipelineState

class PsrpProtocol(object):
    PS_VERSION = "2.0"
    PROTOCOL_VERSION = "2.3"
    SERIALIZATION_VERSION = "1.1.0.1"

    def __init__(self,
            transport,
            read_timeout_sec=WsmvConstant.DEFAULT_READ_TIMEOUT_SEC,
            operation_timeout_sec=WsmvConstant.DEFAULT_OPERATION_TIMEOUT_SEC,
            locale=WsmvConstant.DEFAULT_LOCALE,
            encoding=WsmvConstant.DEFAULT_ENCODING,
            min_runspaces=1,
            max_runspaces=1):

        self.wsmv_protocol = WsmvProtocol(transport, read_timeout_sec, operation_timeout_sec, locale, encoding)
        self.max_envelope_size = self.wsmv_protocol.max_envelope_size
        self.fragmenter = Fragmenter(self.wsmv_protocol)
        self.min_runspaces = min_runspaces
        self.max_runspaces = max_runspaces

        self.state = PsrpRunspacePoolState.BEFORE_OPEN
        self.shell_id = str(uuid.uuid4()).upper()
        self.rpid = uuid.uuid4()

    def create(self):
        self.state = PsrpRunspacePoolState.OPENING
        session_capability = SessionCapability(self.PS_VERSION, self.PROTOCOL_VERSION, self.SERIALIZATION_VERSION)
        init_runspace_pool = InitRunspacePool(str(self.min_runspaces), str(self.max_runspaces))

        sc = Message(Message.DESTINATION_SERVER, PsrpMessageType.SESSION_CAPABILITY, self.rpid, uuid.UUID(WsmvConstant.EMPTY_UUID), session_capability)
        init_pool = Message(Message.DESTINATION_SERVER, PsrpMessageType.INIT_RUNSPACEPOOL, self.rpid, uuid.UUID(WsmvConstant.EMPTY_UUID), init_runspace_pool)

        fragments = self.fragmenter.fragment_messages([sc, init_pool])

        for fragment in fragments:
            open_content = {
                'creationXml': {
                    '@xmlns': 'http://schemas.microsoft.com/powershell',
                    '#text': fragment
                }
            }
            shell_body = WsmvObject.shell(shell_id=self.shell_id, input_streams='stdin pr', output_streams='stdout', open_content=open_content)
            option_set = {
                'protocolversion': '2.2'
            }
            self.wsmv_protocol.send(WsmvAction.CREATE, WsmvResourceURI.SHELL_POWERSHELL, body=shell_body, option_set=option_set)

        self.runspace_pool_state = PsrpRunspacePoolState.NEGOTIATION_SENT
        receive_body = WsmvObject.receive('stdout')
        option_set = {
            'WSMAN_CMDSHELL_OPTION_KEEPALIVE': 'TRUE'
        }

        selector_set = {
            'ShellId': self.shell_id
        }
        defragmenter = Defragmenter()

        while self.runspace_pool_state != PsrpRunspacePoolState.OPENED:
            receive_responses = self.wsmv_protocol.send(WsmvAction.RECEIVE, WsmvResourceURI.SHELL_POWERSHELL, receive_body, selector_set, option_set)
            streams = receive_responses['s:Envelope']['s:Body']['rsp:ReceiveResponse']['rsp:Stream']
            messages = []
            if isinstance(streams, list):
                for stream in streams:
                    messages.append(defragmenter.defragment_message(stream['#text']))
            else:
                messages.append(defragmenter.defragment_message(streams['#text']))

            for message in messages:
                if isinstance(message, Message):
                    message_type = message.message_type
                    if message_type == PsrpMessageType.SESSION_CAPABILITY:
                        self.runspace_pool_state = PsrpRunspacePoolState.NEGOTIATION_SUCCEEDED
                        session_capability = SessionCapability.parse_message_data(message)
                        # Check the PS Version and adjust the max envelope size accordingly
                        if self.wsmv_protocol.max_envelope_size == WsmvConstant.DEFAULT_MAX_ENVELOPE_SIZE:
                            if session_capability.protocol_version > '2.1':
                                self.wsmv_protocol.max_envelope_size = 512000
                            else:
                                self.wsmv_protocol.max_envelope_size = 153600
                    elif message_type == PsrpMessageType.RUNSPACEPOOL_STATE:
                        runspace_state = RunspacePoolState.parse_message_data(message)
                        self.runspace_pool_state = runspace_state.state

        self.runspace_pool_state = PsrpRunspacePoolState.OPENED

    def close(self):
        selector_set = {
            'ShellId': self.shell_id
        }
        self.wsmv_protocol.send(WsmvAction.DELETE, WsmvResourceURI.SHELL_POWERSHELL, selector_set=selector_set)


class Pipeline(object):
    def __init__(self, rpid, shell_id, fragmenter, wsmv_protocol):
        self.rpid = rpid
        self.pid = uuid.uuid4()
        self.shell_id = shell_id
        self.command_id = str(uuid.uuid4()).upper()
        self.state = PsrpPSInvocationState.NOT_STARTED

        self.fragmenter = fragmenter
        self.wsmv_protocol = wsmv_protocol

    def create(self, command):
        command += "\r\nif (!$?) { if($LASTEXITCODE) { exit 10 } else { exit 1 } }"
        create_pipeline = Message(Message.DESTINATION_SERVER, PsrpMessageType.CREATE_PIPELINE, self.rpid, self.pid,
                                  CreatePipeline(command))

        fragments = self.fragmenter.fragment_messages(create_pipeline)
        body = WsmvObject.command_line('Invoke-Expression', fragments[0].decode(), self.command_id)
        response = self.wsmv_protocol.send(WsmvAction.COMMAND, WsmvResourceURI.SHELL_POWERSHELL,
                                           body=body, selector_set={'ShellId': self.shell_id})
        self.state = PsrpPSInvocationState.RUNNING

        # Send first fragment using the Command message
        command_id = response['s:Envelope']['s:Body']['rsp:CommandResponse']['rsp:CommandId']

        # Send the remaining fragments using the Send message
        for idx, fragment in enumerate(fragments):
            if idx != 0:
                body = WsmvObject.send('stdin', command_id, fragment[idx])
                self.wsmv_protocol.send(WsmvAction.SEND, WsmvResourceURI.SHELL_POWERSHELL, body=body,
                                        selector_set={'ShellId': self.shell_id})

    def get_output(self):
        defragmenter = Defragmenter()
        reader = Reader()
        body = WsmvObject.receive('stdout', self.command_id)

        while self.state == PsrpPSInvocationState.RUNNING:
            response = self.wsmv_protocol.send(WsmvAction.RECEIVE, WsmvResourceURI.SHELL_POWERSHELL,
                                               body=body, selector_set={'ShellId': self.shell_id})

            streams = response['s:Envelope']['s:Body']['rsp:ReceiveResponse']['rsp:Stream']
            if isinstance(streams, dict):
                streams = [streams]
            for stream in streams:
                raw_text = stream['#text']
                message = defragmenter.defragment_message(raw_text)

                # If it is None we don't have the full fragments, wait until we get more
                if message is not None:
                    reader.parse_receive_response(message)
                    self.state = reader.state

        output = {
            'stdout': b'\n'.join(reader.stdout_buffer),
            'stderr': b'\n'.join(reader.error_buffer),
            'output': b'\n'.join(reader.output_buffer),
            'verbose': b'\n'.join(reader.verbose_buffer),
            'debug': b'\n'.join(reader.debug_buffer),
            'error': b'\n'.join(reader.error_buffer),
            'warning': b'\n'.join(reader.warning_buffer),
            'return_code': int(reader.return_code)
        }

        self.close()

        return output

    def close(self):
        body = WsmvObject.signal(WsmvSignal.TERMINATE, self.command_id)
        selector_set = {
            'ShellId': self.shell_id
        }
        self.wsmv_protocol.send(WsmvAction.SIGNAL, WsmvResourceURI.SHELL_POWERSHELL, body=body,
                                selector_set=selector_set)
