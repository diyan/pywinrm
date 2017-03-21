import logging
import uuid
import xmltodict

from winrm.contants import WsmvAction, WsmvResourceURI, WsmvConstant
from winrm.exceptions import WinRMError
from winrm.transport import Transport

log = logging.getLogger(__name__)

class Client(object):
    def __init__(self, transport_opts, operation_timeout_sec, locale, encoding, max_envelope_size, resource_uri):
        """
        A base class for shell operations over WSMan, contains common code in both WSMV and PSRP

        :param transport_opts: A dict of options to pass through to the Transport class. See winrm.transport for more details
        :param int operation_timeout_sec: The maximum allowed time in seconds for any single WSMan HTTP operations (default 2)
        :param string locale: The locale and data_locale to set in the messages (default en-US)
        :param string encoding: The string encoding format to encode messages in (default utf-8)
        :param int max_envelope_size: The maximum envelope size in bytes, will be overwritten is Pywinrm can get the config from the server (default 153600)
        :param resource_uri: The WSMV Shell Resource URI to use
        """
        read_timeout_sec = transport_opts.get('read_timeout_sec', WsmvConstant.DEFAULT_READ_TIMEOUT_SEC)
        if operation_timeout_sec >= read_timeout_sec or operation_timeout_sec < 1:
            raise WinRMError("read_timeout_sec must exceed operation_timeout_sec, and both must be non-zero")

        self.session_id = str(uuid.uuid4()).upper()
        self.transport = Transport(**transport_opts)
        self.operation_timeout_sec = operation_timeout_sec
        self.locale = locale
        self.encoding = encoding
        self.shell_id = str(uuid.uuid4()).upper()
        self.resource_uri = resource_uri
        self.set_server_config(max_envelope_size)
        log.debug("Creating new Shell class: Shell ID: %s, Resource URI: %s" % (self.shell_id, self.resource_uri))


    def set_server_config(self, default_max_envelope_size):
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
        self.server_config = {
            'max_batch_items': 20,
            'max_envelope_size': default_max_envelope_size,
            'max_provider_requests': 25,
            'max_timeout_ms': 60000
        }

        try:
            log.debug("Trying to get Server WinRM config")
            res = self.send(WsmvAction.GET, resource_uri=WsmvResourceURI.CONFIG)
            self.server_config = {
                'max_batch_items': int(res['s:Envelope']['s:Body']['cfg:Config']['cfg:MaxBatchItems']),
                'max_envelope_size': int(res['s:Envelope']['s:Body']['cfg:Config']['cfg:MaxEnvelopeSizekb']) * 1024,
                'max_provider_requests': int(res['s:Envelope']['s:Body']['cfg:Config']['cfg:MaxProviderRequests']),
                'max_timeout_ms': int(res['s:Envelope']['s:Body']['cfg:Config']['cfg:MaxTimeoutms'])
            }
        except Exception:
            log.warning("Failed to retrieve Server WinRM config, using defaults instead")
            pass

    def send(self, action, resource_uri=None, body=None, selector_set=None, option_set=None):
        """
        Will send the obj to the server valid the response relates to the request

        :param action: The WSMV action to send through
        :param resource_uri: The WSMV resource_uri
        :param body: The WSMV body which is created by winrm.wsmv.complex_types
        :param selector_set: To add optional selector sets header values to the headers
        :param option_set: To add optional option sets header values to the headers
        :return: A dict which is the xml conversion from the server
        """
        if resource_uri is None:
            resource_uri = self.resource_uri
        message = self.create_message(body, action, resource_uri, selector_set, option_set)
        message_id = message['s:Envelope']['s:Header']['a:MessageID']
        message = xmltodict.unparse(message, full_document=False, encoding=self.encoding)
        log.debug("Sending message to server: %s" % message)

        response_xml = self.transport.send_message(message)
        log.debug("Received message from server: %s" % response_xml)
        response = xmltodict.parse(response_xml, encoding=self.encoding)
        response_relates_id = response['s:Envelope']['s:Header']['a:RelatesTo']

        log.debug("Request ID: %s, Response relates to ID: %s" % (message_id, response_relates_id))
        if message_id != response_relates_id:
            raise WinRMError("Response related to Message ID: '%s' does not match request Message ID: '%s'" % (
            response_relates_id, message_id))

        return response

    def create_message(self, body, action, resource_uri, selector_set=None, option_set=None):
        headers = self._create_headers(action, resource_uri, selector_set, option_set)
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

    def _create_headers(self, action, resource_uri, selector_set, option_set):
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
                '#text': resource_uri
            },
            'w:OperationTimeout': convert_seconds_to_iso8601_duration(self.operation_timeout_sec),
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


def get_value_of_attribute(root, attribute_key, attribute_value, element_value=None):
    """
    Helper method to search through a list of elements in an xml node and
    retrieve the element with the attribute specified. If no values are
    found None is returned instead

    :param root: The xml root to search in
    :param attribute_key: The attribute key to search for the value
    :param attribute_value: The value of the attribute based on the attribute_key
    :param element_value: If set will return the value of the element found
    :return:
    """
    value = None
    if isinstance(root, dict):
        root = [root]
    for node in root:
        if isinstance(node, dict):
            try:
                key = node['@%s' % attribute_key]
                if key == attribute_value:
                    if element_value:
                        value = node.get(element_value, None)
                    else:
                        value = node
                    break
            except KeyError:
                pass
    return value


def convert_seconds_to_iso8601_duration(seconds):
    # Details can be found here https://tools.ietf.org/html/rfc2445#section-4.3.6
    if isinstance(seconds, str):
        if seconds.startswith('P'):
            return seconds
        seconds = int(seconds)

    duration = "P"
    if seconds > 604800:
        weeks = int(seconds / 604800)
        seconds -= 604800 * weeks
        duration += "%dW" % weeks
    if seconds > 86400:
        days = int(seconds / 86400)
        seconds -= 86400 * days
        duration += "%dD" % days
    if seconds > 0:
        duration += "T"
        if seconds > 3600:
            hours = int(seconds / 3600)
            seconds -= 3600 * hours
            duration += "%dH" % hours
        if seconds > 60:
            minutes = int(seconds / 60)
            seconds -= 60 * minutes
            duration += "%dM" % minutes
        if seconds > 0:
            duration += "%dS" % seconds

    return duration
