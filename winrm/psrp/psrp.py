import logging
import uuid

from winrm.client import Client
from winrm.contants import WsmvConstant, WsmvResourceURI, WsmvAction, WsmvSignal, \
    PsrpMessageType, PsrpRunspacePoolState, PsrpPSInvocationState, PsrpConstant
from winrm.exceptions import WinRMError, WinRMTransportError

from winrm.wsmv.message_objects import WsmvObject

from winrm.psrp.response_reader import Reader
from winrm.psrp.fragmenter import Fragmenter, Defragmenter
from winrm.psrp.message_objects import CreatePipeline, SessionCapability, InitRunspacePool, Message, \
    RunspacePoolState, PsrpObject, PipelineHostResponse, ApplicationPrivateData, PipelineInput, EndOfPipelineInput

log = logging.getLogger(__name__)


class PsrpClient(Client):
    def __init__(self,
                 transport_opts,
                 operation_timeout_sec=WsmvConstant.DEFAULT_OPERATION_TIMEOUT_SEC,
                 locale=WsmvConstant.DEFAULT_LOCALE,
                 encoding=WsmvConstant.DEFAULT_ENCODING,
                 max_envelope_size=WsmvConstant.DEFAULT_MAX_ENVELOPE_SIZE,
                 min_runspaces=PsrpConstant.DEFAULT_MIN_RUNSPACES,
                 max_runspaces=PsrpConstant.DEFAULT_MAX_RUNSPACES
                 ):
        """
        Will set up a handler used to interact with the PSRP protocol

        :param transport_opts: See winrm.client Client() for more info
        :param int operation_timeout_sec: See winrm.client Client() for more info
        :param string locale: See winrm.client Client() for more info
        :param string encoding: See winrm.client Client() for more info
        :param int max_envelope_size: See winrm.client Client() for more info
        :param int min_runspaces: The minimum amount of runspaces to create on the server (default 1)
        :param int max_runspaces: The maximum amount of runspaces to create on the server (default 1)
        """
        Client.__init__(self, transport_opts, operation_timeout_sec, locale, encoding, max_envelope_size,
                        WsmvResourceURI.SHELL_POWERSHELL)
        self.min_runspaces = min_runspaces
        self.max_runspaces = max_runspaces
        self.fragmenter = Fragmenter(self)

        self.state = PsrpRunspacePoolState.BEFORE_OPEN
        self.rpid = uuid.uuid4()
        self.pipelines = []
        self.application_private_data = None

    def open_shell(self,
                   ps_version=PsrpConstant.DEFAULT_PS_VERSION,
                   protocol_version=PsrpConstant.DEFAULT_PROTOCOL_VERSION,
                   serialization_version=PsrpConstant.DEFAULT_SERIALIZATION_VERSION
                   ):
        # Will create a new RunspacePool and Shell on the server.
        self.state = PsrpRunspacePoolState.OPENING
        session_capability = SessionCapability(ps_version, protocol_version, serialization_version)
        init_runspace_pool = InitRunspacePool(str(self.min_runspaces), str(self.max_runspaces))

        sc = Message(Message.DESTINATION_SERVER, self.rpid,
                     uuid.UUID(WsmvConstant.EMPTY_UUID), session_capability)
        init_pool = Message(Message.DESTINATION_SERVER, self.rpid,
                            uuid.UUID(WsmvConstant.EMPTY_UUID), init_runspace_pool)

        fragments = self.fragmenter.fragment_messages([sc, init_pool])
        # Send the first fragment using the WSMV Create message
        open_content = {
            'creationXml': {
                '@xmlns': 'http://schemas.microsoft.com/powershell',
                '#text': fragments[0]
            }
        }
        body = WsmvObject.shell(shell_id=self.shell_id, input_streams='stdin pr', output_streams='stdout',
                                      open_content=open_content)
        option_set = {
            'protocolversion': protocol_version
        }
        a = self.send(WsmvAction.CREATE, body=body, option_set=option_set)
        self.state = PsrpRunspacePoolState.NEGOTIATION_SENT

        self._wait_for_open_pool()

    def run_command(self, command, parameters=(), responses=(), no_input=True):
        """
        Will run a command in a new pipeline on the RunspacePool. It will first
        check to see if the pool will accept a new runspace/pipeline based on
        the max_runspaces setting.

        :param command: A PS command or script to run
        :param parameters: If using a PS command, this contains a list of parameter key value pairs to run with the command
        :param responses: A list of optional responses to pass onto the script when prompted. Useful for scripts that doesn't handle input parameters
        :param no_input: Whether the command takes in pipeline input sent with the send_input method before retrieving the message output
        :return winrm.psrp.response_reader.Reader() object containing the powershell output streams
        """
        if self.state != PsrpRunspacePoolState.OPENED:
            raise WinRMError("Cannot execute command pipeline as the RunspacePool State is not Opened")

        running_pipelines = 0
        for pipeline in self.pipelines:
            # Check if the pipeline is running
            if pipeline.state == PsrpPSInvocationState.FAILED:
                running = False
            elif pipeline.state == PsrpPSInvocationState.STOPPED:
                running = False
            else:
                running = True

            if running:
                running_pipelines += 1

        if running_pipelines >= self.max_runspaces:
            raise WinRMError(
                "Cannot create new command pipeline as Runspace Pool already has %d running, max allowed %d" % (
                running_pipelines, self.max_runspaces))

        pipeline = Pipeline(self)
        self.pipelines.append(pipeline)
        pipeline.create(command, parameters, responses, no_input)

        return pipeline.command_id

    def send_input(self, command_id, input):
        """
        If the pipeline accepts input, this can be called multiple times for
        sending pipeline input

        :param command_id: The command_id for the pipeline to send input to
        :param input: A string of the input to send
        """
        pipeline = self._find_pipeline_by_command_id(command_id)
        pipeline.send_input(input)

    def get_command_output(self, command_id):
        """
        Will retrieve the output information for the command_id specified.

        :param command_id: THe command_id for the pipeline to get the output info
        :return: A Reader class containing the command output information
        """
        pipeline = self._find_pipeline_by_command_id(command_id)
        try:
            output = pipeline.get_output()
        finally:
            pipeline.stop()

        return output

    def close_shell(self):
        """
        Will close the RunspacePool and all pipelines that are currently
        running in that pool. Once this action is processed no more commands
        can be placed to this RunspacePool.
        """
        if self.state != PsrpRunspacePoolState.CLOSED:
            for pipeline in self.pipelines:
                pipeline.stop()

            selector_set = {
                'ShellId': self.shell_id
            }
            self.send(WsmvAction.DELETE, selector_set=selector_set)
            self.state = PsrpRunspacePoolState.CLOSED

    def _wait_for_open_pool(self):
        """
        Once the RunspacePool shell is created this will wait until the pool
        is opened for additional commands
        """
        receive_body = WsmvObject.receive('stdout')
        option_set = {
            'WSMAN_CMDSHELL_OPTION_KEEPALIVE': 'TRUE'
        }

        selector_set = {
            'ShellId': self.shell_id
        }
        defragmenter = Defragmenter()

        while self.state != PsrpRunspacePoolState.OPENED:
            body = self.send(WsmvAction.RECEIVE, body=receive_body, selector_set=selector_set, option_set=option_set)

            streams = body['s:Envelope']['s:Body']['rsp:ReceiveResponse']['rsp:Stream']
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
                        self.state = PsrpRunspacePoolState.NEGOTIATION_SUCCEEDED
                        session_capability = SessionCapability.parse_message_data(message)
                        self._set_max_envelope_size(session_capability.protocol_version)
                    elif message_type == PsrpMessageType.RUNSPACEPOOL_STATE:
                        runspace_state = RunspacePoolState.parse_message_data(message)
                        self.state = runspace_state.state
                        if runspace_state == PsrpRunspacePoolState.BROKEN or \
                                        runspace_state == PsrpRunspacePoolState.CLOSED:
                            raise WinRMError("Failed to initialised a PSRP Runspace Pool, state set to %s"
                                             % runspace_state.friendly_state)
                    elif message_type == PsrpMessageType.APPLICATION_PRIVATE_DATA:
                        application_private_data = ApplicationPrivateData.parse_message_data(message)
                        self.application_private_data = application_private_data.application_info
                        log.debug("Retrieved server application private data: %s" % str(self.application_private_data))

        log.debug("PSRP RunspacePool created: Shell ID: %s, Resource URI: %s" % (self.shell_id, self.resource_uri))

    def _set_max_envelope_size(self, server_protocol_version):
        """
        When initially checking the max envelope size it can fail when the user
        does not have admin permissions. In this case we use the default size
        for older WinRM protocol versions. This method will use the protocol
        version returned by the server to determine if we can increase the
        max envelope size if it is still set to the Pywinrm default

        :param server_protocol_version: The protocol version returned by the server in a SESSION_CAPABILITY message
        """
        current_envelope_size = self.server_config['max_envelope_size']
        if current_envelope_size == WsmvConstant.DEFAULT_MAX_ENVELOPE_SIZE:
             if server_protocol_version > '2.1':
                self.server_config['max_envelope_size'] = 512000

    def _find_pipeline_by_command_id(self, command_id):
        pipeline = None
        for iter_pipeline in self.pipelines:
            if iter_pipeline.command_id == command_id:
                pipeline = iter_pipeline
                break

        if not pipeline:
            raise WinRMError("Cannot find pipeline that matches command_id %s" % command_id)

        return pipeline


class Pipeline(object):
    def __init__(self, client):
        """
        A pipeline object that can run a command in the RunspacePool. Each
        pipeline can only run 1 command before it needs to be closed. You can
        run multiple pipelines in a RunspacePool but if max_runspaces has been
        set to a number > 1 than there is no guarantee it will keep the same
        values set by a previous pipeline

        :param client: The class of PsrpClient used to send messages to the server
        """
        self.client = client
        self.pid = uuid.uuid4()
        self.command_id = str(uuid.uuid4()).upper()
        self.state = PsrpPSInvocationState.NOT_STARTED
        self.responses = []
        self.current_response_count = 0
        self.no_input = True

    def create(self, command, parameters, responses, no_input=True):
        """
        Will create a command pipeline to run on the server

        :param command: A PS command or script to run
        :param parameters: If using a PS command, this contains a list of parameter key value pairs to run with the command
        :param responses: A list of optional responses to pass onto the script when prompted. Useful for scripts that doesn't handle input parameters
        :param no_input: Whether the pipeline does not accept input or not
        """
        self.responses = responses
        self.current_response_count = 0
        self.no_input = no_input
        commands = [PsrpObject.create_command(command, parameters)]

        # We pipe the resulting command to a string so PSRP doesn't return a complex object
        commands.append(PsrpObject.create_command('Out-String', ['-Stream']))
        create_pipeline = Message(Message.DESTINATION_SERVER, self.client.rpid,
                                  self.pid, CreatePipeline(commands, self.no_input))

        fragments = self.client.fragmenter.fragment_messages(create_pipeline)
        body = WsmvObject.command_line('', fragments[0].decode(), self.command_id)
        response = self.client.send(WsmvAction.COMMAND, body=body, selector_set={'ShellId': self.client.shell_id})
        self.state = PsrpPSInvocationState.RUNNING

        # Send first fragment using the Command message
        command_id = response['s:Envelope']['s:Body']['rsp:CommandResponse']['rsp:CommandId']

        # Send the remaining fragments using the Send message
        for idx, fragment in enumerate(fragments):
            if idx != 0:
                body = WsmvObject.send('stdin', fragments[idx], command_id=command_id)
                self.client.send(WsmvAction.SEND, body=body, selector_set={'ShellId': self.client.shell_id})

    def send_input(self, input):
        """
        Can be used to send the input to a pipeline before we retrieve the output

        :param input: A string to send as an input to the pipeline
        """
        pipeline_input = Message(Message.DESTINATION_SERVER, self.client.rpid,
                                 self.pid, PipelineInput(input))
        fragments = self.client.fragmenter.fragment_messages(pipeline_input)
        for fragment in fragments:
            body = WsmvObject.send('stdin', fragment.decode(), self.command_id)
            self.client.send(WsmvAction.SEND, body=body, selector_set={'ShellId': self.client.shell_id})

    def get_output(self):
        """
        Will extract the command output from the server into a Reader()
        object. This object can be used to extra information from the various
        Powershell streams.

        Once the information has been retrieved the pipeline will be stopped

        :return: winrm.psrp.response_reader.Reader() object containing the powershell streams
        """
        defragmenter = Defragmenter()
        reader = Reader(self._input_callback)

        if not self.no_input:
            # Once we have sent everything to the pipeline we need to tell it we have finalised it
            end_of_pipeline_input = Message(Message.DESTINATION_SERVER, self.client.rpid,
                                            self.pid, EndOfPipelineInput())
            fragments = self.client.fragmenter.fragment_messages(end_of_pipeline_input)
            body = WsmvObject.send('stdin', fragments[0].decode(), self.command_id)
            self.client.send(WsmvAction.SEND, body=body, selector_set={'ShellId': self.client.shell_id})

        body = WsmvObject.receive('stdout', self.command_id)
        while self.state == PsrpPSInvocationState.RUNNING:
            response = self.client.send(WsmvAction.RECEIVE, body=body, selector_set={'ShellId': self.client.shell_id})

            streams = response['s:Envelope']['s:Body']['rsp:ReceiveResponse'].get('rsp:Stream', [])
            if isinstance(streams, dict):
                streams = [streams]
            for stream in streams:
                raw_text = stream['#text']
                message = defragmenter.defragment_message(raw_text)

                # If it is None we don't have the full fragments, wait until we get more
                if message is not None:
                    new_state = reader.parse_receive_response(message)
                    if new_state:
                        self.state = new_state

        self.stop()

        return reader

    def _input_callback(self, method_identifier, name, type):
        """
        Will take in the input request and pass in the pre-set input responses
        passed in when we started the command. If the response count is less than
        the responses required, a WinRMError will fire

        :param method_identifier: The method identifier ID retrieved from the host call request message
        :param name: The name of the input retrieved from the host call request message
        :param type: The method identifier text retrieved from the host call request message
        """
        responses = self.responses
        if len(responses) < self.current_response_count + 1:
            raise WinRMError("Expecting response index at %d but only "
                             "%d responses have been pre-set" % (self.current_response_count + 1, len(responses)))

        current_response = self.responses[self.current_response_count]
        self.current_response_count += 1

        input_message = Message(Message.DESTINATION_SERVER, self.client.rpid,
                                self.pid, PipelineHostResponse(str(self.current_response_count), method_identifier, type, name, current_response))
        fragments = self.client.fragmenter.fragment_messages(input_message)
        selector_set = {"ShellId": self.client.shell_id}
        for fragment in fragments:
            body = WsmvObject.send('pr', fragment, self.command_id)
            self.client.send(WsmvAction.SEND, body=body, selector_set=selector_set)

    def stop(self):
        # Will stop the pipeline if it has not been stopped already
        if self.state != PsrpPSInvocationState.STOPPED and self.state != PsrpPSInvocationState.FAILED:
            self.state = PsrpPSInvocationState.STOPPING
            body = WsmvObject.signal(WsmvSignal.TERMINATE, self.command_id)
            selector_set = {
                'ShellId': self.client.shell_id
            }
            try:
                self.client.send(WsmvAction.SIGNAL, body=body, selector_set=selector_set)
                self.state = PsrpPSInvocationState.STOPPED
            except WinRMTransportError:
                self.state = PsrpPSInvocationState.FAILED
