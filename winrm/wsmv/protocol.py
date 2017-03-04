import base64
import uuid
import xmltodict

from winrm.contants import WsmvConstant, WsmvAction, WsmvResourceURI, WsmvSignal
from winrm.exceptions import WinRMError, WinRMOperationTimeoutError
from winrm.wsmv.objects import WsmvObject


class WsmvProtocol(object):
    def __init__(
            self, transport,
            read_timeout_sec=WsmvConstant.DEFAULT_READ_TIMEOUT_SEC,
            operation_timeout_sec=WsmvConstant.DEFAULT_OPERATION_TIMEOUT_SEC,
            locale=WsmvConstant.DEFAULT_LOCALE,
            encoding=WsmvConstant.DEFAULT_ENCODING):
        """
        Creates a handler for managing WSMV session and exposes various method
        to create a shell, run a command and then close the shell through the
        WSMV protocol. WSMV executes commands in a cmd.exe context, if you
        want to run a command in a powershell.exe context please use
        winrm.psrp.protocol.PsrpHandler instead.

        :param Transport transport: A initialised Transport() object for handling message transport
        :param int read_timeout_sec: The maximum amount of seconds to wait before a HTTP connect/read times out (default 30). This value should be slightly higher than operation_timeout_sec, as the server can block *at least* that long.
        :param int operation_timeout_sec: The maximum allows time in seconds for any single WSMan HTTP operation (default 20). Note that operation timeouts while receiving output (the only WSMan operation that should take any singificant time, and where these timeouts are expected) will be silently retried indefinitely.
        :param int max_envelop_size: The maximum envelope size of the WSMan message (default 153600).
        :param string locale: The locale value to use when creating a Shell on the remote host (default en-US).
        :param string encoding: The encoding format when creating XML strings to send to the server (default utf-8).
        """
        if operation_timeout_sec >= read_timeout_sec or operation_timeout_sec < 1:
            raise WinRMError("read_timeout_sec must exceed operation_timeout_sec, and both must be non-zero")

        self.session_id = str(uuid.uuid4()).upper()
        self.server_config = self.get_server_config()
        self.max_envelope_size = self.server_config['max_envelope_size']
        self.read_timeout_sec = read_timeout_sec
        self.operation_timeout_sec = operation_timeout_sec
        self.locale = locale
        self.encoding = encoding
        self.transport = transport

    def open_shell(self, noprofile=False, codepage=437, **kwargs):
        """
        [MS-WSMV] v30.0 2016-07-14
        3.1.4.5.2 Remote Shells

        To create a new Shell, a wst:Create message MUST be sent where the
        resource_uri element of the EPR specifies the type of Shell to be
        created.

        :param noprofile: If set to TRUE, will use the default profile instead of the user profile on the system.
        :param codepage: Client's console output code page.
        :param kwargs: Optional arguments to pass along when creating the Shell object. See ComplexType.shell for further definitions
        :return: The Shell ID of the newly created shell to be used for further actions
        """
        body = WsmvObject.shell(**kwargs)
        option_set = {
            'WINRS_NOPROFILE': str(noprofile).upper(),
            'WINRS_CODEPAGE': str(codepage)
        }
        res = self.send(WsmvAction.CREATE, WsmvResourceURI.SHELL_CMD, body=body, option_set=option_set)
        shell_id = res['s:Envelope']['s:Body']['rsp:Shell']['rsp:ShellId']
        return shell_id

    def run_command(self, shell_id, command, arguments=(), consolemode_stdin=True, skip_cmd_shell=False):
        """
        [MS-WSMV] v30.0 2016-07-14
        3.1.4.11 Command

        Will run a command through WSMV on the server.

        :param shell_id: The Shell ID to run the command in
        :param command: The command without any arguments
        :param arguments: Optional arguments to add to the command
        :param consolemode_stdin: Standard input is console if True or pip if False
        :param skip_cmd_shell: If True will run outside cmd.exe, if True will run with cmd.exe
        :return: The Command ID to be used later when retrieving the stdout
        """
        body = WsmvObject.command_line(command, arguments)
        selector_set = {
            'ShellId': shell_id
        }
        option_set = {
            'WINRS_CONSOLEMODE_STDIN': str(consolemode_stdin).upper(),
            'WINRS_SKIP_CMD_SHELL': str(skip_cmd_shell).upper()
        }
        res = self.send(WsmvAction.COMMAND, WsmvResourceURI.SHELL_CMD, body, selector_set, option_set)
        command_id = res['s:Envelope']['s:Body']['rsp:CommandResponse']['rsp:CommandId']

        return command_id

    def get_command_output(self, shell_id, command_id):
        """
        [MS-WSMV] v30.0 2016-07-14
        3.1.4.14 Receive

        In the Text-based Command Shell scenario, the Receive message is used
        to collect output from a running command

        :param shell_id: The Shell ID the command is running in
        :param command_id: The Command ID for the command to get the ouput for
        :return: dict:
            int return_code: The return code from the command
            bytestring stdout: The stdout from the command
            bytestring stderr: The stderr from the command
        """
        stdout_buffer = []
        stderr_buffer = []
        return_code = -1
        command_done = False

        body = WsmvObject.receive('stdout stderr', command_id)
        selector_set = {'ShellId': shell_id}
        while not command_done:
            try:
                raw_output = self.send(WsmvAction.RECEIVE, WsmvResourceURI.SHELL_CMD, body=body,
                                       selector_set=selector_set)
                stdout, stderr, return_code, command_done = self._parse_raw_command_output(raw_output)
                stdout_buffer.append(stdout)
                stderr_buffer.append(stderr)
            except WinRMOperationTimeoutError:
                # this is an expected error when waiting for a long-running process, just silently retry
                pass

        output = {
            'stdout': b''.join(stdout_buffer),
            'stderr': b''.join(stderr_buffer),
            'return_code': int(return_code)
        }

        return output

    def cleanup_command(self, shell_id, command_id):
        """
        [MS-WSMV] v30.0 2016-07-14
        3.1.4.12 Signal

        This will send the terminate signal to a command based on the ID that
        has been passed through.

        :param shell_id: The Shell ID the command is running in
        :param command_id: The Command ID for the command to get the ouput for
        """
        body = WsmvObject.signal(WsmvSignal.TERMINATE, command_id)
        selector_set = {
            'ShellId': shell_id
        }
        self.send(WsmvAction.SIGNAL, WsmvResourceURI.SHELL_CMD, body=body, selector_set=selector_set)

    def close_shell(self, shell_id):
        """
        [MS-WSMV] v30.0 2016-07-14
        3.1.4.15 Disconnect

        Will disconnect from a remote Shell based on the ID that has been
        passed through. This should be run at the end of all process to
        ensure any left over shells on the host are removed.

        :param shell_id: The Shell ID to disconnect from
        """
        selector_set = {
            'ShellId': shell_id
        }
        self.send(WsmvAction.DELETE, WsmvResourceURI.SHELL_CMD, selector_set=selector_set)

    def get_server_config(self):
        """
        [MS-WSMV] v30 2016-07-14
        2.2.4.10 ConfigType

        ConfigType is the container for WSMV service configuration data.
        If not running under an admin we cannot retrieve these values and will
        revert to the default value

        :return: dict:
            max_batch_items: Maximum number of elements in a Pull response, min 1, max 4294967295, default 20
            max_envelope_size_kb: Maximum SOAP data in kilobytes, min 32, max 4294967295, default 150
            max_provider_requests: Maximum number of concurrent requests to WSMV, min 1, max 4294967295, default 25
            max_timeout_ms: Maximum timeout in milliseconds for any requests except Pull, min 500, max 4294967295, default 60000
        """
        try:
            res = self.send(WsmvAction.GET, WsmvResourceURI.CONFIG)
            config = {
                'max_batch_items': int(res['s:Envelope']['s:Body']['cfg:Config']['cfg:MaxBatchItems']),
                'max_envelope_size': int(res['s:Envelope']['s:Body']['cfg:Config']['cfg:MaxEnvelopeSizekb']) * 1024,
                'max_provider_requests': int(res['s:Envelope']['s:Body']['cfg:Config']['cfg:MaxProviderRequests']),
                'max_timeout_ms': int(res['s:Envelope']['s:Body']['cfg:Config']['cfg:MaxTimeoutms'])
            }
        except Exception:
            # Not running as admin, reverting to defauls
            config = {
                'max_batch_items': 20,
                'max_envelope_size': WsmvConstant.DEFAULT_MAX_ENVELOPE_SIZE,
                'max_provider_requests': 25,
                'max_timeout_ms': 60000
            }

        return config

    def create_message(self, body, action, resource_uri, selector_set=None, option_set=None):
        headers = self._create_headers(action, resource_uri, selector_set, option_set)
        message = {
            's:Envelope': {
                's:Header': headers,
                's:Body': {}
            }
        }
        for alias, namespace in WsmvConstant.NAMESPACES.items():
            message['s:Envelope']["@xmlns:%s" % alias] = namespace

        if body:
            message['s:Envelope']['s:Body'] = body

        return message

    def send(self, action, resource_uri, body=None, selector_set=None, option_set=None):
        """
        Will send the obj to the server valid the response relates to the request

        :param action: The WSMV action to send through
        :param resource_uri: The WSMV resource_uri
        :param body: The WSMV body which is created by winrm.wsmv.complex_types
        :param selector_set: To add optional selector sets header values to the headers
        :param option_set: To add optional option sets header values to the headers
        :return: A dict which is the xml conversion from the server
        """
        message = self.create_message(body, action, resource_uri, selector_set, option_set)
        message_id = message['s:Envelope']['s:Header']['a:MessageID']
        message = xmltodict.unparse(message, full_document=False, encoding=self.encoding)
        print(message)

        response_xml = self.transport.send_message(message)
        response = xmltodict.parse(response_xml, encoding=self.encoding)
        response_relates_id = response['s:Envelope']['s:Header']['a:RelatesTo']

        if message_id != response_relates_id:
            raise WinRMError("Response related to Message ID: '%s' does not match request Message ID: '%s'" % (
            response_relates_id, message_id))

        return response

    def _create_headers(self, action, resource_uri, selector_set, option_set):
        headers = {
            'a:Action': {
                '@s:mustUnderstand': 'true',
                '#text': action
            },
            'p:DataLocale': {
                '@s:mustUnderstand': 'false',
                '@xml:lang': self.locale
            },
            'w:Locale': {
                '@s:mustUnderstand': 'false',
                '@xml:lang': self.locale
            },
            'a:To': self.transport.endpoint,
            'w:ResourceURI': {
                '@s:mustUnderstand': 'true',
                '#text': resource_uri
            },
            'w:OperationTimeout': 'PT%sS' % str(self.operation_timeout_sec),
            'a:ReplyTo': {
                "a:Address": {
                    "@s:mustUnderstand": 'true',
                    '#text': 'http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous'
                }
            },
            'w:MaxEnvelopeSize': '%s' % str(self.max_envelope_size),
            'a:MessageID': 'uuid:%s' % str(uuid.uuid4()).upper(),
            'p:SessionId': {
                '@s:mustUnderstand': 'false',
                '#text': 'uuid:%s' % self.session_id
            }
        }

        if selector_set:
            selector_set_list = []
            for key, value in selector_set.items():
                selector_set_list.append({'@Name': key, '#text': value})
            headers['w:SelectorSet'] = {'w:Selector': selector_set_list}

        if option_set:
            option_set_list = []
            for key, value in option_set.items():
                option_set_list.append({'@Name': key, '#text': value})
            headers['w:OptionSet'] = {'w:Option': option_set_list}
        return headers


    def _parse_raw_command_output(self, output):
        stdout = b''
        stderr = b''
        receive_response = output['s:Envelope']['s:Body']['rsp:ReceiveResponse']
        try:
            for stream_node in receive_response['rsp:Stream']:
                raw_text = stream_node['#text']
                text = base64.b64decode(raw_text.encode('ascii'))
                if stream_node['@Name'] == 'stdout':
                    stdout += text
                elif stream_node['@Name'] == 'stderr':
                    stderr += text
        except KeyError:
            pass

        command_state = output['s:Envelope']['s:Body']['rsp:ReceiveResponse']['rsp:CommandState']['@State']
        if command_state == 'http://schemas.microsoft.com/wbem/wsman/1/windows/shell/CommandState/Done':
            command_done = True
            return_code = output['s:Envelope']['s:Body']['rsp:ReceiveResponse']['rsp:CommandState']['rsp:ExitCode']
        else:
            command_done = False
            return_code = -1

        return stdout, stderr, return_code, command_done
