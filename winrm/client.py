import uuid
import xmltodict

from winrm.contants import WsmvAction, WsmvResourceURI, WsmvConstant
from winrm.exceptions import WinRMError
from winrm.transport import Transport


class Client(object):
    def __init__(self, transport_opts, operation_timeout_sec, locale, encoding, max_envelope_size, resource_uri):
        read_timeout_sec = transport_opts.get('read_timeout_sec', WsmvConstant.DEFAULT_READ_TIMEOUT_SEC)
        if operation_timeout_sec >= read_timeout_sec or operation_timeout_sec < 1:
            raise WinRMError("read_timeout_sec must exceed operation_timeout_sec, and both must be non-zero")

        self.session_id = str(uuid.uuid4()).upper()
        self.transport = Transport(**transport_opts)
        self.operation_timeout_sec = operation_timeout_sec
        self.locale = locale
        self.encoding = encoding
        self.server_config = self.get_server_config(max_envelope_size)
        self.shell_id = str(uuid.uuid4()).upper()
        self.resource_uri = resource_uri


    def get_server_config(self, default_max_envelope_size):
        """
        [MS-WSMV] v30 2016-07-14
        2.2.4.10 ConfigType

        ConfigType is the container for WSMV service configuration data.
        If not running under an admin we cannot retrieve these values and will
        revert to the default value

        :param default_max_envelope_size: The default max envelope size to use if we cannot retrieve the config
        :return: dict:
            max_batch_items: Maximum number of elements in a Pull response, min 1, max 4294967295, default 20
            max_envelope_size_kb: Maximum SOAP data in kilobytes, min 32, max 4294967295, default 150
            max_provider_requests: Maximum number of concurrent requests to WSMV, min 1, max 4294967295, default 25
            max_timeout_ms: Maximum timeout in milliseconds for any requests except Pull, min 500, max 4294967295, default 60000
        """
        try:
            res = self.send(WsmvAction.GET, WsmvResourceURI.CONFIG)
            config = {
                'max_batch_items': int(res['s:Envelope']['s:Body']['cfg:Config']['cfg:MaxBatchItems']),
                'max_envelope_size': int(res['s:Envelope']['s:Body']['cfg:Config']['cfg:MaxEnvelopeSizekb']) * 1024,
                'max_provider_requests': int(res['s:Envelope']['s:Body']['cfg:Config']['cfg:MaxProviderRequests']),
                'max_timeout_ms': int(res['s:Envelope']['s:Body']['cfg:Config']['cfg:MaxTimeoutms'])
            }
        except Exception:
            # Not running as admin, reverting to defaults
            config = {
                'max_batch_items': 20,
                'max_envelope_size': default_max_envelope_size,
                'max_provider_requests': 25,
                'max_timeout_ms': 60000
            }

        return config

    def create_message(self, body, action, selector_set=None, option_set=None):
        headers = self._create_headers(action, selector_set, option_set)
        message = {
            's:Envelope': {
                's:Header': headers,
                's:Body': {}
            }
        }
        for alias, namespace in WsmvConstant.NAMESPACES.items():
            message['s:Envelope']["@xmlns:%s" % alias] = namespace

        if body:
            message['s:Envelope']['s:Body'] = body

        return message

    def send(self, action, body=None, selector_set=None, option_set=None):
        """
        Will send the obj to the server valid the response relates to the request

        :param action: The WSMV action to send through
        :param resource_uri: The WSMV resource_uri
        :param body: The WSMV body which is created by winrm.wsmv.complex_types
        :param selector_set: To add optional selector sets header values to the headers
        :param option_set: To add optional option sets header values to the headers
        :return: A dict which is the xml conversion from the server
        """
        message = self.create_message(body, action, selector_set, option_set)
        message_id = message['s:Envelope']['s:Header']['a:MessageID']
        message = xmltodict.unparse(message, full_document=False, encoding=self.encoding)

        response_xml = self.transport.send_message(message)
        response = xmltodict.parse(response_xml, encoding=self.encoding)
        response_relates_id = response['s:Envelope']['s:Header']['a:RelatesTo']

        if message_id != response_relates_id:
            raise WinRMError("Response related to Message ID: '%s' does not match request Message ID: '%s'" % (
            response_relates_id, message_id))

        return response

    def _create_headers(self, action, selector_set, option_set):
        headers = {
            'a:Action': {
                '@s:mustUnderstand': 'true',
                '#text': action
            },
            'p:DataLocale': {
                '@s:mustUnderstand': 'false',
                '@xml:lang': self.locale
            },
            'w:Locale': {
                '@s:mustUnderstand': 'false',
                '@xml:lang': self.locale
            },
            'a:To': self.transport.endpoint,
            'w:ResourceURI': {
                '@s:mustUnderstand': 'true',
                '#text': self.resource_uri
            },
            'w:OperationTimeout': 'PT%sS' % str(self.operation_timeout_sec),
            'a:ReplyTo': {
                "a:Address": {
                    "@s:mustUnderstand": 'true',
                    '#text': 'http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous'
                }
            },
            'w:MaxEnvelopeSize': '%s' % str(self.server_config['max_envelope_size']),
            'a:MessageID': 'uuid:%s' % str(uuid.uuid4()).upper(),
            'p:SessionId': {
                '@s:mustUnderstand': 'false',
                '#text': 'uuid:%s' % self.session_id
            }
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
