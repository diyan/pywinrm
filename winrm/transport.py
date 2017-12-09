from __future__ import unicode_literals
import sys
import os
import inspect

is_py2 = sys.version[0] == '2'

if is_py2:
    # use six for this instead?
    unicode_type = type(u'')
else:
    # use six for this instead?
    unicode_type = type(u'')

import requests
import requests.auth
import warnings
from distutils.util import strtobool

HAVE_KERBEROS = False
try:
    from requests_kerberos import HTTPKerberosAuth, REQUIRED, OPTIONAL, DISABLED

    HAVE_KERBEROS = True
except ImportError:
    pass

HAVE_NTLM = False
try:
    from requests_ntlm import HttpNtlmAuth

    HAVE_NTLM = True
except ImportError as ie:
    pass

HAVE_CREDSSP = False
try:
    from requests_credssp import HttpCredSSPAuth

    HAVE_CREDSSP = True
except ImportError as ie:
    pass

from winrm.exceptions import InvalidCredentialsError, WinRMError, \
    WinRMTransportError
from winrm.encryption import Encryption

__all__ = ['Transport']


class UnsupportedAuthArgument(Warning):
    pass


class Transport(object):
    def __init__(
            self, endpoint, username=None, password=None, realm=None,
            service=None, keytab=None, ca_trust_path=None, cert_pem=None,
            cert_key_pem=None, read_timeout_sec=None, server_cert_validation='validate',
            kerberos_delegation=False,
            kerberos_hostname_override=None,
            auth_method='auto',
            message_encryption='auto',
            credssp_disable_tlsv1_2=False,
            send_cbt=True):
        self.endpoint = endpoint
        self.username = username
        self.password = password
        self.realm = realm
        self.service = service
        self.keytab = keytab
        self.ca_trust_path = ca_trust_path
        self.cert_pem = cert_pem
        self.cert_key_pem = cert_key_pem
        self.read_timeout_sec = read_timeout_sec
        self.server_cert_validation = server_cert_validation
        self.kerberos_hostname_override = kerberos_hostname_override
        self.message_encryption = message_encryption
        self.credssp_disable_tlsv1_2 = credssp_disable_tlsv1_2
        self.send_cbt = send_cbt

        if self.server_cert_validation not in [None, 'validate', 'ignore']:
            raise WinRMError('invalid server_cert_validation mode: %s' % self.server_cert_validation)

        # defensively parse this to a bool
        if isinstance(kerberos_delegation, bool):
            self.kerberos_delegation = kerberos_delegation
        else:
            self.kerberos_delegation = bool(strtobool(str(kerberos_delegation)))

        self.auth_method = auth_method
        self.default_headers = {
            'Content-Type': 'application/soap+xml;charset=UTF-8',
            'User-Agent': 'Python WinRM client',
        }

        # try to suppress user-unfriendly warnings from requests' vendored urllib3
        try:
            from requests.packages.urllib3.exceptions import InsecurePlatformWarning
            warnings.simplefilter('ignore', category=InsecurePlatformWarning)
        except:
            pass  # oh well, we tried...

        try:
            from requests.packages.urllib3.exceptions import SNIMissingWarning
            warnings.simplefilter('ignore', category=SNIMissingWarning)
        except:
            pass  # oh well, we tried...

        # if we're explicitly ignoring validation, try to suppress InsecureRequestWarning, since the user opted-in
        if self.server_cert_validation == 'ignore':
            try:
                from requests.packages.urllib3.exceptions import InsecureRequestWarning
                warnings.simplefilter('ignore', category=InsecureRequestWarning)
            except: pass # oh well, we tried...
            
            try:
                from urllib3.exceptions import InsecureRequestWarning
                warnings.simplefilter('ignore', category=InsecureRequestWarning)
            except: pass # oh well, we tried...

        # validate credential requirements for various auth types
        if self.auth_method != 'kerberos':
            if self.auth_method == 'certificate' or (
                            self.auth_method == 'ssl' and (self.cert_pem or self.cert_key_pem)):
                if not self.cert_pem or not self.cert_key_pem:
                    raise InvalidCredentialsError("both cert_pem and cert_key_pem must be specified for cert auth")
                if not os.path.exists(self.cert_pem):
                    raise InvalidCredentialsError("cert_pem file not found (%s)" % self.cert_pem)
                if not os.path.exists(self.cert_key_pem):
                    raise InvalidCredentialsError("cert_key_pem file not found (%s)" % self.cert_key_pem)

            else:
                if not self.username:
                    raise InvalidCredentialsError("auth method %s requires a username" % self.auth_method)
                if self.password is None:
                    raise InvalidCredentialsError("auth method %s requires a password" % self.auth_method)

        self.session = None

        # Used for encrypting messages
        self.encryption = None  # The Pywinrm Encryption class used to encrypt/decrypt messages
        if self.message_encryption not in ['auto', 'always', 'never']:
            raise WinRMError(
                "invalid message_encryption arg: %s. Should be 'auto', 'always', or 'never'" % self.message_encryption)

    def build_session(self):
        session = requests.Session()

        session.verify = self.server_cert_validation == 'validate'
        if session.verify and self.ca_trust_path:
                session.verify = self.ca_trust_path

        # configure proxies from HTTP/HTTPS_PROXY envvars
        session.trust_env = True
        settings = session.merge_environment_settings(url=self.endpoint, proxies={}, stream=None,
                                                      verify=None, cert=None)

        # we're only applying proxies and/or verify from env, other settings are ignored
        session.proxies = settings['proxies']

        if settings['verify'] is not None or self.ca_trust_path is not None:
            session.verify = self.ca_trust_path or settings['verify']

        encryption_available = False

        if self.auth_method == 'kerberos':
            if not HAVE_KERBEROS:
                raise WinRMError("requested auth method is kerberos, but requests_kerberos is not installed")

            man_args = dict(
                mutual_authentication=REQUIRED,
            )
            opt_args = dict(
                delegate=self.kerberos_delegation,
                force_preemptive=True,
                principal=self.username,
                hostname_override=self.kerberos_hostname_override,
                sanitize_mutual_error_response=False,
                service=self.service,
                send_cbt=self.send_cbt
            )
            kerb_args = self._get_args(man_args, opt_args, HTTPKerberosAuth.__init__)
            session.auth = HTTPKerberosAuth(**kerb_args)
            encryption_available = hasattr(session.auth, 'winrm_encryption_available') and session.auth.winrm_encryption_available
        elif self.auth_method in ['certificate', 'ssl']:
            if self.auth_method == 'ssl' and not self.cert_pem and not self.cert_key_pem:
                # 'ssl' was overloaded for HTTPS with optional certificate auth,
                # fall back to basic auth if no cert specified
                session.auth = requests.auth.HTTPBasicAuth(username=self.username, password=self.password)
            else:
                session.cert = (self.cert_pem, self.cert_key_pem)
                session.headers['Authorization'] = \
                    "http://schemas.dmtf.org/wbem/wsman/1/wsman/secprofile/https/mutual"
        elif self.auth_method == 'ntlm':
            if not HAVE_NTLM:
                raise WinRMError("requested auth method is ntlm, but requests_ntlm is not installed")
            man_args = dict(
                username=self.username,
                password=self.password
            )
            opt_args = dict(
                send_cbt=self.send_cbt
            )
            ntlm_args = self._get_args(man_args, opt_args, HttpNtlmAuth.__init__)
            session.auth = HttpNtlmAuth(**ntlm_args)
            # check if requests_ntlm has the session_security attribute available for encryption
            encryption_available = hasattr(session.auth, 'session_security')
        # TODO: ssl is not exactly right here- should really be client_cert
        elif self.auth_method in ['basic', 'plaintext']:
            session.auth = requests.auth.HTTPBasicAuth(username=self.username, password=self.password)
        elif self.auth_method == 'credssp':
            if not HAVE_CREDSSP:
                raise WinRMError("requests auth method is credssp, but requests-credssp is not installed")
            session.auth = HttpCredSSPAuth(username=self.username, password=self.password,
                                               disable_tlsv1_2=self.credssp_disable_tlsv1_2)
            encryption_available = hasattr(session.auth, 'wrap') and hasattr(session.auth, 'unwrap')
        else:
            raise WinRMError("unsupported auth method: %s" % self.auth_method)

        session.headers.update(self.default_headers)
        self.session = session

        # Will check the current config and see if we need to setup message encryption
        if self.message_encryption == 'always' and not encryption_available:
            raise WinRMError(
                "message encryption is set to 'always' but the selected auth method %s does not support it" % self.auth_method)
        elif encryption_available:
            if self.message_encryption == 'always':
                self.setup_encryption()
            elif self.message_encryption == 'auto' and not self.endpoint.lower().startswith('https'):
                self.setup_encryption()

    def setup_encryption(self):
        # Security context doesn't exist, sending blank message to initialise context
        request = requests.Request('POST', self.endpoint, data=None)
        prepared_request = self.session.prepare_request(request)
        self._send_message_request(prepared_request, '')
        self.encryption = Encryption(self.session, self.auth_method)

    def send_message(self, message):
        if not self.session:
            self.build_session()

        # urllib3 fails on SSL retries with unicode buffers- must send it a byte string
        # see https://github.com/shazow/urllib3/issues/717
        if isinstance(message, unicode_type):
            message = message.encode('utf-8')

        if self.encryption:
            prepared_request = self.encryption.prepare_encrypted_request(self.session, self.endpoint, message)
        else:
            request = requests.Request('POST', self.endpoint, data=message)
            prepared_request = self.session.prepare_request(request)

        response = self._send_message_request(prepared_request, message)
        return self._get_message_response_text(response)

    def _send_message_request(self, prepared_request, message):
        try:
            response = self.session.send(prepared_request, timeout=self.read_timeout_sec)
            response.raise_for_status()
            return response
        except requests.HTTPError as ex:
            if ex.response.status_code == 401:
                raise InvalidCredentialsError("the specified credentials were rejected by the server")
            if ex.response.content:
                response_text = self._get_message_response_text(ex.response)
            else:
                response_text = ''


            raise WinRMTransportError('http', ex.response.status_code, response_text)

    def _get_message_response_text(self, response):
        if self.encryption:
            response_text = self.encryption.parse_encrypted_response(response)
        else:
            response_text = response.content
        return response_text

    def _get_args(self, mandatory_args, optional_args, function):
        argspec = set(inspect.getargspec(function).args)
        function_args = dict()
        for name, value in mandatory_args.items():
            if name in argspec:
                function_args[name] = value
            else:
                raise Exception("Function %s does not contain mandatory arg "
                                "%s, check installed version with pip list"
                                % (str(function), name))

        for name, value in optional_args.items():
            if name in argspec:
                function_args[name] = value
            else:
                warnings.warn("Function %s does not contain optional arg %s, "
                              "check installed version with pip list"
                              % (str(function), name))

        return function_args
