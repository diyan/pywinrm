import base64

from winrm.client import Client
from winrm.contants import WsmvConstant, WsmvAction, WsmvResourceURI, WsmvSignal
from winrm.exceptions import WinRMOperationTimeoutError
from winrm.wsmv.objects import WsmvObject


class WsmvClient(Client):

    def __init__(self,
                 transport_opts,
                 operation_timeout_sec=WsmvConstant.DEFAULT_OPERATION_TIMEOUT_SEC,
                 locale=WsmvConstant.DEFAULT_LOCALE,
                 encoding=WsmvConstant.DEFAULT_ENCODING,
                 max_envelope_size=WsmvConstant.DEFAULT_MAX_ENVELOPE_SIZE
                 ):
        """
        Creates a handler for managing WSMV session and exposes various method
        to create a shell, run a command and then close the shell through the
        WSMV protocol. WSMV executes commands in a cmd.exe context, if you
        want to run a command in a powershell.exe context please use
        winrm.psrp.protocol.PsrpHandler instead.

        :param Transport transport: A initialised Transport() object for handling message transport
        :param int read_timeout_sec: The maximum amount of seconds to wait before a HTTP connect/read times out (default 30). This value should be slightly higher than operation_timeout_sec, as the server can block *at least* that long.
        :param int operation_timeout_sec: The maximum allows time in seconds for any single WSMan HTTP operation (default 20). Note that operation timeouts while receiving output (the only WSMan operation that should take any singificant time, and where these timeouts are expected) will be silently retried indefinitely.
        :param string locale: The locale value to use when creating a Shell on the remote host (default en-US).
        :param string encoding: The encoding format when creating XML strings to send to the server (default utf-8).
        """
        Client.__init__(self, transport_opts, operation_timeout_sec, locale, encoding, max_envelope_size,
                        WsmvResourceURI.SHELL_CMD)

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
        res = self.send(WsmvAction.CREATE, body=body, option_set=option_set)
        self.shell_id = res['s:Envelope']['s:Body']['rsp:Shell']['rsp:ShellId']

    def run_command(self, command, arguments=(), consolemode_stdin=True, skip_cmd_shell=False):
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
            'ShellId': self.shell_id
        }
        option_set = {
            'WINRS_CONSOLEMODE_STDIN': str(consolemode_stdin).upper(),
            'WINRS_SKIP_CMD_SHELL': str(skip_cmd_shell).upper()
        }
        res = self.send(WsmvAction.COMMAND, body, selector_set, option_set)
        command_id = res['s:Envelope']['s:Body']['rsp:CommandResponse']['rsp:CommandId']

        return command_id

    def get_command_output(self, command_id):
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
        selector_set = {'ShellId': self.shell_id}
        while not command_done:
            try:
                raw_output = self.send(WsmvAction.RECEIVE, body=body,
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

    def cleanup_command(self, command_id):
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
            'ShellId': self.shell_id
        }
        self.send(WsmvAction.SIGNAL, body=body, selector_set=selector_set)

    def close_shell(self):
        """
        [MS-WSMV] v30.0 2016-07-14
        3.1.4.15 Disconnect

        Will disconnect from a remote Shell based on the ID that has been
        passed through. This should be run at the end of all process to
        ensure any left over shells on the host are removed.

        :param shell_id: The Shell ID to disconnect from
        """
        selector_set = {
            'ShellId': self.shell_id
        }
        self.send(WsmvAction.DELETE, self.resource_uri, selector_set=selector_set)

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
