import logging
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from winrm.client import Client
from winrm.contants import WsmvConstant, WsmvAction, WsmvResourceURI, WsmvSignal, WsmvCommandState
from winrm.exceptions import WinRMOperationTimeoutError

from winrm.wsmv.message_objects import WsmvObject
from winrm.wsmv.response_reader import Reader

log = logging.getLogger(__name__)


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
        winrm.psrp.psrp.PsrpClient instead.

        :param transport_opts: See winrm.client Client() for more info
        :param int operation_timeout_sec: See winrm.client Client() for more info
        :param string locale: See winrm.client Client() for more info
        :param string encoding: See winrm.client Client() for more info
        :param int max_envelope_size: See winrm.client Client() for more info
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
        option_set = OrderedDict([
            ('WINRS_CODEPAGE', str(codepage)),
            ('WINRS_NOPROFILE', str(noprofile).upper())
        ])

        res = self.send(WsmvAction.CREATE, body=body, option_set=option_set)
        self.shell_id = res['s:Envelope']['s:Body']['rsp:Shell']['rsp:ShellId']
        log.debug("WSMV Shell created: Shell ID: %s, Resource URI: %s" % (self.shell_id, self.resource_uri))

    def run_command(self, command, arguments=(), consolemode_stdin=True, skip_cmd_shell=False):
        """
        [MS-WSMV] v30.0 2016-07-14
        3.1.4.11 Command

        Will run a command through WSMV on the server.

        :param command: The command without any arguments
        :param arguments: Optional arguments to add to the command
        :param consolemode_stdin: Standard input is console if True
        :param skip_cmd_shell: If True will run outside cmd.exe, if False will run with cmd.exe
        :return: The Command ID to be used later when retrieving the stdout
        """
        body = WsmvObject.command_line(command, arguments)
        selector_set = {
            'ShellId': self.shell_id
        }
        option_set = OrderedDict([
            ('WINRS_CONSOLEMODE_STDIN', str(consolemode_stdin).upper()),
            ('WINRS_SKIP_CMD_SHELL', str(skip_cmd_shell).upper())
        ])
        res = self.send(WsmvAction.COMMAND, body=body, selector_set=selector_set, option_set=option_set)
        command_id = res['s:Envelope']['s:Body']['rsp:CommandResponse']['rsp:CommandId']

        return command_id

    def get_command_output(self, command_id):
        """
        [MS-WSMV] v30.0 2016-07-14
        3.1.4.14 Receive

        In the Text-based Command Shell scenario, the Receive message is used
        to collect output from a running command

        :param command_id: The Command ID for the command to get the ouput for
        :return: Reader: A class containing the stdout, stderr and return_code of the command
        """
        try:
            state = WsmvCommandState.RUNNING
            body = WsmvObject.receive('stdout stderr', command_id)
            selector_set = {'ShellId': self.shell_id}
            reader = Reader()

            while state != WsmvCommandState.DONE:
                try:
                    response = self.send(WsmvAction.RECEIVE, body=body, selector_set=selector_set)
                    state = reader.parse_receive_response(response)
                except WinRMOperationTimeoutError:
                    # this is an expected error when waiting for a long-running process, just silently retry
                    pass
        finally:
            self._cleanup_command(command_id)

        return reader

    def close_shell(self):
        """
        [MS-WSMV] v30.0 2016-07-14
        3.1.4.15 Disconnect

        Will disconnect from a remote Shell based on the ID that has been
        passed through. This should be run at the end of all process to
        ensure any left over shells on the host are removed.
        """
        selector_set = {
            'ShellId': self.shell_id
        }
        self.send(WsmvAction.DELETE, selector_set=selector_set)

    def _cleanup_command(self, command_id):
        """
        [MS-WSMV] v30.0 2016-07-14
        3.1.4.12 Signal

        This will send the terminate signal to a command based on the ID that
        has been passed through.

        :param command_id: The Command ID for the command to get the ouput for
        """
        body = WsmvObject.signal(WsmvSignal.TERMINATE, command_id)
        selector_set = {
            'ShellId': self.shell_id
        }
        self.send(WsmvAction.SIGNAL, body=body, selector_set=selector_set)
