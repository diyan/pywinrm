import xmltodict


from winrm.contants import Actions, Constants
from winrm.wsmv.objects import WsmvObject


class Fragmenter(object):
    def __init__(self, max_envelope_size):
        self.max_envelope_size = max_envelope_size
        self.object_id = 0
        self.counter = 0

    def fragment_message(self, psrp_data):
        fragments = []

        return fragments

    def assemble_message(self, fragments):
        message = ''

        return message


    def _calculate_fragment_size(self):
        # MaxEvelopeSize in KB * 1024 to convert to bytes
        max_envelope_bytes = self.max_envelope_size * 1024

        # Number of bytes in fragment header
        fragment_header_bytes = 21

        # Number of bytes of the wsmv message to encapsulate the PSRP data in
        wsmv_message_bytes = self._get_empty_wsmv_command_size()

        # Determine how many base64 characters are allowed, convert to base64 decoded bytes available
        base64_bytes_allowed = max_envelope_bytes - wsmv_message_bytes
        raw_base64_size = base64_bytes_allowed / 4 * 3

        # Subtract remaining amount with the header bytes length
        allowed_fragment_size = raw_base64_size - fragment_header_bytes

        return allowed_fragment_size


    def _get_empty_wsmv_command_size(self):
        resource_uri = 'http://schemas.microsoft.com/powershell/Microsoft.PowerShell'
        command_line = WsmvObject.command_line('Invoke-Expression', [])
        selector_set = {
            'ShellId': '00000000-0000-0000-0000-000000000000'
        }
        headers = self._create_headers(Actions.COMMAND, resource_uri, selector_set)
        message = self._create_message(headers, command_line)
        return len(message)

    def _create_headers(self, action, resource_uri, selector_set):
        headers = {
            'a:Action': {
                '@mustUnderstand': 'true',
                '#text': action
            },
            'p:DataLocale': {
                '@mustUnderstand': 'false',
                '@xml:lang': 'en-US'
            },
            'w:Locale': {
                '@mustUnderstand': 'false',
                '@xml:lang': 'en-US'
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
            'a:MessageID': 'uuid:00000000-0000-0000-0000-000000000000'
        }

        if selector_set:
            selector_set_list = []
            for key, value in selector_set.items():
                selector_set_list.append({'@Name': key, '#text': value})
            headers['w:SelectorSet'] = {'w:Selector': selector_set_list}

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

        return xmltodict.unparse(message, encoding='utf-8', full_document=False)