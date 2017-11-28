from __future__ import unicode_literals

import logging
import requests
import requests.auth
import os
import warnings
import xmltodict

from six import string_types
from xml.parsers.expat import ExpatError

from distutils.util import strtobool


log = logging.getLogger(__name__)

HAVE_KERBEROS = False
try:
    from requests_kerberos import HTTPKerberosAuth, REQUIRED, OPTIONAL, DISABLED
    HAVE_KERBEROS = True
except ImportError:
    log.debug("Failed to import requests-kerberos, Kerberos auth is not enabled")
    pass

HAVE_NTLM = False
try:
    from requests_ntlm import HttpNtlmAuth
    HAVE_NTLM = True
except ImportError as ie:
    log.debug("Failed to import requests_ntlm, NTLM auth is not enabled")
    pass

HAVE_CREDSSP = False
try:
    from requests_credssp import HttpCredSSPAuth
    HAVE_CREDSSP = True
except ImportError as ie:
    log.debug("Failed to import requests-credssp, CredSSP auth is not enabled")
    pass

unicode_type = type(u'')

from winrm.exceptions import InvalidCredentialsError, \
    WinRMError, WinRMTransportError, WinRMOperationTimeoutError

__all__ = ['Transport']


class Transport(object):

    def __init__(self, **kwargs):
        log.debug("Initialising transport with vars %s" % str(kwargs))
        self.endpoint = kwargs.get('endpoint')
        self.auth_method = kwargs.get('auth_method', 'auto')
        self.username = kwargs.get('username', None)
        self.password = kwargs.get('password', None)
        self.realm = kwargs.get('realm', None)
        self.ca_trust_path = kwargs.get('ca_trust_path', None)
        self.cert_pem = kwargs.get('cert_pem', None)
        self.cert_key_pem = kwargs.get('cert_key_pem', None)
        self.read_timeout_sec = kwargs.get('read_timeout_sec', None)
        self.server_cert_validation = kwargs.get('server_cert_validation', 'validate')
        self.kerberos_service = kwargs.get('kerberos_service', 'HTTP')
        self.kerberos_delegation = kwargs.get('kerberos_delegation', False)
        self.kerberos_hostname_override = kwargs.get('kerberos_hostname_override', None)
        self.credssp_disable_tlsv1_2 = kwargs.get('credssp_disable_tlsv1_2', False)
        self.proxies = kwargs.get('proxies', None)

        if self.server_cert_validation not in [None, 'validate', 'ignore']:
            raise WinRMError('invalid server_cert_validation mode: %s' % self.server_cert_validation)

        # defensively parse this to a bool
        if isinstance(self.kerberos_delegation, bool):
            self.kerberos_delegation = self.kerberos_delegation
        else:
            self.kerberos_delegation = bool(strtobool(str(self.kerberos_delegation)))

        self.default_headers = {
            'Content-Type': 'application/soap+xml;charset=UTF-8',
            'User-Agent': 'Python WinRM client',
        }

        # try to suppress user-unfriendly warnings from requests' vendored urllib3
        self._suppress_library_warnings()

        # validate credential requirements for various auth types
        self._validate_auth_method()
        self.session = None

    def _validate_auth_method(self):
        valid_auth_methods = ['basic', 'kerberos', 'ntlm', 'certificate', 'credssp', 'plaintext', 'ssl']
        if self.auth_method not in valid_auth_methods:
            raise WinRMError("requested auth method is %s, but valid auth methods are %s" %
                                          (self.auth_method, ' '.join(valid_auth_methods)))

        if self.auth_method == 'kerberos':
            if not HAVE_KERBEROS:
                raise WinRMError("requested auth method is kerberos, but requests_kerberos is not installed")
        elif self.auth_method == 'certificate' or (self.auth_method == 'ssl' and (self.cert_pem or self.cert_key_pem)):
            if self.auth_method == 'ssl':
                warnings.warn("auth_method 'ssl' has been deprecated, please use 'certificate' instead")
                self.auth_method = 'certificate'

            if not self.cert_pem or not self.cert_key_pem:
                raise InvalidCredentialsError("both cert_pem and cert_key_pem must be specified for cert auth")
            if not os.path.exists(self.cert_pem):
                raise InvalidCredentialsError("cert_pem file not found (%s)" % self.cert_pem)
            if not os.path.exists(self.cert_key_pem):
                raise InvalidCredentialsError("cert_key_pem file not found (%s)" % self.cert_key_pem)
        else:
            if self.auth_method in ['ssl', 'plaintext']:
                warnings.warn("auth_method '%s' has been deprecated, please use 'basic' instead'" % self.auth_method)
                self.auth_method = 'basic'

            if self.username is None:
                raise InvalidCredentialsError("auth method %s requires a username" % self.auth_method)
            if self.password is None:
                raise InvalidCredentialsError("auth method %s requires a password" % self.auth_method)

            if self.auth_method == 'ntlm' and not HAVE_NTLM:
                raise InvalidCredentialsError("requested auth method is ntlm, but requests_ntlm is not installed")
            if self.auth_method == 'credssp' and not HAVE_CREDSSP:
                raise WinRMError("requests auth method is credssp, but requests-credssp is not installed")

    def _suppress_library_warnings(self):
        try:
            from requests.packages.urllib3.exceptions import InsecurePlatformWarning
            warnings.simplefilter('ignore', category=InsecurePlatformWarning)
        except: pass # oh well, we tried...

        try:
            from requests.packages.urllib3.exceptions import SNIMissingWarning
            warnings.simplefilter('ignore', category=SNIMissingWarning)
        except: pass # oh well, we tried...

        # if we're explicitly ignoring validation, try to suppress InsecureRequestWarning, since the user opted-in
        if self.server_cert_validation == 'ignore':
            try:
                from requests.packages.urllib3.exceptions import InsecureRequestWarning
                warnings.simplefilter('ignore', category=InsecureRequestWarning)
            except: pass # oh well, we tried...

    def build_session(self):
        log.debug("Building a new Requests session")
        session = requests.Session()
        session.verify = self.server_cert_validation == 'validate'

        # configure proxies from HTTP/HTTPS_PROXY envvars
        session.trust_env = True
        settings = session.merge_environment_settings(url=self.endpoint, proxies=self.proxies, stream=None,
                                                      verify=None, cert=None)

        # we're only applying proxies from env, other settings are ignored
        session.proxies = settings['proxies']

        # Applying proxy settings
        session.proxies = settings['proxies']

        if self.auth_method == 'basic':
            log.debug("Connecting using HTTP Basic Authentication")
            session.auth = requests.auth.HTTPBasicAuth(username=self.username, password=self.password)
        elif self.auth_method == 'kerberos':
            log.debug("Connecting using Kerberos Authentication")
            # TODO: do argspec sniffing on extensions to ensure we're not setting bogus kwargs on older versions
            session.auth = HTTPKerberosAuth(mutual_authentication=REQUIRED,
                                            delegate=self.kerberos_delegation,
                                            force_preemptive=True,
                                            principal=self.username,
                                            hostname_override=self.kerberos_hostname_override,
                                            sanitize_mutual_error_response=False,
                                            service=self.kerberos_service)
        elif self.auth_method == 'ntlm':
            log.debug("Connecting using NTLM Authentication")
            session.auth = HttpNtlmAuth(username=self.username, password=self.password)
        elif self.auth_method == 'certificate':
            log.debug("Connecting using Certificate Authentication")
            session.cert = (self.cert_pem, self.cert_key_pem)
            session.headers['Authorization'] = \
                "http://schemas.dmtf.org/wbem/wsman/1/wsman/secprofile/https/mutual"
        elif self.auth_method == 'credssp':
            log.debug("Connecting using CredSSP Authentication")
            session.auth = HttpCredSSPAuth(username=self.username, password=self.password,
                                           disable_tlsv1_2=self.credssp_disable_tlsv1_2)

        session.headers.update(self.default_headers)

        return session

    def send_message(self, message):
        # TODO support kerberos/ntlm session with message encryption

        if not self.session:
            self.session = self.build_session()

        # urllib3 fails on SSL retries with unicode buffers- must send it a byte string
        # see https://github.com/shazow/urllib3/issues/717
        if isinstance(message, unicode_type):
            message = message.encode('utf-8')

        request = requests.Request('POST', self.endpoint, data=message)
        prepared_request = self.session.prepare_request(request)

        try:
            response = self.session.send(prepared_request, timeout=self.read_timeout_sec)
            response_text = response.text
            #print(response_text)
            response.raise_for_status()
            return response_text
        except requests.HTTPError as ex:
            if ex.response.status_code == 401:
                raise InvalidCredentialsError("the specified credentials were rejected by the server")
            self._raise_wsman_error(ex.response)

    @staticmethod
    def _raise_wsman_error(response):
        if response.content:
            response_text = response.content
            log.warning("Received error from Server, Message response: %s" % response_text)

            try:
                response_dict = xmltodict.parse(response_text)
            except ExpatError:
                response_dict = {}

            try:
                wsman_fault = response_dict['s:Envelope']['s:Body']['s:Fault']['s:Detail']['f:WSManFault']
                code = wsman_fault.get('@Code', 'Unknown')
                # Per http://msdn.microsoft.com/en-us/library/cc251676.aspx rule 3,
                if code == '2150858793':
                    raise WinRMOperationTimeoutError()

                fault_message = wsman_fault['f:Message']
                if isinstance(fault_message, string_types):
                    error_info = 'WSMan Code; %s, Error: %s' % (code, fault_message)
                else:
                    provider_fault = fault_message['f:ProviderFault']
                    provider = provider_fault.get('@provider', 'Unknown')
                    path = provider_fault.get('@path', 'Unknown')
                    error = provider_fault.get('#text', 'Unknown')
                    error_info = 'WSMan Code: %s, Provider: %s, Path: %s, Error: %s' % (code, provider, path, error)
            except KeyError:
                error_info = 'Error: Unknown %s' % response_text
            raise WinRMTransportError('http', 'Bad HTTP response returned from server. Code {0}: {1}'.format(
                response.status_code, error_info))
        else:
            raise WinRMTransportError('http',
                                      'Bad HTTP response returned from server. Code {0}'.format(response.status_code))
