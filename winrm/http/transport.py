import urllib2
from xml.etree import ElementTree
from winrm.exceptions import WinRMHTTPTransportError

class HttpTransport(object):
    def __init__(self, endpoint):
        self.endpoint = endpoint
        self.user_agent =  'Python WinRM client'
        self.timeout = 3600 # Set this to an unreasonable amount for now because WinRM has timeouts

    def send_request(self, message):
        headers = {'Content-Type' : 'application/soap+xml;charset=UTF-8', 'Content-Length' : len(message),
                   'User-Agent' : 'Python WinRM client'}
        request = urllib2.Request(self.endpoint, headers=headers)
        #password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
        #password_manager.add_password(None, self.endpoint, 'user', 'pass')
        #auth_manager = urllib2.HTTPBasicAuthHandler(password_manager)
        #opener = urllib2.build_opener(auth_manager)
        opener = urllib2.build_opener()
        urllib2.install_opener(opener)
        response = urllib2.urlopen(request, timeout=self.timeout)
        print response.getcode()
        print response.headers.getheader('content-type')
        if response.getcode() == 200:
            # Version 1.1 of WinRM adds the namespaces in the document instead of the envelope so we have to
            # add them ourselves here. This should have no affect version 2.
            doc = ElementTree.parse(response.read())
            #Ruby
            #doc = Nokogiri::XML(resp.http_body.content)
            #doc.collect_namespaces.each_pair do |k,v|
            #    doc.root.add_namespace((k.split(/:/).last),v) unless doc.namespaces.has_key?(k)
            #end
            #return doc
            return doc
        else:
            raise WinRMHTTPTransportError('Bad HTTP response returned from server ({0}).'.format(response.getcode()))

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
        super(HttpPlaintext, self).__init__(endpoint)
        #Ruby
        #@httpcli.set_auth(nil, user, pass)
        if disable_sspi:
            self.no_sspi_auth()
        if basic_auth_only:
            self.basic_auth_only()

class HttpSSL(HttpTransport):
    """Uses SSL to secure the transport"""
    def __init__(self, endpoint, username, password, ca_trust_path=None, disable_sspi=True, basic_auth_only=True):
        super(HttpSSL, self).__init__(endpoint)
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