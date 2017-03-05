import re
import uuid
import xmltodict

from winrm.contants import WsmvConstant, WsmvResourceURI, WsmvAction, PsrpMessageType, PsrpRunspacePoolState, PsrpConstant, PsrpPSInvocationState
from winrm.exceptions import WinRMError, WinRMTransportError, WinRMOperationTimeoutError

from winrm.wsmv.objects import WsmvObject
from winrm.wsmv.protocol import WsmvProtocol

from winrm.psrp.fragmenter import Fragment, Fragmenter, Defragmenter
from winrm.psrp.messages import CreatePipeline, SessionCapability, InitRunspacePool, Message, RunspacePoolState, PipelineState

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
        self.defragmenter = Defragmenter()
        self.runspace_pool_state = PsrpRunspacePoolState.BEFORE_OPEN
        self.pipeline_state = PsrpPSInvocationState.NOT_STARTED
        self.rpid = uuid.uuid4() # For each unique runspace
        self.pid = uuid.uuid4() # For each unique pipeline

    def create_runspace_pool(self):
        self.runspace_pool_state = PsrpRunspacePoolState.OPENING
        session_capability = SessionCapability("2.0", "2.2", "1.1.0.1")
        init_runspace_pool = InitRunspacePool("1", "1")

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
            shell_id = str(uuid.uuid4()).upper()
            shell_body = WsmvObject.shell(shell_id=shell_id, input_streams='stdin pr', output_streams='stdout', open_content=open_content)
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
            'ShellId': shell_id
        }

        while self.runspace_pool_state != PsrpRunspacePoolState.OPENED:
            receive_responses = self.wsmv_protocol.send(WsmvAction.RECEIVE, WsmvResourceURI.SHELL_POWERSHELL, receive_body, selector_set, option_set)
            streams = receive_responses['s:Envelope']['s:Body']['rsp:ReceiveResponse']['rsp:Stream']
            messages = []
            if isinstance(streams, list):
                for stream in streams:
                    messages.append(self.defragmenter.defragment_message(stream['#text']))
            else:
                messages.append(self.defragmenter.defragment_message(streams['#text']))

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

        return shell_id

    def run_command(self, shell_id, command):
        command += "\r\nif (!$?) { if($LASTEXITCODE) { exit $LASTEXITCODE } else { exit 1 } }"
        command_id = str(uuid.uuid4()).upper()
        create_pipeline = CreatePipeline(command)
        cp = Message(Message.DESTINATION_SERVER, PsrpMessageType.CREATE_PIPELINE, self.rpid, self.pid,
                     create_pipeline)
        fragments = self.fragmenter.fragment_messages([cp])

        # Send first fragment using the Command message
        selector_set = {'ShellId': shell_id}
        body = WsmvObject.command_line('Invoke-Expression', fragments[0].decode(), command_id)
        res = self.wsmv_protocol.send(WsmvAction.COMMAND, WsmvResourceURI.SHELL_POWERSHELL, body=body,
                                      selector_set=selector_set)
        command_id = res['s:Envelope']['s:Body']['rsp:CommandResponse']['rsp:CommandId']

        for idx, fragment in enumerate(fragments):
            if idx != 0:
                # Send the remaining fragments using the Send message
                body = WsmvObject.send('stdin', command_id, fragment[idx])
                self.wsmv_protocol.send(WsmvAction.SEND, WsmvResourceURI.SHELL_POWERSHELL, body=body, selector_set=selector_set)

        self.pipeline_state = PsrpPSInvocationState.RUNNING
        return command_id

    def get_command_output(self, shell_id, command_id):
        stdout_buffer = []
        stderr_buffer = []
        output_buffer = []
        verbose_buffer = []
        debug_buffer = []
        error_buffer = []
        warning_buffer = []
        return_code = -1
        body = WsmvObject.receive('stdout', command_id)
        selector_set = {
            'ShellId': shell_id
        }

        while self.pipeline_state == PsrpPSInvocationState.RUNNING:
            res = self.wsmv_protocol.send(WsmvAction.RECEIVE, WsmvResourceURI.SHELL_POWERSHELL, body=body,
                                          selector_set=selector_set)

            receive_response = res['s:Envelope']['s:Body']['rsp:ReceiveResponse']
            streams = receive_response['rsp:Stream']
            if isinstance(streams, dict):
                streams = [streams]

            for stream_node in streams:
                raw_text = stream_node['#text']
                stream_type = stream_node['@Name']
                message = self.defragmenter.defragment_message(raw_text)

                # If it is None we don't have the full fragments, wait until we get more
                if message is not None:
                    message_type = message.message_type

                    if message_type == PsrpMessageType.PIPELINE_STATE:
                        pipeline_state = PipelineState.parse_message_data(message)
                        self.pipeline_state = pipeline_state.state
                        if pipeline_state.exception_as_error_record:
                            error_buffer.append(pipeline_state.exception_as_error_record.encode())
                    elif message_type == PsrpMessageType.PIPELINE_OUTPUT:
                        output = message.data['S']
                        if output:
                            output_buffer.append(message.data['S'].encode())
                            stdout_buffer.append(message.data['S'].encode())
                    elif message_type == PsrpMessageType.ERROR_RECORD:
                        error = self._parse_error_message(message.data)
                        error_buffer.append(error)
                        stderr_buffer.append(error)
                    elif message_type == PsrpMessageType.DEBUG_RECORD:
                        debug_buffer.append(message.data['Obj']['ToString'].encode())
                    elif message_type == PsrpMessageType.VERBOSE_RECORD:
                        verbose_buffer.append(message.data['Obj']['ToString'].encode())
                    elif message_type == PsrpMessageType.WARNING_RECORD:
                        warning_buffer.append(message.data['Obj']['ToString'].encode())
                    elif message_type == PsrpMessageType.PIPELINE_HOST_CALL:
                        stdout_buffer.append(self._parse_host_call(message.data))
                    else:
                        a = ''



            command_state_info = receive_response['rsp:CommandState']
            if command_state_info['@State'] == 'http://schemas.microsoft.com/wbem/wsman/1/windows/shell/CommandState/Done':
                return_code = command_state_info['rsp:ExitCode']

        output = {
            'stdout': b'\n'.join(stdout_buffer),
            'stderr': b'\n'.join(stderr_buffer),
            'output': b'\n'.join(output_buffer),
            'verbose': b'\n'.join(verbose_buffer),
            'debug': b'\n'.join(debug_buffer),
            'error': b'\n'.join(error_buffer),
            'warning': b'\n'.join(warning_buffer),
            'return_code': int(return_code)
        }

        return output

    def _parse_host_call(self, message_data):
        raw_output = message_data['Obj']['MS']['Obj']
        full_output = b''
        method_identifier = ''
        for raw in raw_output:
            if raw['@N'] == 'mi':
                method_identifier = raw['ToString']
            else:
                output_list = raw['LST']
                if isinstance(output_list, dict):
                    output_list = [output_list]

                if method_identifier != 'SetShouldExit' and method_identifier != 'WriteProgress':
                    for output in output_list:
                        full_output += output['S'].encode()

        if method_identifier == 'WriteDebugLine':
            full_output = b'DEBUG: %s' % full_output
        elif method_identifier == 'WriteWarningLine':
            full_output = b'WARNING: %s' % full_output
        elif method_identifier == 'WriteVerboseLine':
            full_output = b'VERBOSE: %s' % full_output
        else:
            a = ''

        return full_output

    def _parse_error_message(self, message_data):
        error_message = message_data['Obj']['ToString']

        my_command = ''
        error_category_message = ''
        position_message = ''
        fully_qualified_error_id = ''

        for error_info in message_data['Obj']['MS']['S']:
            if error_info['@N'] == 'FullyQualifiedErrorId':
                fully_qualified_error_id = error_info['#text']
            elif error_info['@N'] == 'ErrorCategory_Message':
                error_category_message = error_info['#text']

        for error_info in message_data['Obj']['MS']['Obj']:
            if error_info['@N'] == 'InvocationInfo':
                invocation_info = error_info['Props']['S']
                for info in invocation_info:
                    if info['@N'] == 'PositionMessage':
                        position_message = info['#text']
                    elif info['@N'] == 'MyCommand':
                        my_command = info['#text']

        error_string = """%s : %s
%s
    + CategoryInfo          : %s
    + FullyQualifiedErrorId : %s
""" % (my_command, error_message, position_message, error_category_message, fully_qualified_error_id)

        pattern = '_x([0-9A-F]*)_'
        hex_strings = re.findall(pattern, error_string, re.I)
        for hex_string in hex_strings:
            error_string = error_string.replace("_x%s_" % hex_string, chr(int(hex_string, 16)))

        return error_string.encode()
