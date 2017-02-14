from __future__ import unicode_literals
from contextlib import contextmanager
import re
import sys
import os
import weakref

is_py2 = sys.version[0] == '2'

if is_py2:
    from urlparse import urlsplit, urlunsplit
    # use six for this instead?
    unicode_type = type(u'')
else:
    from urllib.parse import urlsplit, urlunsplit
    # use six for this instead?
    unicode_type = type(u'')

import requests
import requests.auth
import warnings
from distutils.util import strtobool
from requests.hooks import default_hooks
from requests.adapters import HTTPAdapter

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

from winrm.exceptions import BasicAuthDisabledError, InvalidCredentialsError, \
    WinRMError, WinRMTransportError, WinRMOperationTimeoutError
from winrm.encryption import Encryption

__all__ = ['Transport']

class Transport(object):
    
    def __init__(
            self, endpoint, username=None, password=None, realm=None,
            service=None, keytab=None, ca_trust_path=None, cert_pem=None,
            cert_key_pem=None, read_timeout_sec=None, server_cert_validation='validate',
            kerberos_delegation=False,
            kerberos_hostname_override=None,
            auth_method='auto',
            message_encryption='auto'):
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
        self.encryption = None # The Pywinrm Encryption class used to encrypt/decrypt messages
        if self.message_encryption not in ['auto', 'always', 'never']:
            raise WinRMError(
                "invalid message_encryption arg: %s. Should be 'auto', 'always', or 'never'" % self.message_encryption)


    def build_session(self):
        session = requests.Session()

        session.verify = self.server_cert_validation == 'validate'

        # configure proxies from HTTP/HTTPS_PROXY envvars
        session.trust_env = True
        settings = session.merge_environment_settings(url=self.endpoint, proxies={}, stream=None,
                                                      verify=None, cert=None)

        # we're only applying proxies from env, other settings are ignored
        session.proxies = settings['proxies']

        encryption_available = False
        if self.auth_method == 'kerberos':
            if not HAVE_KERBEROS:
                raise WinRMError("requested auth method is kerberos, but requests_kerberos is not installed")
            # TODO: do argspec sniffing on extensions to ensure we're not setting bogus kwargs on older versions
            session.auth = HTTPKerberosAuth(mutual_authentication=REQUIRED, delegate=self.kerberos_delegation,
                                            force_preemptive=True, principal=self.username,
                                            hostname_override=self.kerberos_hostname_override,
                                            sanitize_mutual_error_response=False)
        elif self.auth_method in ['certificate','ssl']:
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
            session.auth = HttpNtlmAuth(username=self.username, password=self.password)
            # check if requests_ntlm has the session_security attribute available for encryption
            encryption_available = hasattr(session.auth, 'session_security')
        # TODO: ssl is not exactly right here- should really be client_cert
        elif self.auth_method in ['basic','plaintext']:
            session.auth = requests.auth.HTTPBasicAuth(username=self.username, password=self.password)
        elif self.auth_method == 'credssp':
            if not HAVE_CREDSSP:
                raise WinRMError("requests auth method is credssp, but requests-credssp is not installed")
            session.auth = HttpCredSSPAuth(username=self.username, password=self.password)
        else:
            raise WinRMError("unsupported auth method: %s" % self.auth_method)

        session.headers.update(self.default_headers)
        self.session = session

        # Will check the current config and see if we need to setup message encryption
        if self.message_encryption == 'always' and not encryption_available:
            raise WinRMError("message encryption is set to 'always' but the selected auth method %s does not support it" % self.auth_method)
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

            # Per http://msdn.microsoft.com/en-us/library/cc251676.aspx rule 3,
            # should handle this 500 error and retry receiving command output.
            if b'http://schemas.microsoft.com/wbem/wsman/1/windows/shell/Receive' in message and b'Code="2150858793"' in response_text:
                raise WinRMOperationTimeoutError()

            error_message = 'Bad HTTP response returned from server. Code {0}'.format(ex.response.status_code)

            raise WinRMTransportError('http', error_message)

    def _get_message_response_text(self, response):
        if self.encryption:
            response_text = self.encryption.parse_encrypted_response(response)
        else:
            response_text = response.content
        return response_text