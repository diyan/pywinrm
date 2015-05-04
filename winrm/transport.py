from __future__ import unicode_literals
from contextlib import contextmanager
import re
import sys
import weakref
is_py2 = sys.version[0] == '2'
if is_py2:
    from urlparse import urlsplit, urlunsplit
else:
    from urllib.parse import urlsplit, urlunsplit

import requests
import requests.auth
from requests.hooks import default_hooks
from requests.adapters import HTTPAdapter

HAVE_KERBEROS = False
try:
    import kerberos
    import requests_kerberos
    HAVE_KERBEROS = True
except ImportError:
    pass

HAVE_NTLM = False
try:
    from ntlm import ntlm
    HAVE_NTLM = True
except ImportError:
    pass

from winrm.exceptions import BasicAuthDisabledError, InvalidCredentialsError, \
    WinRMError

__all__ = ['Transport']

if HAVE_KERBEROS:

    class KerberosAuth(requests_kerberos.HTTPKerberosAuth):
        '''
        Custom Kerberos authentication provider that allows specifying a realm.
        '''
    
        def __init__(self, mutual_authentication=requests_kerberos.REQUIRED, service='HTTP', realm=None, auth_scheme='Negotiate'):
            super(KerberosAuth, self).__init__(mutual_authentication, service)
            self.realm = realm
            self.auth_scheme = auth_scheme
            self.regex = re.compile(r'(?:.*,)*\s*%s\s*([^,]*),?' % self.auth_scheme, re.I)

        @contextmanager
        def _replace_realm(self, response):
            original_url = response.url
            if self.realm:
                parts = urlsplit(original_url)
                netloc = parts.netloc.replace(parts.hostname, self.realm)
                response.url = urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))
            yield
            response.url = original_url

        @contextmanager
        def _replace_regex(self):
            original_regex = getattr(requests_kerberos.kerberos_._negotiate_value, 'regex', None)
            requests_kerberos.kerberos_._negotiate_value.regex = self.regex
            yield
            if original_regex:
                setattr(requests_kerberos.kerberos_._negotiate_value, 'regex', original_regex)
            else:
                delattr(requests_kerberos.kerberos_._negotiate_value, 'regex')

        def generate_request_header(self, response):
            with self._replace_regex():
                with self._replace_realm(response):
                    result = super(KerberosAuth, self).generate_request_header(response)
                    if result is not None:
                        result = result.replace('Negotiate ', '%s ' % self.auth_scheme)
                    return result

        def handle_401(self, response, **kwargs):
            with self._replace_regex():
                return super(KerberosAuth, self).handle_401(response, **kwargs)

        def handle_other(self, response):
            with self._replace_regex():
                return super(KerberosAuth, self).handle_other(response)

        def authenticate_server(self, response):
            with self._replace_regex():
                with self._replace_realm(response):
                    return super(KerberosAuth, self).authenticate_server(response)

if HAVE_NTLM:

    class NtlmAuth(requests.auth.AuthBase):
        '''
        HTTP NTLM Authentication Handler for Requests.
        Supports pass-the-hash.
        Copied from https://github.com/requests/requests-ntlm/ with changes to
        support alternate auth schemes.
        '''

        def __init__(self, username, password, session=None, auth_scheme='NTLM'):
            try:
                self.domain, self.username = username.split('\\', 1)
            except ValueError:
                raise ValueError(
                    r"username should be in 'domain\\username' format."
                )

            self.domain = self.domain.upper()
            self.password = password
            self.adapter = HTTPAdapter()

            # Keep a weak reference to the Session, if one is in use.
            # This is to avoid a circular reference.
            self.session = weakref.ref(session) if session else None
            self.auth_scheme = auth_scheme

        def retry_using_http_NTLM_auth(self, auth_header_field, auth_header,
                                       response, args):
            """Attempt to authenticate using HTTP NTLM challenge/response."""
            if auth_header in response.request.headers:
                return response

            request = response.request.copy()

            content_length = int(request.headers.get('Content-Length', '0'))
            if hasattr(request.body, 'seek'):
                if content_length > 0:
                    request.body.seek(-content_length, 1)
                else:
                    request.body.seek(0, 0)

            adapter = self.adapter
            if self.session:
                session = self.session()
                if session:
                    adapter = session.get_adapter(response.request.url)

            # initial auth header with username. will result in challenge
            msg = "%s\\%s" % (self.domain, self.username) if self.domain else self.username
            auth = '%s %s' % (self.auth_scheme, ntlm.create_NTLM_NEGOTIATE_MESSAGE(msg))
            request.headers[auth_header] = auth

            # A streaming response breaks authentication.
            # This can be fixed by not streaming this request, which is safe
            # because the returned response3 will still have stream=True set if
            # specified in args. In addition, we expect this request to give us a
            # challenge and not the real content, so the content will be short
            # anyway.
            args_nostream = dict(args, stream=False)
            response2 = adapter.send(request, **args_nostream)

            # needed to make NTLM auth compatible with requests-2.3.0
            response2.content

            # this is important for some web applications that store
            # authentication-related info in cookies (it took a long time to
            # figure out)
            if response2.headers.get('set-cookie'):
                request.headers['Cookie'] = response2.headers.get('set-cookie')

            # get the challenge
            auth_header_value = response2.headers[auth_header_field]
            ntlm_header_value = list(filter(
                lambda s: s.startswith('%s ' % self.auth_scheme), auth_header_value.split(',')
            ))[0].strip()
            ServerChallenge, NegotiateFlags = ntlm.parse_NTLM_CHALLENGE_MESSAGE(
                ntlm_header_value[(len(self.auth_scheme) + 1):]
            )

            # build response
            request = request.copy()
            auth = '%s %s' % (self.auth_scheme, ntlm.create_NTLM_AUTHENTICATE_MESSAGE(
                ServerChallenge, self.username, self.domain, self.password,
                NegotiateFlags
            ))
            request.headers[auth_header] = auth

            response3 = adapter.send(request, **args)

            # Update the history.
            response3.history.append(response)
            response3.history.append(response2)

            return response3

        def response_hook(self, response, **kwargs):
            """The actual hook handler."""
            www_authenticate = response.headers.get('www-authenticate', '').lower()
            www_auth_schemes = [x.strip().split()[0] for x in www_authenticate.split(',') if x.strip()]
            if response.status_code == 401 and self.auth_scheme.lower() in www_auth_schemes:
                return self.retry_using_http_NTLM_auth('www-authenticate',
                                                       'Authorization', response, kwargs)

            proxy_authenticate = response.headers.get('proxy-authenticate', '').lower()
            proxy_auth_schemes = [x.strip().split()[0] for x in proxy_authenticate.split(',') if x.strip()]
            if response.status_code == 407 and self.auth_scheme.lower() in proxy_auth_schemes:
                return self.retry_using_http_NTLM_auth('proxy-authenticate',
                                                       'Proxy-authorization', response,
                                                       kwargs)

            return response

        def __call__(self, request):
            # we must keep the connection because NTLM authenticates the
            # connection, not single requests
            request.headers["Connection"] = "Keep-Alive"

            request.register_hook('response', self.response_hook)
            return request


class MultiAuth(requests.auth.AuthBase):

    def __init__(self, session=None):
        self.auth_map = {}
        self.current_auth = None
        self.session = weakref.ref(session) if session else None

    def add_auth(self, scheme, auth_instance):
        auth_instances = self.auth_map.setdefault(scheme.lower(), [])
        auth_instances.append(auth_instance)

    def handle_401(self, response, **kwargs):
        """Takes the given response and tries digest-auth, if needed."""

        original_request = response.request.copy()
        www_authenticate = response.headers.get('www-authenticate', '').lower()
        www_auth_schemes = [x.strip().split()[0] for x in www_authenticate.split(',') if x.strip()]
        auths_to_try = [x for x in www_auth_schemes if x in [y.lower() for y in self.auth_map.keys()]]

        for auth_scheme in auths_to_try:
            for auth_instance in self.auth_map[auth_scheme]:
                #print 'trying', auth_instance, 'for', auth_scheme

                # Consume content and release the original connection
                # to allow our new request to reuse the same one.
                response.content
                response.raw.release_conn()
                prepared_request = original_request.copy()
                prepared_request.hooks = default_hooks()
                prepared_request.prepare_auth(auth_instance)

                adapter = HTTPAdapter()
                if self.session:
                    adapter = self.session() or adapter
                new_response = adapter.send(prepared_request, **kwargs)
                new_response.history.append(response)
                new_response.request = prepared_request
        
                if new_response.status_code != 401:
                    #print auth_instance, 'successful for', auth_scheme
                    self.current_auth = auth_instance
                    return new_response
                response = new_response

        return response

    def handle_response(self, response, **kwargs):
        if response.status_code == 401 and not self.current_auth:
            response = self.handle_401(response, **kwargs)
        return response

    def __call__(self, request):
        if self.current_auth:
            request = self.current_auth(request)
        request.register_hook('response', self.handle_response)
        return request


class Transport(object):
    
    def __init__(
            self, endpoint, username=None, password=None, realm=None,
            service=None, keytab=None, ca_trust_path=None, cert_pem=None,
            cert_key_pem=None, timeout=None):
        self.endpoint = endpoint
        self.username = username
        self.password = password
        self.realm = realm
        self.service = service
        self.keytab = keytab
        self.ca_trust_path = ca_trust_path
        self.cert_pem = cert_pem
        self.cert_key_pem = cert_key_pem
        self.timeout = timeout
        self.default_headers = {
            'Content-Type': 'application/soap+xml;charset=UTF-8',
            'User-Agent': 'Python WinRM client',
        }
        self.session = None

    def build_session(self):
        session = requests.Session()
        
        session.auth = MultiAuth(session)
        if HAVE_KERBEROS:
            for auth_scheme in ('Negotiate', 'Kerberos'):
                kerberos_auth = KerberosAuth(mutual_authentication=requests_kerberos.OPTIONAL, realm=self.realm, auth_scheme=auth_scheme)
                session.auth.add_auth(auth_scheme, kerberos_auth)

        if HAVE_NTLM and self.username and '\\' in self.username and self.password:
            for auth_scheme in ('Negotiate', 'NTLM'):
                ntlm_auth = NtlmAuth(self.username, self.password, session, auth_scheme)
                session.auth.add_auth(auth_scheme, ntlm_auth)

        if self.username and self.password:
            basic_auth = requests.auth.HTTPBasicAuth(self.username, self.password)
            session.auth.add_auth('Basic', basic_auth)

        if self.cert_pem:
            if self.cert_key_pem:
                session.cert = (self.cert_pem, self.cert_key_pem)
            else:
                session.cert = self.cert_pem

        session.headers.update(self.default_headers)

        return session

    def send_message(self, message):
        # TODO support kerberos session with message encryption

        if not self.session:
            self.session = self.build_session()
        request = requests.Request('POST', self.endpoint, data=message)
        prepared_request = self.session.prepare_request(request)
        try:
            response = self.session.send(prepared_request, verify=False, timeout=self.timeout)
            response.raise_for_status()
            # Version 1.1 of WinRM adds the namespaces in the document instead of the envelope so we have to
            # add them ourselves here. This should have no affect version 2.
            response_text = response.text
            return response_text
        except requests.HTTPError as ex:
            if ex.response.status_code == 401:
                server_auth = ex.response.headers['WWW-Authenticate'].lower()
                client_auth = list(self.session.auth.auth_map.keys())
                # Client can do only the Basic auth but server can not
                if 'basic' not in server_auth and len(client_auth) == 1 \
                        and client_auth[0] == 'basic':
                    raise BasicAuthDisabledError()
                # Both client and server can do a Basic auth
                if 'basic' in server_auth and 'basic' in client_auth:
                    raise InvalidCredentialsError()
            if ex.response:
                response_text = ex.response.content
            else:
                response_text = ''
            # Per http://msdn.microsoft.com/en-us/library/cc251676.aspx rule 3,
            # should handle this 500 error and retry receiving command output.
            if 'http://schemas.microsoft.com/wbem/wsman/1/windows/shell/Receive' in message and 'Code="2150858793"' in response_text:
                # TODO raise TimeoutError here instead of just return text
                return response_text
            error_message = 'Bad HTTP response returned from server. Code {0}'.format(ex.response.status_code)
            #if ex.msg:
            #    error_message += ', {0}'.format(ex.msg)
            raise WinRMError('http', error_message)
