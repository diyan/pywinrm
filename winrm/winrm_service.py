# Test how in-place editor works on GitHub
from datetime import timedelta
import uuid
from http.transport import HttpPlaintext
from isodate.isoduration import duration_isoformat
import xmlwitch
import requests
import xml.etree.ElementTree as ET

class WinRMWebService(object):
    """
    This is the main class that does the SOAP request/response logic. There are a few helper classes, but pretty
    much everything comes through here first.
    """
    DEFAULT_TIMEOUT = 'PT60S'
    DEFAULT_MAX_ENV_SIZE = 153600
    DEFAULT_LOCALE = 'en-US'

    def __init__(self, endpoint, transport='kerberos', username=None, password=None, realm=None, service=None, keytab=None, ca_trust_path=None):
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
        self.timeout = WinRMWebService.DEFAULT_TIMEOUT
        self.max_env_sz = WinRMWebService.DEFAULT_MAX_ENV_SIZE
        self.locale = WinRMWebService.DEFAULT_LOCALE
        self.transport = transport
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
        # TODO implement self.merge_headers(header, resource_uri_cmd, action_create, h_opts)
        xml = xmlwitch.Builder(version='1.0', encoding='utf-8')
        with xml.env__Envelope(**self.namespaces):
            with xml.env__Header:
                xml.a__To(self.endpoint)
                with xml.a__ReplyTo:
                    xml.a__Address('http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous', mustUnderstand='true')
                xml.w__MaxEnvelopeSize('153600', mustUnderstand='true')
                xml.a__MessageID('uuid:{0}'.format(uuid.uuid4()))
                xml.w__Locale(None, xml__lang='en-US', mustUnderstand='false')
                xml.p__DataLocale(None, xml__lang='en-US', mustUnderstand='false')
                xml.w__OperationTimeout('PT60S')
                xml.w__ResourceURI('http://schemas.microsoft.com/wbem/wsman/1/windows/shell/cmd', mustUnderstand='true')
                xml.a__Action('http://schemas.xmlsoap.org/ws/2004/09/transfer/Create', mustUnderstand='true')
                with xml.w__OptionSet:
                    xml.w__Option(str(noprofile).upper(), Name='WINRS_NOPROFILE')
                    xml.w__Option(str(codepage), Name='WINRS_CODEPAGE')

            with xml.env__Body:
                with xml.rsp__Shell:
                    xml.rsp__InputStreams(i_stream)
                    xml.rsp__OutputStreams(o_stream)
                    if working_directory:
                        #TODO ensure that rsp:WorkingDirectory should be nested within rsp:Shell
                        xml.rsp_WorkingDirectory(working_directory)
                    # TODO: research Lifetime a bit more: http://msdn.microsoft.com/en-us/library/cc251546(v=PROT.13).aspx
                    #if lifetime:
                    #    xml.rsp_Lifetime = iso8601_duration.sec_to_dur(lifetime)
                    # TODO: make it so the input is given in milliseconds and converted to xs:duration
                    if idle_timeout:
                        xml.rsp_IdleTimeOut = idle_timeout
                    if env_vars:
                        with xml.rsp_Environment:
                            for key, value in env_vars.items():
                                xml.rsp_Variable(value, Name=key)

        response = self.send_message(str(xml))
        root = ET.fromstring(response)
        return root.find('.//*[@Name="ShellId"]').text

    @property
    def namespaces(self):
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

    def send_request(self, message):
        return requests.post(
            self.endpoint,
            data=message,
            auth=(self.username, self.password))

    def send_message(self, message):
        response = self.send_request(message)
        # TODO handle status codes other than HTTP OK 200
        # TODO port error handling code
        return response.text

    def close_shell(self, shell_id):
        """
        Close the shell
        @param string shell_id: The shell id on the remote machine.  See #open_shell
        @returns This should have more error checking but it just returns true for now.
        @rtype bool
        """
        pass


endpoint = ''
transport = HttpPlaintext(endpoint)