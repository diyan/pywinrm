"""Contains client side logic of WinRM SOAP protocol implementation"""
import warnings

from winrm.transport import Transport
from winrm.exceptions import WinRMError

from winrm.wsmv.protocol import WsmvProtocol

class Protocol(object):
    """This is the main class that does the SOAP request/response logic. There
    are a few helper classes, but pretty much everything comes through here
    first.
    """
    DEFAULT_READ_TIMEOUT_SEC = 30
    DEFAULT_OPERATION_TIMEOUT_SEC = 20
    DEFAULT_MAX_ENV_SIZE = 153600
    DEFAULT_LOCALE = 'en-US'

    def __init__(
            self, endpoint, transport='plaintext', username=None,
            password=None, realm=None, service=None, keytab=None,
            ca_trust_path=None, cert_pem=None, cert_key_pem=None,
            server_cert_validation='validate',
            kerberos_delegation=False,
            read_timeout_sec=DEFAULT_READ_TIMEOUT_SEC,
            operation_timeout_sec=DEFAULT_OPERATION_TIMEOUT_SEC,
            kerberos_hostname_override=None,
        ):
        """
        @param string endpoint: the WinRM webservice endpoint
        @param string transport: transport type, one of 'plaintext' (default), 'kerberos', 'ssl', 'ntlm', 'credssp'  # NOQA
        @param string username: username
        @param string password: password
        @param string realm: unused
        @param string service: the service name, default is HTTP
        @param string keytab: the path to a keytab file if you are using one
        @param string ca_trust_path: Certification Authority trust path
        @param string cert_pem: client authentication certificate file path in PEM format  # NOQA
        @param string cert_key_pem: client authentication certificate key file path in PEM format  # NOQA
        @param string server_cert_validation: whether server certificate should be validated on Python versions that suppport it; one of 'validate' (default), 'ignore' #NOQA
        @param bool kerberos_delegation: if True, TGT is sent to target server to allow multiple hops  # NOQA
        @param int read_timeout_sec: maximum seconds to wait before an HTTP connect/read times out (default 30). This value should be slightly higher than operation_timeout_sec, as the server can block *at least* that long. # NOQA
        @param int operation_timeout_sec: maximum allowed time in seconds for any single wsman HTTP operation (default 20). Note that operation timeouts while receiving output (the only wsman operation that should take any significant time, and where these timeouts are expected) will be silently retried indefinitely. # NOQA
        @param string kerberos_hostname_override: the hostname to use for the kerberos exchange (defaults to the hostname in the endpoint URL)
        """

        warnings.warn("winrm.protocol is a deprecated class, all functionality should"
                      " be moved over to use winrm.wsmv.protocol instead")

        if operation_timeout_sec >= read_timeout_sec or operation_timeout_sec < 1:
            raise WinRMError("read_timeout_sec must exceed operation_timeout_sec, and both must be non-zero")

        self.read_timeout_sec = read_timeout_sec
        self.operation_timeout_sec = operation_timeout_sec
        self.locale = Protocol.DEFAULT_LOCALE

        self.transport = Transport(
            endpoint=endpoint, username=username, password=password,
            realm=realm, service=service, keytab=keytab,
            ca_trust_path=ca_trust_path, cert_pem=cert_pem,
            cert_key_pem=cert_key_pem, read_timeout_sec=self.read_timeout_sec,
            server_cert_validation=server_cert_validation,
            kerberos_delegation=kerberos_delegation,
            kerberos_hostname_override=kerberos_hostname_override,
            auth_method=transport)

        self.username = username
        self.password = password
        self.service = service
        self.keytab = keytab
        self.ca_trust_path = ca_trust_path
        self.server_cert_validation = server_cert_validation
        self.kerberos_delegation = kerberos_delegation
        self.kerberos_hostname_override = kerberos_hostname_override

        # Used to bridge old deprecated protocol to new WSMV protocol
        self.wsmv = WsmvProtocol(self.transport, read_timeout_sec, operation_timeout_sec)

    def open_shell(self, i_stream='stdin', o_stream='stdout stderr',
                   working_directory=None, env_vars=None, noprofile=False,
                   codepage=437, lifetime=None, idle_timeout=None):
        """
        Create a Shell on the destination host
        @param string i_stream: Which input stream to open. Leave this alone
         unless you know what you're doing (default: stdin)
        @param string o_stream: Which output stream to open. Leave this alone
         unless you know what you're doing (default: stdout stderr)
        @param string working_directory: the directory to create the shell in
        @param dict env_vars: environment variables to set for the shell. For
         instance: {'PATH': '%PATH%;c:/Program Files (x86)/Git/bin/', 'CYGWIN':
          'nontsec codepage:utf8'}
        @returns The ShellId from the SOAP response. This is our open shell
         instance on the remote machine.
        @rtype string
        """
        new_kwargs = {
            'input_steams': i_stream,
            'output_steams': o_stream,
            'working_directory': working_directory,
            'environment': env_vars,
            'idle_time_out': idle_timeout
        }
        return self.wsmv.open_shell(noprofile, codepage, **new_kwargs)

    def close_shell(self, shell_id):
        """
        Close the shell
        @param string shell_id: The shell id on the remote machine.
         See #open_shell
        @returns This should have more error checking but it just returns true
         for now.
        @rtype bool
        """
        self.wsmv.close_shell(shell_id)
        return True

    def run_command(
            self, shell_id, command, arguments=(), console_mode_stdin=True,
            skip_cmd_shell=False):
        """
        Run a command on a machine with an open shell
        @param string shell_id: The shell id on the remote machine.
         See #open_shell
        @param string command: The command to run on the remote machine
        @param iterable of string arguments: An array of arguments for this
         command
        @param bool console_mode_stdin: (default: True)
        @param bool skip_cmd_shell: (default: False)
        @return: The CommandId from the SOAP response.
         This is the ID we need to query in order to get output.
        @rtype string
        """
        return self.wsmv.run_command(shell_id, command, arguments, console_mode_stdin, skip_cmd_shell)

    def cleanup_command(self, shell_id, command_id):
        """
        Clean-up after a command. @see #run_command
        @param string shell_id: The shell id on the remote machine.
         See #open_shell
        @param string command_id: The command id on the remote machine.
         See #run_command
        @returns: This should have more error checking but it just returns true
         for now.
        @rtype bool
        """
        self.wsmv.cleanup_command(shell_id, command_id)
        return True

    def get_command_output(self, shell_id, command_id):
        """
        Get the Output of the given shell and command
        @param string shell_id: The shell id on the remote machine.
         See #open_shell
        @param string command_id: The command id on the remote machine.
         See #run_command
        #@return [Hash] Returns a Hash with a key :exitcode and :data.
         Data is an Array of Hashes where the cooresponding key
        #   is either :stdout or :stderr.  The reason it is in an Array so so
         we can get the output in the order it ocurrs on
        #   the console.
        """
        command_output = self.wsmv.get_command_output(shell_id, command_id)
        stdout = command_output['stdout']
        stderr = command_output['stderr']
        return_code = command_output['return_code']

        return stdout, stderr, return_code
