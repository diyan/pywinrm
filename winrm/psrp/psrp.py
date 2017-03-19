import uuid

from winrm.client import Client
from winrm.contants import WsmvConstant, WsmvResourceURI, WsmvAction, WsmvSignal, \
    PsrpMessageType, PsrpRunspacePoolState, PsrpPSInvocationState, PsrpConstant
from winrm.exceptions import WinRMError, WinRMTransportError

from winrm.wsmv.objects import WsmvObject

from winrm.psrp.response_reader import Reader
from winrm.psrp.fragmenter import Fragmenter, Defragmenter
from winrm.psrp.messages import CreatePipeline, SessionCapability, InitRunspacePool, Message, RunspacePoolState, ObjectTypes, PipelineInput, EndOfPipelineInput


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

        :param Transport transport: A initialised Transport() object for handling message transport
        :param int read_timeout_sec: The maximum amount of seconds to wait before a HTTP connect/read times out (default 30). This value should be slightly higher than operation_timeout_sec, as the server can block *at least* that long.
        :param int operation_timeout_sec: The maximum allows time in seconds for any single WSMan HTTP operation (default 20). Note that operation timeouts while receiving output (the only WSMan operation that should take any singificant time, and where these timeouts are expected) will be silently retried indefinitely.
        :param string locale: The locale value to use when creating a Shell on the remote host (default en-US).
        :param string encoding: The encoding format when creating XML strings to send to the server (default utf-8).
        :param int min_runspaces: The minumum amount of runspaces to create on the server (default 1)
        :param int max_runspaces: The maximum amount of runspaces to create on the server (default 1)
        :param string ps_version: The powershell version supported by pywinrm (default 2.0)
        :param string protocol_version: The remoting protocol version supported by pywinrm (default 2.3)
        :param string serialization_version: The powershell serialization version supported by pywinrm (default 1.1.0.1)
        """
        Client.__init__(self, transport_opts, operation_timeout_sec, locale, encoding, max_envelope_size,
                        WsmvResourceURI.SHELL_POWERSHELL)
        self.min_runspaces = min_runspaces
        self.max_runspaces = max_runspaces
        self.fragmenter = Fragmenter(self)

        self.state = PsrpRunspacePoolState.BEFORE_OPEN
        self.rpid = uuid.uuid4()
        self.pipelines = []

    def open_shell(self,
                   ps_version=PsrpConstant.DEFAULT_PS_VERSION,
                   protocol_version=PsrpConstant.DEFAULT_PROTOCOL_VERSION,
                   serialization_version=PsrpConstant.DEFAULT_SERIALIZATION_VERSION
                   ):
        # Will create a new RunspacePool and Shell on the server.
        self.state = PsrpRunspacePoolState.OPENING
        session_capability = SessionCapability(ps_version, protocol_version, serialization_version)
        init_runspace_pool = InitRunspacePool(str(self.min_runspaces), str(self.max_runspaces))

        sc = Message(Message.DESTINATION_SERVER, PsrpMessageType.SESSION_CAPABILITY, self.rpid,
                     uuid.UUID(WsmvConstant.EMPTY_UUID), session_capability)
        init_pool = Message(Message.DESTINATION_SERVER, PsrpMessageType.INIT_RUNSPACEPOOL, self.rpid,
                            uuid.UUID(WsmvConstant.EMPTY_UUID), init_runspace_pool)

        fragments = self.fragmenter.fragment_messages([sc, init_pool])

        for fragment in fragments:
            open_content = {
                'creationXml': {
                    '@xmlns': 'http://schemas.microsoft.com/powershell',
                    '#text': fragment
                }
            }
            body = WsmvObject.shell(shell_id=self.shell_id, input_streams='stdin pr', output_streams='stdout',
                                          open_content=open_content)
            option_set = {
                'protocolversion': protocol_version
            }
            self.send(WsmvAction.CREATE, body=body, option_set=option_set)

        self.state = PsrpRunspacePoolState.NEGOTIATION_SENT
        self._wait_for_open_pool()

    def run_command(self, command, arguments=()):
        """
        Will run a command in a new pipeline on the RunspacePool. It will first
        check to see if the pool will accept a new runspace/pipeline based on
        the max_runspaces setting.

        :param command: The command or script to run
        :return winrm.psrp.response_reader.Reader() object containing the powershell streams
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

        if running_pipelines > self.max_runspaces:
            raise WinRMError(
                "Cannot create new command pipeline as Runspace Pool already has %d running, max allowed %d" % (
                running_pipelines, self.max_runspaces))

        pipeline = Pipeline(self)
        self.pipelines.append(pipeline)
        pipeline.create(command, arguments)

        return pipeline.command_id

    def get_command_output(self, command_id):
        running_pipeline = None
        for pipeline in self.pipelines:
            if pipeline.command_id == command_id:
                running_pipeline = pipeline

        try:
            output = running_pipeline.get_output()
        finally:
            running_pipeline.stop()

        return output

    def cleanup_command(self, command_id):
        for pipeline in self.pipelines:
            if pipeline.command_id == command_id:
                pipeline.stop()

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
            body = self.send(WsmvAction.RECEIVE, receive_body, selector_set, option_set)
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


class Pipeline(object):
    def __init__(self, client):
        """
        A pipeline object that can run a command in the RunspacePool. Each
        pipeline can only run 1 command before it needs to be closed. You can
        run multiple pipelines in a RunspacePool but if max_runspaces has been
        set to a number > 1 than there is no guarantee it will keep the same
        values set by a previous pipeline

        :param rpid: The RunspacePool rpid
        :param shell_id: The shell id that was created in the RunspacePool
        :param resource_uri: The resource URI for the shell
        :param fragmenter: The fragmenter object created in the RunspacePool used to fragment messages
        :param wsmv_protocol: The WSMV protocol object used to send messages to the server
        """
        self.client = client
        self.pid = uuid.uuid4()
        self.command_id = str(uuid.uuid4()).upper()
        self.state = PsrpPSInvocationState.NOT_STARTED

    def create(self, command, arguments):
        """
        Will create a command pipeline to run on the server

        :param command: A script or command to run
        :param arguments: Optional argument to add to the command
        """
        commands = [ObjectTypes.create_command(command, arguments)]

        # We pipe the resulting command to a string so PSRP doesn't return a custom object
        commands.append(ObjectTypes.create_command('Out-String', ['-Stream']))
        create_pipeline = Message(Message.DESTINATION_SERVER, PsrpMessageType.CREATE_PIPELINE, self.client.rpid,
                                  self.pid, CreatePipeline(commands))

        fragments = self.client.fragmenter.fragment_messages(create_pipeline)
        body = WsmvObject.command_line('', fragments[0].decode(), self.command_id)
        response = self.client.send(WsmvAction.COMMAND, body=body, selector_set={'ShellId': self.client.shell_id})
        self.state = PsrpPSInvocationState.RUNNING

        # Send first fragment using the Command message
        command_id = response['s:Envelope']['s:Body']['rsp:CommandResponse']['rsp:CommandId']

        # Send the remaining fragments using the Send message
        for idx, fragment in enumerate(fragments):
            if idx != 0:
                body = WsmvObject.send('stdin', command_id, fragment[idx])
                self.client.send(WsmvAction.SEND, body=body,
                                        selector_set={'ShellId': self.client.shell_id})

    def get_output(self):
        """
        Will extract the command output from the server into a Reader()
        object. This object can be used to extra information from the various
        Powershell streams.

        Once the information has been retrieved the pipeline will be stopped

        :return: winrm.psrp.response_reader.Reader() object containing the powershell streams
        """
        defragmenter = Defragmenter()
        reader = Reader()
        body = WsmvObject.receive('stdout', self.command_id)

        while self.state == PsrpPSInvocationState.RUNNING:
            response = self.client.send(WsmvAction.RECEIVE, body=body, selector_set={'ShellId': self.client.shell_id})

            streams = response['s:Envelope']['s:Body']['rsp:ReceiveResponse']['rsp:Stream']
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

            command_state = response['s:Envelope']['s:Body']['rsp:ReceiveResponse']['rsp:CommandState']['@State']
            if command_state == 'http://schemas.microsoft.com/wbem/wsman/1/windows/shell/CommandState/Pending':
                self.send_command_input('hello world')

        self.stop()

        return reader

    def send_command_input(self, input):
        input_message = Message(Message.DESTINATION_SERVER, PsrpMessageType.PIPELINE_INPUT, self.client.rpid, self.pid, PipelineInput(input))
        fragments = self.client.fragmenter.fragment_messages(input_message)
        selector_set = {"ShellId": self.client.shell_id}
        for fragment in fragments:
            body = WsmvObject.send('pr', self.command_id, fragment)
            a = self.client.send(WsmvAction.SEND, body=body, selector_set=selector_set)
            b = ''

        #if end_of_input:
        #    end_of_input_message = Message(Message.DESTINATION_SERVER, PsrpMessageType.PIPELINE_INPUT, self.rpid, running_pipeline.pid, EndOfPipelineInput())
        #    fragments = self.fragmenter.fragment_messages(end_of_input_message)
        #    for fragment in fragments:
        #        body = WsmvObject.send('stdin', command_id, fragment)
        #        a = self.send(WsmvAction.SEND, body=body, selector_set=selector_set)
        #        b = ''

        z = ''


    def stop(self):
        # Will stop the pipeline if it has not been stopped already
        if self.state != PsrpPSInvocationState.STOPPED or self.state != PsrpPSInvocationState.FAILED:
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
