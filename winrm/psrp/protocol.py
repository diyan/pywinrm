import uuid
import xmltodict

from winrm.exceptions import WinRMError
from winrm.contants import Actions, Constants, MessageTypes
from winrm.psrp.fragmenter import Fragmenter
from winrm.psrp.messages import SessionCapability, InitRunspacePool, Message

class PsrpHandler(object):
    def __init__(self, transport, read_timeout_sec=Constants.DEFAULT_READ_TIMEOUT_SEC,
            operation_timeout_sec=Constants.DEFAULT_OPERATION_TIMEOUT_SEC,
            locale=Constants.DEFAULT_LOCALE, encoding=Constants.DEFAULT_ENCODING):

        server_config = self.get_server_config()
        self.read_timeout_sec = read_timeout_sec
        self.operation_timeout_sec = operation_timeout_sec
        self.max_envelope_size = server_config['max_envelope_size']
        self.locale = locale
        self.encoding = encoding
        self.transport = transport

        self.fragmenter = Fragmenter(self.max_envelope_size)


    def create_runspace_pool(self):
        session_capability = SessionCapability()
        session_capability_msg = session_capability.create_message_data("2.2", "2.0", "1.1.0.1")

        init_runspace_pool = InitRunspacePool()
        init_runspace_pool_msg= init_runspace_pool.create_message_data("1", "2")

        sc_msg = Message()
        sc = sc_msg.create_message(Message.DESTINATION_SERVER, MessageTypes.SESSION_CAPABILITY, uuid.uuid4(), uuid.uuid4(), session_capability_msg)

        init_pool_msg = Message()
        init_pool = init_pool_msg.create_message(Message.DESTINATION_SERVER, MessageTypes.INIT_RUNSPACEPOOL, uuid.uuid4(), uuid.uuid4(), init_runspace_pool_msg)

        a = ''

    def get_server_config(self):
        """
        [MS-WSMV] v30 2016-07-14
        2.2.4.10 ConfigType

        ConfigType is the container for WSMV service configuration data.
        If not running under an admin we cannot retrieve these values and will
        revert to the default value

        :return: dict:
            max_batch_items: Maximum number of elements in a Pull response, min 1, max 4294967295, default 20
            max_envelope_size_kb: Maximum SOAP data in kilobytes, min 32, max 4294967295, default 150
            max_provider_requests: Maximum number of concurrent requests to WSMV, min 1, max 4294967295, default 25
            max_timeout_ms: Maximum timeout in milliseconds for any requests except Pull, min 500, max 4294967295, default 60000
        """
        try:
            resource_uri = 'http://schemas.microsoft.com/wbem/wsman/1/config'
            res = self._send(Actions.GET, resource_uri)
            config = {
                'max_batch_items': res['s:Envelope']['s:Body']['cfg:Config']['cfg:MaxBatchItems'],
                'max_envelope_size_kb': res['s:Envelope']['s:Body']['cfg:Config']['cfg:MaxEnvelopeSizekb'],
                'max_provider_requests': res['s:Envelope']['s:Body']['cfg:Config']['cfg:MaxProviderRequests'],
                'max_timeout_ms': res['s:Envelope']['s:Body']['cfg:Config']['cfg:MaxTimeoutms']
            }
        except Exception:
            # Not running as admin, reverting to defauls
            config = {
                'max_batch_items': '20',
                'max_envelope_size_kb': '150',
                'max_provider_requests': '25',
                'max_timeout_ms': '60000'
            }

        return config

    def _send(self, action, resource_uri, body=None, selector_set=None, option_set=None):
        """
        Will send the obj to the server valid the response relates to the request

        :param action: The WSMV action to send through
        :param resource_uri: The WSMV resource_uri
        :param body: The WSMV body which is created by winrm.wsmv.complex_types
        :param selector_set: To add optional selector sets header values to the headers
        :param option_set: To add optional option sets header values to the headers
        :return: A dict which is the xml conversion from the server
        """
        headers = self._create_headers(action, resource_uri, selector_set, option_set)
        message_id = headers['a:MessageID']
        message = self._create_message(headers, body)

        response_xml = self.transport.send_message(message)
        response = xmltodict.parse(response_xml, encoding=self.encoding)
        response_relates_id = response['s:Envelope']['s:Header']['a:RelatesTo']

        if message_id != response_relates_id:
            raise WinRMError("Response related to Message ID: '%s' does not match request Message ID: '%s'" % (
            response_relates_id, message_id))

        return response

    def _create_headers(self, action, resource_uri, selector_set, option_set):
        headers = {
            'a:Action': {
                '@mustUnderstand': 'true',
                '#text': action
            },
            'p:DataLocale': {
                '@mustUnderstand': 'false',
                '@xml:lang': self.locale
            },
            'w:Locale': {
                '@mustUnderstand': 'false',
                '@xml:lang': self.locale
            },
            'a:To': self.transport.endpoint,
            'w:ResourceURI': {
                '@mustUnderstand': 'true',
                '#text': resource_uri
            },
            'w:OperationTimeout': 'PT{0}S'.format(int(self.operation_timeout_sec)),
            'a:ReplyTo': {
                "a:Address": {
                    "@mustUnderstand": 'true',
                    '#text': 'http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous'
                }
            },
            'w:MaxEnvelopeSize': '{0}'.format(self.max_envelope_size),
            'a:MessageID': 'uuid:{0}'.format(uuid.uuid4())
        }

        if selector_set:
            selector_set_list = []
            for key, value in selector_set.items():
                selector_set_list.append({'@Name': key, '#text': value})
            headers['w:SelectorSet'] = {'w:Selector': selector_set_list}

        if option_set:
            option_set_list = []
            for key, value in option_set.items():
                option_set_list.append({'@Name': key, '#text': value})
            headers['w:OptionSet'] = {'w:Option': option_set_list}
        return headers

    def _create_message(self, headers, body):
        message = {
            's:Envelope': {}
        }
        for alias, namespace in Constants.NAMESPACES.items():
            message['s:Envelope']["@xmlns:%s" % alias] = namespace
        message['s:Envelope']['s:Header'] = headers
        if body:
            message['s:Envelope']['s:Body'] = body
        else:
            message['s:Envelope']['s:Body'] = {}

        return xmltodict.unparse(message, encoding=self.encoding, full_document=False)
