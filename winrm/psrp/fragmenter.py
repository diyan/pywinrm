import base64
import struct
import xmltodict


from winrm.contants import WsmvAction, WsmvConstant, WsmvResourceURI
from winrm.wsmv.objects import WsmvObject

class Fragmenter(object):
    IS_START_FRAGMENT = 0x00000001
    IS_MIDDLE_FRAGMENT = 0x00000000
    IS_END_FRAGMENT = 0x00000010


    def __init__(self, wsmv_protocol):
        self.wsmv_protocol = wsmv_protocol
        self.object_id = 0

    def fragment_messages(self, blobs):
        max_blob_size = self._calculate_max_blob_size()
        fragments = []

        raw_fragment = b''
        current_fragment_size = 0
        for blob in blobs:
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

                current_fragment = self._create_fragment(self.object_id, 0, self.IS_START_FRAGMENT,
                                                       self.IS_END_FRAGMENT, blob)
                fragments.append(base64.b64encode(current_fragment))

                raw_fragment = ''
                current_fragment_size = 0
            else:
                # The current blob plus the previous blob can fit into 1 envelope
                fragment = self._create_fragment(self.object_id, 0, self.IS_START_FRAGMENT, self.IS_END_FRAGMENT, blob)
                raw_fragment += fragment
                current_fragment_size += blob_size

            self.object_id += 1

        # Make sure the raw fragment has been added at the end
        if len(raw_fragment) > 0:
            fragments.append(base64.b64encode(raw_fragment))

        return fragments

    def _fragment_blob(self, blob, max_blob_size):
        fragments = []
        fragment_id = 0
        blob_size = len(blob)
        bytes_fragmented = 0
        start_bit = self.IS_START_FRAGMENT

        while bytes_fragmented < len(blob):
            end_bit = self.IS_MIDDLE_FRAGMENT
            last_byte = bytes_fragmented + max_blob_size
            if last_byte > fragment_id:
                last_byte = blob_size
                end_bit = self.IS_END_FRAGMENT

            blob_fragment = blob[bytes_fragmented:last_byte]
            fragment = self._create_fragment(self.object_id, fragment_id, end_bit, start_bit, blob_fragment)
            fragments.append(fragment)

            start_bit = self.IS_MIDDLE_FRAGMENT
            fragment_id += 1
            bytes_fragmented = last_byte

        return fragments

    def _create_fragment(self, object_id, fragment_id, e, s, blob):
        start_end_byte = e | s

        fragment = struct.pack("<Q", object_id)
        fragment += struct.pack("<Q", fragment_id)
        fragment += struct.pack("<Q", start_end_byte)
        fragment += struct.pack("<I", len(blob))
        fragment += blob

        return fragment

    def _calculate_max_blob_size(self):
        """
        Calculates the max size the blob inside a fragment can be to fit within
        the MaxEnvelopeSizeKb of the server

        :return: the max length of a fragment blob as an int
        """
        # MaxEvelopeSize in KB * 1024 to convert to bytes
        max_envelope_bytes = self.wsmv_protocol.max_envelope_size * 1024

        # Number of bytes in fragment header
        fragment_header_bytes = 21

        # Number of bytes of the wsmv message to encapsulate the PSRP data in
        wsmv_message_bytes = self._get_empty_wsmv_command_size()

        # Determine how many base64 characters are allowed, convert to base64 decoded bytes available
        base64_bytes_allowed = max_envelope_bytes - wsmv_message_bytes
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
        body = WsmvObject.command_line('Invoke-Expression', ())
        selector_set = {
            'ShellId': WsmvConstant.EMPTY_UUID
        }
        message = self.wsmv_protocol.create_message(body, WsmvAction.COMMAND, WsmvResourceURI.SHELL_POWERSHELL,
                                                    selector_set=selector_set)
        return len(xmltodict.unparse(message))
