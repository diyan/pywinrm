import urllib2
from urllib2 import URLError, HTTPError
from winrm.exceptions import WinRMTransportError

class HttpTransport(object):
    def __init__(self, endpoint, username, password):
        self.endpoint = endpoint
        self.username = username
        self.password = password
        self.user_agent =  'Python WinRM client'
        self.timeout = 3600 # Set this to an unreasonable amount for now because WinRM has timeouts

    def send_message(self, message):
        headers = {'Content-Type' : 'application/soap+xml;charset=UTF-8',
                   'Content-Length' : len(message),
                   'User-Agent' : 'Python WinRM client'}
        password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
        password_manager.add_password(None, self.endpoint, self.username, self.password)
        auth_manager = urllib2.HTTPBasicAuthHandler(password_manager)
        opener = urllib2.build_opener(auth_manager)
        urllib2.install_opener(opener)
        request = urllib2.Request(self.endpoint, data=message, headers=headers)
        try:
            response = urllib2.urlopen(request, timeout=self.timeout)
            # Version 1.1 of WinRM adds the namespaces in the document instead of the envelope so we have to
            # add them ourselves here. This should have no affect version 2.
            response_text = response.read()
            return response_text
            #doc = ElementTree.fromstring(response.read())
            #Ruby
            #doc = Nokogiri::XML(resp.http_body.content)
            #doc.collect_namespaces.each_pair do |k,v|
            #    doc.root.add_namespace((k.split(/:/).last),v) unless doc.namespaces.has_key?(k)
            #end
            #return doc
            #return doc
        except HTTPError as ex:
            error_message = 'Bad HTTP response returned from server. Code {0}'.format(ex.code)
            if ex.msg:
                error_message += ', {0}'.format(ex.msg)
            raise WinRMTransportError(error_message)
        except URLError as ex:
            raise WinRMTransportError(ex.message)

    def basic_auth_only(self):
        #here we should remove handler for any authentication handlers other than basic
        # but maybe leave original credentials

        # auths = @httpcli.www_auth.instance_variable_get('@authenticator')
        # auths.delete_if {|i| i.scheme !~ /basic/i}
        # drop all variables in auths if they not contains "basic" as insensitive.
        pass

    def no_sspi_auth(self):
        # here we should remove handler for Negotiate/NTLM negotiation
        # but maybe leave original credentials
        pass

class HttpPlaintext(HttpTransport):
    def __init__(self, endpoint, username='', password='', disable_sspi=True, basic_auth_only=True):
        super(HttpPlaintext, self).__init__(endpoint, username, password)
        if disable_sspi:
            self.no_sspi_auth()
        if basic_auth_only:
            self.basic_auth_only()

class HttpSSL(HttpTransport):
    """Uses SSL to secure the transport"""
    def __init__(self, endpoint, username, password, ca_trust_path=None, disable_sspi=True, basic_auth_only=True):
        super(HttpSSL, self).__init__(endpoint, username, password)
        #Ruby
        #@httpcli.set_auth(endpoint, user, pass)
        #@httpcli.ssl_config.set_trust_ca(ca_trust_path) unless ca_trust_path.nil?
        if disable_sspi:
            self.no_sspi_auth()
        if basic_auth_only:
            self.basic_auth_only()

class HttpGSSAPI(HttpTransport):
    def __init__(self, endpoint, realm, service=None, keytab=None, opts=None):
        """
        Uses Kerberos/GSSAPI to authenticate and encrypt messages
        @param string endpoint: the WinRM webservice endpoint
        @param string realm: the Kerberos realm we are authenticating to
        @param string service: the service name, default is HTTP
        @param string keytab: the path to a keytab file if you are using one
        """
        super(HttpGSSAPI, self).__init__(endpoint)
        # Remove the GSSAPI auth from HTTPClient because we are doing our own thing
        #Ruby
        #auths = @httpcli.www_auth.instance_variable_get('@authenticator')
        #auths.delete_if {|i| i.is_a?(HTTPClient::SSPINegotiateAuth)}
        #service ||= 'HTTP'
        #@service = "#{service}/#{@endpoint.host}@#{realm}"
        #init_krb

        def set_auth(self, username, password):
            raise NotImplementedError

        def send_request(self, message):
            raise NotImplementedError

        def _init_krb(self):
            raise NotImplementedError

        def _winrm_encrypt(self, string):
            raise NotImplementedError

        def _winrm_decrypt(self, string):
            raise NotImplementedError