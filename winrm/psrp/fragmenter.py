import base64
import struct
import xmltodict

from winrm.contants import WsmvAction, WsmvConstant, WsmvResourceURI
from winrm.wsmv.message_objects import WsmvObject
from winrm.psrp.message_objects import Message


class Fragment(object):
    IS_MIDDLE_FRAGMENT = 0x0
    IS_START_FRAGMENT = 0x1
    IS_END_FRAGMENT = 0x2

    def __init__(self, object_id, fragment_id, start_bit, end_bit, blob):
        self.object_id = object_id
        self.fragment_id = fragment_id
        self.start_bit = start_bit
        self.end_bit = end_bit
        self.blob_length = len(blob)
        self.blob = blob

    def create_fragment(self):
        start_end_byte = self.start_bit | self.end_bit

        fragment = struct.pack(">Q", self.object_id)
        fragment += struct.pack(">Q", self.fragment_id)
        fragment += struct.pack(">B", start_end_byte)
        fragment += struct.pack(">I", self.blob_length)
        fragment += self.blob

        return fragment

    @staticmethod
    def parse_fragment(fragment):
        object_id = struct.unpack('>Q', fragment[0:8])[0]
        fragment_id = struct.unpack('>Q', fragment[8:16])[0]
        start_end_byte = struct.unpack('>B', fragment[16:17])[0]
        blob_length = struct.unpack('>I', fragment[17:21])[0]
        blob = fragment[21:blob_length+21]

        start_bit = Fragment.IS_MIDDLE_FRAGMENT
        end_bit = Fragment.IS_MIDDLE_FRAGMENT
        if start_end_byte == 0x3:
            start_bit = Fragment.IS_START_FRAGMENT
            end_bit = Fragment.IS_END_FRAGMENT
        elif start_end_byte == Fragment.IS_START_FRAGMENT:
            start_bit = Fragment.IS_START_FRAGMENT
        elif  start_end_byte == Fragment.IS_END_FRAGMENT:
            end_bit = Fragment.IS_END_FRAGMENT

        return Fragment(object_id, fragment_id, start_bit, end_bit, blob)


class Fragmenter(object):
    def __init__(self, client):
        self.client = client
        self.object_id = 0

    def fragment_messages(self, messages):
        if not isinstance(messages, list):
            messages = [messages]

        max_blob_size = self._calculate_max_blob_size()
        fragments = []

        raw_fragment = b''
        current_fragment_size = 0
        for message in messages:
            blob = message.create_message()
            self.object_id += 1
            blob_size = len(blob)
            if blob_size > max_blob_size:
                # The individual blob needs to split into multiple fragments
                if len(raw_fragment) > 0:
                    fragments.append(base64.b64encode(raw_fragment))

                for fragment in self._fragment_blob(blob, max_blob_size):
                    fragments.append(base64.b64encode(fragment))

                raw_fragment = ''
                current_fragment_size = 0
            elif current_fragment_size + blob_size > max_blob_size:
                # The current blob plus the previous blob is too large, split into chunks
                if len(raw_fragment) > 0:
                    fragments.append(base64.b64encode(raw_fragment))

                current_fragment = Fragment(self.object_id, 0, Fragment.IS_START_FRAGMENT, Fragment.IS_END_FRAGMENT,
                                                blob)
                fragments.append(base64.b64encode(current_fragment.create_fragment()))

                raw_fragment = ''
                current_fragment_size = 0
            else:
                # The current blob plus the previous blob can fit into 1 envelope
                fragment = Fragment(self.object_id, 0, Fragment.IS_START_FRAGMENT, Fragment.IS_END_FRAGMENT, blob)
                raw_fragment += fragment.create_fragment()
                current_fragment_size += blob_size

        # Make sure the raw fragment has been added at the end
        if len(raw_fragment) > 0:
            fragments.append(base64.b64encode(raw_fragment))

        return fragments

    def _fragment_blob(self, blob, max_blob_size):
        fragments = []
        fragment_id = 0
        blob_size = len(blob)
        bytes_fragmented = 0
        start_bit = Fragment.IS_START_FRAGMENT

        while bytes_fragmented < len(blob):
            end_bit = Fragment.IS_MIDDLE_FRAGMENT
            last_byte = bytes_fragmented + max_blob_size
            if last_byte > fragment_id:
                last_byte = blob_size
                end_bit = Fragment.IS_END_FRAGMENT

            blob_fragment = blob[bytes_fragmented:last_byte]
            fragment = Fragment(self.object_id, fragment_id, end_bit, start_bit, blob_fragment)
            fragments.append(fragment.create_fragment())

            start_bit = Fragment.IS_MIDDLE_FRAGMENT
            fragment_id += 1
            bytes_fragmented = last_byte

        return fragments

    def _calculate_max_blob_size(self):
        """
        Calculates the max size the blob inside a fragment can be to fit within
        the MaxEnvelopeSizeKb of the server

        :return: the max length of a fragment blob as an int
        """
        # Number of bytes in fragment header
        fragment_header_bytes = 21

        # Number of bytes of the wsmv message to encapsulate the PSRP data in
        wsmv_message_bytes = self._get_empty_wsmv_command_size()

        # Determine how many base64 characters are allowed, convert to base64 decoded bytes available
        base64_bytes_allowed = self.client.server_config['max_envelope_size'] - wsmv_message_bytes
        raw_base64_size = base64_bytes_allowed / 4 * 3

        # Subtract remaining amount with the header bytes length
        allowed_fragment_size = raw_base64_size - fragment_header_bytes

        return int(allowed_fragment_size)


    def _get_empty_wsmv_command_size(self):
        """
        Creates an empty WSMV CommandLine message to use when calculating how
        large the PSRP fragment can be
        :return: The length of the WSMV CommandLine xml string
        """
        body = WsmvObject.command_line('', '', WsmvConstant.EMPTY_UUID)
        selector_set = {
            'ShellId': WsmvConstant.EMPTY_UUID
        }
        message = self.client.create_message(body, WsmvAction.COMMAND, resource_uri=self.client.resource_uri,
                                             selector_set=selector_set)
        return len(xmltodict.unparse(message))

class Defragmenter(object):
    def __init__(self):
        self.fragments = b''

    def defragment_message(self, message):
        fragment = base64.b64decode(message)

        fragment = Fragment.parse_fragment(fragment)
        self.fragments += fragment.blob

        if fragment.end_bit == Fragment.IS_END_FRAGMENT:
            defragmented_message = Message.parse_message(self.fragments)
            self.fragments = b''
            return defragmented_message
        else:
            return None
