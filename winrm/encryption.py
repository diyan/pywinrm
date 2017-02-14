import requests
import struct

from winrm.exceptions import WinRMError

class Encryption(object):
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
                         the protocol string to use. Currently only NTLM is supported
        """
        if protocol == 'ntlm': # Details under Negotiate [2.2.9.1.1] in MS-WSMV
            self.wrap = session.auth.session_security.wrap
            self.unwrap = session.auth.session_security.unwrap
            self.protocol_string = b"application/HTTP-SPNEGO-session-encrypted"
        # TODO: Add support for Kerberos and CredSSP encryption
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
        encrypted_message = self._encrypt_message(message)
        request = requests.Request('POST', endpoint, data=encrypted_message)
        prepared_request = session.prepare_request(request)
        prepared_request.headers['Content-Length'] = str(len(prepared_request.body))
        prepared_request.headers['Content-Type'] = 'multipart/encrypted;protocol="{0}";boundary="Encrypted Boundary"'\
            .format(self.protocol_string.decode())

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
        sealed_message, signature = self.wrap(message)
        message_length = str(len(message)).encode()
        signature_length = struct.pack("<i", len(signature))

        message_payload = b"--Encrypted Boundary\r\n" \
                          b"\tContent-Type: " + self.protocol_string + b"\r\n" \
                          b"\tOriginalContent: type=application/soap+xml;charset=UTF-8;Length=" + message_length + b"\r\n" \
                          b"--Encrypted Boundary\r\n" \
                          b"\tContent-Type: application/octet-stream\r\n" + \
                          signature_length + signature + sealed_message + \
                          b"--Encrypted Boundary\r\n"

        return message_payload

    def _decrypt_response(self, response):
        encrypted_boundary = response.content.split(b'--Encrypted Boundary\r\n')
        metadata_section = encrypted_boundary[1]
        payload_section = encrypted_boundary[2]

        # I can't find any documentation explaining this but sometimes the last
        # Encrypted Boundary has -- before the newline. Handling this here
        if payload_section.endswith(b'--Encrypted Boundary--\r\n'):
            payload_section = payload_section[:len(payload_section) - 24]

        expected_length = int(metadata_section.split(b';Length=')[1].strip())
        encrypted_data = payload_section.replace(b'\tContent-Type: application/octet-stream\r\n', b'')
        signature_length = struct.unpack("<i", encrypted_data[:4])[0]
        signature = encrypted_data[4:signature_length + 4]
        encrypted_message = encrypted_data[signature_length + 4:]

        message = self.unwrap(encrypted_message, signature)
        actual_length = len(message)
        if actual_length != expected_length:
            raise WinRMError('Encrypted length from server does not match the expected size, message has been tampered with')

        return message
