import requests
import struct

from winrm.exceptions import WinRMError

class Encryption(object):

    SIXTEN_KB = 16384
    MIME_BOUNDARY = b'--Encrypted Boundary'

    def __init__(self, session, protocol):
        """
        [MS-WSMV] v30.0 2016-07-14

        2.2.9.1 Encrypted Message Types
        When using Encryption, there are three options available
            1. Negotiate/SPNEGO
            2. Kerberos
            3. CredSSP
        Details for each implementation can be found in this document under this section

        This init sets the following values to use to encrypt and decrypt. This is to help generify
        the methods used in the body of the class.
            wrap: A method that will return the encrypted message and a signature
            unwrap: A method that will return an unencrypted message and verify the signature
            protocol_string: The protocol string used for the particular auth protocol

        :param session: The handle of the session to get GSS-API wrap and unwrap methods
        :param protocol: The auth protocol used, will determine the wrapping and unwrapping method plus
                         the protocol string to use. Currently only NTLM and CredSSP is supported
        """
        self.protocol = protocol
        self.session = session

        if protocol == 'ntlm': # Details under Negotiate [2.2.9.1.1] in MS-WSMV
            self.protocol_string = b"application/HTTP-SPNEGO-session-encrypted"
            self._build_message = self._build_ntlm_message
            self._decrypt_message = self._decrypt_ntlm_message
        elif protocol == 'credssp': # Details under CredSSP [2.2.9.1.3] in MS-WSMV
            self.protocol_string = b"application/HTTP-CredSSP-session-encrypted"
            self._build_message = self._build_credssp_message
            self._decrypt_message = self._decrypt_credssp_message
        # TODO: Add support for Kerberos encryption
        else:
            raise WinRMError("Encryption for protocol '%s' not yet supported in pywinrm" % protocol)

    def prepare_encrypted_request(self, session, endpoint, message):
        """
        Creates a prepared request to send to the server with an encrypted message
        and correct headers

        :param session: The handle of the session to prepare requests with
        :param endpoint: The endpoint/server to prepare requests to
        :param message: The unencrypted message to send to the server
        :return: A prepared request that has an encrypted message
        """
        if self.protocol == 'credssp' and len(message) > self.SIXTEN_KB:
            content_type = 'multipart/x-multi-encrypted'
            encrypted_message = b''
            message_chunks = [message[i:i+self.SIXTEN_KB] for i in range(0, len(message), self.SIXTEN_KB)]
            for message_chunk in message_chunks:
                encrypted_chunk = self._encrypt_message(message_chunk)
                encrypted_message += encrypted_chunk
        else:
            content_type = 'multipart/encrypted'
            encrypted_message = self._encrypt_message(message)
        encrypted_message += self.MIME_BOUNDARY + b"--\r\n"

        request = requests.Request('POST', endpoint, data=encrypted_message)
        prepared_request = session.prepare_request(request)
        prepared_request.headers['Content-Length'] = str(len(prepared_request.body))
        prepared_request.headers['Content-Type'] = '{0};protocol="{1}";boundary="Encrypted Boundary"'\
            .format(content_type, self.protocol_string.decode())

        return prepared_request

    def parse_encrypted_response(self, response):
        """
        Takes in the encrypted response from the server and decrypts it

        :param response: The response that needs to be decrytped
        :return: The unencrypted message from the server
        """
        content_type = response.headers['Content-Type']
        if 'protocol="{0}"'.format(self.protocol_string.decode()) in content_type:
            msg = self._decrypt_response(response)
        else:
            msg = response.text

        return msg

    def _encrypt_message(self, message):
        message_length = str(len(message)).encode()
        encrypted_stream = self._build_message(message)

        message_payload = self.MIME_BOUNDARY + b"\r\n" \
                          b"\tContent-Type: " + self.protocol_string + b"\r\n" \
                          b"\tOriginalContent: type=application/soap+xml;charset=UTF-8;Length=" + message_length + b"\r\n" + \
                          self.MIME_BOUNDARY + b"\r\n" \
                          b"\tContent-Type: application/octet-stream\r\n" + \
                          encrypted_stream

        return message_payload

    def _decrypt_response(self, response):
        parts = response.content.split(self.MIME_BOUNDARY + b'\r\n')
        parts = list(filter(None, parts)) # filter out empty parts of the split
        message = b''

        for i in range(0, len(parts)):
            if i % 2 == 1:
                continue

            header = parts[i].strip()
            payload = parts[i + 1]

            expected_length = int(header.split(b'Length=')[1])

            # remove the end MIME block if it exists
            if payload.endswith(self.MIME_BOUNDARY + b'--\r\n'):
                payload = payload[:len(payload) - 24]

            encrypted_data = payload.replace(b'\tContent-Type: application/octet-stream\r\n', b'')
            decrypted_message = self._decrypt_message(encrypted_data)
            actual_length = len(decrypted_message)

            if actual_length != expected_length:
                raise WinRMError('Encrypted length from server does not match the '
                                 'expected size, message has been tampered with')
            message += decrypted_message

        return message

    def _decrypt_ntlm_message(self, encrypted_data):
        signature_length = struct.unpack("<i", encrypted_data[:4])[0]
        signature = encrypted_data[4:signature_length + 4]
        encrypted_message = encrypted_data[signature_length + 4:]

        message = self.session.auth.session_security.unwrap(encrypted_message, signature)

        return message

    def _decrypt_credssp_message(self, encrypted_data):
        # trailer_length = struct.unpack("<i", encrypted_data[:4])[0]
        encrypted_message = encrypted_data[4:]

        message = self.session.auth.unwrap(encrypted_message)

        return message

    def _build_ntlm_message(self, message):
        sealed_message, signature = self.session.auth.session_security.wrap(message)
        signature_length = struct.pack("<i", len(signature))

        return signature_length + signature + sealed_message

    def _build_credssp_message(self, message):
        sealed_message = self.session.auth.wrap(message)

        # not really sure why I need to take a further 21 from the below the
        # length of the --Encrypted Boundary\r\n is 22 but this seems to be
        # the magic number
        message_length_difference = len(sealed_message) - len(message) - 21

        trailer_length = struct.pack("<i", message_length_difference)

        return trailer_length + sealed_message
