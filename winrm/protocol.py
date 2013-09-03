import base64
from datetime import timedelta
import uuid
import xml.etree.ElementTree as ET
from isodate.isoduration import duration_isoformat
import xmlwitch
from winrm.transport import HttpPlaintext, HttpKerberos


class Protocol(object):
    """
    This is the main class that does the SOAP request/response logic. There are a few helper classes, but pretty
    much everything comes through here first.
    """
    DEFAULT_TIMEOUT = 'PT60S'
    DEFAULT_MAX_ENV_SIZE = 153600
    DEFAULT_LOCALE = 'en-US'

    def __init__(self, endpoint, transport='plaintext', username=None, password=None, realm=None, service=None, keytab=None, ca_trust_path=None):
        """
        @param string endpoint: the WinRM webservice endpoint
        @param string transport: transport type, one of 'kerberos' (default), 'ssl', 'plaintext'
        @param string username: username
        @param string password: password
        @param string realm: the Kerberos realm we are authenticating to
        @param string service: the service name, default is HTTP
        @param string keytab: the path to a keytab file if you are using one
        @param string ca_trust_path: Certification Authority trust path
        """
        self.endpoint = endpoint
        self.timeout = Protocol.DEFAULT_TIMEOUT
        self.max_env_sz = Protocol.DEFAULT_MAX_ENV_SIZE
        self.locale = Protocol.DEFAULT_LOCALE
        if transport == 'plaintext':
            self.transport = HttpPlaintext(endpoint, username, password)
        elif transport == 'kerberos':
            self.transport = HttpKerberos(endpoint)
        else:
            raise NotImplementedError()
        self.username = username
        self.password = password
        self.service = service
        self.keytab = keytab
        self.ca_trust_path = ca_trust_path

    def set_timeout(self, seconds):
        """
        Operation timeout, see http://msdn.microsoft.com/en-us/library/ee916629(v=PROT.13).aspx
        @param int seconds: the number of seconds to set the timeout to. It will be converted to an ISO8601 format.
        """
        # in original library there is an alias - op_timeout method
        return duration_isoformat(timedelta(seconds))

    def open_shell(self, i_stream='stdin', o_stream='stdout stderr', working_directory=None, env_vars=None, noprofile=False, codepage=437, lifetime=None, idle_timeout=None):
        """
        Create a Shell on the destination host
        @param string i_stream: Which input stream to open. Leave this alone unless you know what you're doing (default: stdin)
        @param string o_stream: Which output stream to open. Leave this alone unless you know what you're doing (default: stdout stderr)
        @param string working_directory: the directory to create the shell in
        @param dict env_vars: environment variables to set for the shell. Fir instance: {'PATH': '%PATH%;c:/Program Files (x86)/Git/bin/', 'CYGWIN': 'nontsec codepage:utf8'}
        @returns The ShellId from the SOAP response.  This is our open shell instance on the remote machine.
        @rtype string
        """
        node = xmlwitch.Builder(version='1.0', encoding='utf-8')
        with node.env__Envelope(**self._namespaces):
            with node.env__Header:
                self._build_soap_header(node)
                self._set_resource_uri_cmd(node)
                self._set_action_create(node)
                with node.w__OptionSet:
                    node.w__Option(str(noprofile).upper(), Name='WINRS_NOPROFILE')
                    node.w__Option(str(codepage), Name='WINRS_CODEPAGE')

            with node.env__Body:
                with node.rsp__Shell:
                    node.rsp__InputStreams(i_stream)
                    node.rsp__OutputStreams(o_stream)
                    if working_directory:
                        #TODO ensure that rsp:WorkingDirectory should be nested within rsp:Shell
                        node.rsp_WorkingDirectory(working_directory)
                    # TODO: research Lifetime a bit more: http://msdn.microsoft.com/en-us/library/cc251546(v=PROT.13).aspx
                    #if lifetime:
                    #    node.rsp_Lifetime = iso8601_duration.sec_to_dur(lifetime)
                    # TODO: make it so the input is given in milliseconds and converted to xs:duration
                    if idle_timeout:
                        node.rsp_IdleTimeOut = idle_timeout
                    if env_vars:
                        with node.rsp_Environment:
                            for key, value in env_vars.items():
                                node.rsp_Variable(value, Name=key)

        response = self.send_message(str(node))
        root = ET.fromstring(response)
        return next(node for node in root.findall('.//*') if node.get('Name') == 'ShellId').text

    # Helper methods for building SOAP Headers

    def _build_soap_header(self, node, message_id=None):
        if not message_id:
            message_id = uuid.uuid4()
        node.a__To(str(self.endpoint))
        with node.a__ReplyTo:
            node.a__Address('http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous', mustUnderstand='true')
        node.w__MaxEnvelopeSize(str(self.max_env_sz), mustUnderstand='true')
        node.a__MessageID('uuid:{0}'.format(message_id))
        node.w__Locale(None, xml__lang=self.locale, mustUnderstand='false')
        node.p__DataLocale(None, xml__lang=self.locale, mustUnderstand='false')
        # TODO: research this a bit http://msdn.microsoft.com/en-us/library/cc251561(v=PROT.13).aspx
        #node.cfg__MaxTimeoutms = 600
        node.w__OperationTimeout(self.timeout)

    def _set_resource_uri_cmd(self, node):
        node.w__ResourceURI('http://schemas.microsoft.com/wbem/wsman/1/windows/shell/cmd', mustUnderstand='true')

    def _set_resource_uri_wmi(self, node, namespace='root/cimv2/*'):
        node.w__ResourceURI('http://schemas.microsoft.com/wbem/wsman/1/wmi/{0}'.format(namespace), mustUnderstand='true')

    def _set_action_create(self, node):
        node.a__Action('http://schemas.xmlsoap.org/ws/2004/09/transfer/Create', mustUnderstand='true')

    def _set_action_delete(self, node):
        node.a__Action('http://schemas.xmlsoap.org/ws/2004/09/transfer/Delete', mustUnderstand='true')

    def _set_action_command(self, node):
        node.a__Action('http://schemas.microsoft.com/wbem/wsman/1/windows/shell/Command', mustUnderstand='true')

    def _set_action_receive(self, node):
        node.a__Action('http://schemas.microsoft.com/wbem/wsman/1/windows/shell/Receive', mustUnderstand='true')

    def _set_action_signal(self, node):
        node.a__Action('http://schemas.microsoft.com/wbem/wsman/1/windows/shell/Signal', mustUnderstand='true')

    def _set_action_enumerate(self, node):
        node.a__Action('http://schemas.xmlsoap.org/ws/2004/09/enumeration/Enumerate', mustUnderstand='true')

    def _set_selector_shell_id(self, node, shell_id):
        with node.w__SelectorSet:
            node.w__Selector(shell_id, Name='ShellId')

    @property
    def _namespaces(self):
        return {
            'xmlns:xsd': 'http://www.w3.org/2001/XMLSchema',
            'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'xmlns:env': 'http://www.w3.org/2003/05/soap-envelope',

            'xmlns:a': 'http://schemas.xmlsoap.org/ws/2004/08/addressing',
            'xmlns:b': 'http://schemas.dmtf.org/wbem/wsman/1/cimbinding.xsd',
            'xmlns:n': 'http://schemas.xmlsoap.org/ws/2004/09/enumeration',
            'xmlns:x': 'http://schemas.xmlsoap.org/ws/2004/09/transfer',
            'xmlns:w': 'http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd',
            'xmlns:p': 'http://schemas.microsoft.com/wbem/wsman/1/wsman.xsd',
            'xmlns:rsp': 'http://schemas.microsoft.com/wbem/wsman/1/windows/shell',
            'xmlns:cfg': 'http://schemas.microsoft.com/wbem/wsman/1/config'
        }

    def send_message(self, message):
        # TODO add message_id vs relates_to checking
        # TODO port error handling code
        return self.transport.send_message(message)

    def close_shell(self, shell_id):
        """
        Close the shell
        @param string shell_id: The shell id on the remote machine.  See #open_shell
        @returns This should have more error checking but it just returns true for now.
        @rtype bool
        """
        message_id = uuid.uuid4()
        node = xmlwitch.Builder(version='1.0', encoding='utf-8')
        with node.env__Envelope(**self._namespaces):
            with node.env__Header:
                self._build_soap_header(node, message_id)
                self._set_resource_uri_cmd(node)
                self._set_action_delete(node)
                self._set_selector_shell_id(node, shell_id)

            # SOAP message requires empty env:Body
            with node.env__Body:
                pass

        response = self.send_message(str(node))
        root = ET.fromstring(response)
        relates_to = next(node for node in root.findall('.//*') if node.tag.endswith('RelatesTo')).text
        # TODO change assert into user-friendly exception
        assert uuid.UUID(relates_to.replace('uuid:', '')) == message_id

    def run_command(self, shell_id, command, arguments=(), console_mode_stdin=True, skip_cmd_shell=False):
        """
        Run a command on a machine with an open shell
        @param string shell_id: The shell id on the remote machine.  See #open_shell
        @param string command: The command to run on the remote machine
        @param iterable of string arguments: An array of arguments for this command
        @param bool console_mode_stdin: (default: True)
        @param bool skip_cmd_shell: (default: False)
        @return: The CommandId from the SOAP response.  This is the ID we need to query in order to get output.
        @rtype string
        """
        node = xmlwitch.Builder(version='1.0', encoding='utf-8')
        with node.env__Envelope(**self._namespaces):
            with node.env__Header:
                self._build_soap_header(node)
                self._set_resource_uri_cmd(node)
                self._set_action_command(node)
                self._set_selector_shell_id(node, shell_id)
                with node.w__OptionSet:
                    node.w__Option(str(console_mode_stdin).upper(), Name='WINRS_CONSOLEMODE_STDIN')
                    node.w__Option(str(skip_cmd_shell).upper(), Name='WINRS_SKIP_CMD_SHELL')

            with node.env__Body:
                with node.rsp__CommandLine:
                    node.rsp__Command(command)
                    if arguments:
                        node.rsp__Arguments(' '.join(arguments))

        response = self.send_message(str(node))
        root = ET.fromstring(response)
        command_id = next(node for node in root.findall('.//*') if node.tag.endswith('CommandId')).text
        return command_id

    def cleanup_command(self, shell_id, command_id):
        """
        Clean-up after a command. @see #run_command
        @param string shell_id: The shell id on the remote machine.  See #open_shell
        @param string command_id: The command id on the remote machine.  See #run_command
        @returns: This should have more error checking but it just returns true for now.
        @rtype bool
        """
        message_id = uuid.uuid4()
        node = xmlwitch.Builder(version='1.0', encoding='utf-8')
        with node.env__Envelope(**self._namespaces):
            with node.env__Header:
                self._build_soap_header(node, message_id)
                self._set_resource_uri_cmd(node)
                self._set_action_signal(node)
                self._set_selector_shell_id(node, shell_id)

            # Signal the Command references to terminate (close stdout/stderr)
            with node.env__Body:
                with node.rsp__Signal(CommandId=command_id):
                    node.rsp__Code('http://schemas.microsoft.com/wbem/wsman/1/windows/shell/signal/terminate')

        response = self.send_message(str(node))
        root = ET.fromstring(response)
        relates_to = next(node for node in root.findall('.//*') if node.tag.endswith('RelatesTo')).text
        # TODO change assert into user-friendly exception
        assert uuid.UUID(relates_to.replace('uuid:', '')) == message_id

    def get_command_output(self, shell_id, command_id):
        """
        Get the Output of the given shell and command
        @param string shell_id: The shell id on the remote machine.  See #open_shell
        @param string command_id: The command id on the remote machine.  See #run_command
        #@return [Hash] Returns a Hash with a key :exitcode and :data.  Data is an Array of Hashes where the cooresponding key
        #   is either :stdout or :stderr.  The reason it is in an Array so so we can get the output in the order it ocurrs on
        #   the console.
        """
        stdout_buffer, stderr_buffer = [], []
        command_done = False
        while not command_done:
            stdout, stderr, return_code, command_done = \
                self._raw_get_command_output(shell_id, command_id)
            stdout_buffer.append(stdout)
            stderr_buffer.append(stderr)
        return "".join(stdout_buffer), "".join(stderr_buffer), return_code

    def _raw_get_command_output(self, shell_id, command_id):
        node = xmlwitch.Builder(version='1.0', encoding='utf-8')
        with node.env__Envelope(**self._namespaces):
            with node.env__Header:
                self._build_soap_header(node)
                self._set_resource_uri_cmd(node)
                self._set_action_receive(node)
                self._set_selector_shell_id(node, shell_id)

            with node.env__Body:
                with node.rsp__Receive:
                    node.rsp__DesiredStream('stdout stderr', CommandId=command_id)

        response = self.send_message(str(node))
        root = ET.fromstring(response)
        stream_nodes = [node for node in root.findall('.//*') if node.tag.endswith('Stream')]
        stdout = stderr = ''
        return_code = -1
        for stream_node in stream_nodes:
            if stream_node.text:
                if stream_node.attrib['Name'] == 'stdout':
                    stdout += str(base64.b64decode(stream_node.text.encode('ascii')))
                elif stream_node.attrib['Name'] == 'stderr':
                    stderr += str(base64.b64decode(stream_node.text.encode('ascii')))

        # We may need to get additional output if the stream has not finished.
        # The CommandState will change from Running to Done like so:
        # @example
        #   from...
        #   <rsp:CommandState CommandId="..." State="http://schemas.microsoft.com/wbem/wsman/1/windows/shell/CommandState/Running"/>
        #   to...
        #   <rsp:CommandState CommandId="..." State="http://schemas.microsoft.com/wbem/wsman/1/windows/shell/CommandState/Done">
        #     <rsp:ExitCode>0</rsp:ExitCode>
        #   </rsp:CommandState>
        command_done = len([node for node in root.findall('.//*') if node.get('State', '').endswith('CommandState/Done')]) == 1
        if command_done:
            return_code = int(next(node for node in root.findall('.//*') if node.tag.endswith('ExitCode')).text)

        return stdout, stderr, return_code, command_done