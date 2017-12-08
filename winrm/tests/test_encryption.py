import base64
import pytest
import struct

from winrm.encryption import Encryption
from winrm.exceptions import WinRMError


def test_init_with_invalid_protocol():
    with pytest.raises(WinRMError) as excinfo:
        Encryption(None, 'invalid_protocol')

    assert "Encryption for protocol 'invalid_protocol' not supported in pywinrm" in str(excinfo.value)


def test_encrypt_message():
    test_session = SessionTest()
    test_message = b"unencrypted message"
    test_endpoint = b"endpoint"

    encryption = Encryption(test_session, 'ntlm')

    actual = encryption.prepare_encrypted_request(test_session, test_endpoint, test_message)
    expected_encrypted_message = b"dW5lbmNyeXB0ZWQgbWVzc2FnZQ=="
    expected_signature = b"1234"
    signature_length = struct.pack("<i", len(expected_signature))

    assert actual.headers == {
        "Content-Length": "272",
        "Content-Type": 'multipart/encrypted;protocol="application/HTTP-SPNEGO-session-encrypted";boundary="Encrypted Boundary"'
    }
    assert actual.body == b"--Encrypted Boundary\r\n" \
                          b"\tContent-Type: application/HTTP-SPNEGO-session-encrypted\r\n" \
                          b"\tOriginalContent: type=application/soap+xml;charset=UTF-8;Length=19\r\n" \
                          b"--Encrypted Boundary\r\n" \
                          b"\tContent-Type: application/octet-stream\r\n" + \
                          signature_length + expected_signature + expected_encrypted_message + \
                          b"--Encrypted Boundary--\r\n"


def test_encrypt_large_credssp_message():
    test_session = SessionTest()
    test_message = b"unencrypted message " * 2048
    test_endpoint = b"endpoint"
    message_chunks = [test_message[i:i + 16384] for i in range(0, len(test_message), 16384)]

    encryption = Encryption(test_session, 'credssp')

    actual = encryption.prepare_encrypted_request(test_session, test_endpoint, test_message)
    expected_encrypted_message1 = base64.b64encode(message_chunks[0])
    expected_encrypted_message2 = base64.b64encode(message_chunks[1])
    expected_encrypted_message3 = base64.b64encode(message_chunks[2])

    assert actual.headers == {
        "Content-Length": "55303",
        "Content-Type": 'multipart/x-multi-encrypted;protocol="application/HTTP-CredSSP-session-encrypted";boundary="Encrypted Boundary"'
    }

    assert actual.body == b"--Encrypted Boundary\r\n" \
                          b"\tContent-Type: application/HTTP-CredSSP-session-encrypted\r\n" \
                          b"\tOriginalContent: type=application/soap+xml;charset=UTF-8;Length=16384\r\n" \
                          b"--Encrypted Boundary\r\n" \
                          b"\tContent-Type: application/octet-stream\r\n" + \
                          struct.pack("<i", 32) + expected_encrypted_message1 + \
                          b"--Encrypted Boundary\r\n" \
                          b"\tContent-Type: application/HTTP-CredSSP-session-encrypted\r\n" \
                          b"\tOriginalContent: type=application/soap+xml;charset=UTF-8;Length=16384\r\n" \
                          b"--Encrypted Boundary\r\n" \
                          b"\tContent-Type: application/octet-stream\r\n" + \
                          struct.pack("<i", 32) + expected_encrypted_message2 + \
                          b"--Encrypted Boundary\r\n" \
                          b"\tContent-Type: application/HTTP-CredSSP-session-encrypted\r\n" \
                          b"\tOriginalContent: type=application/soap+xml;charset=UTF-8;Length=8192\r\n" \
                          b"--Encrypted Boundary\r\n" \
                          b"\tContent-Type: application/octet-stream\r\n" + \
                          struct.pack("<i", 32) + expected_encrypted_message3 + \
                          b"--Encrypted Boundary--\r\n"


def test_decrypt_message():
    test_session = SessionTest()
    test_encrypted_message = b"dW5lbmNyeXB0ZWQgbWVzc2FnZQ=="
    test_signature = b"1234"
    test_signature_length = struct.pack("<i", len(test_signature))
    test_message = b"--Encrypted Boundary\r\n" \
                   b"\tContent-Type: application/HTTP-SPNEGO-session-encrypted\r\n" \
                   b"\tOriginalContent: type=application/soap+xml;charset=UTF-8;Length=19\r\n" \
                   b"--Encrypted Boundary\r\n" \
                   b"\tContent-Type: application/octet-stream\r\n" + \
                   test_signature_length + test_signature + test_encrypted_message + \
                   b"--Encrypted Boundary\r\n"
    test_response = ResponseTest('protocol="application/HTTP-SPNEGO-session-encrypted"', test_message)

    encryption = Encryption(test_session, 'ntlm')

    actual = encryption.parse_encrypted_response(test_response)

    assert actual == b'unencrypted message'


def test_decrypt_message_boundary_with_end_hyphens():
    test_session = SessionTest()
    test_encrypted_message = b"dW5lbmNyeXB0ZWQgbWVzc2FnZQ=="
    test_signature = b"1234"
    test_signature_length = struct.pack("<i", len(test_signature))
    test_message = b"--Encrypted Boundary\r\n" \
                   b"\tContent-Type: application/HTTP-SPNEGO-session-encrypted\r\n" \
                   b"\tOriginalContent: type=application/soap+xml;charset=UTF-8;Length=19\r\n" \
                   b"--Encrypted Boundary\r\n" \
                   b"\tContent-Type: application/octet-stream\r\n" + \
                   test_signature_length + test_signature + test_encrypted_message + \
                   b"--Encrypted Boundary--\r\n"
    test_response = ResponseTest('protocol="application/HTTP-SPNEGO-session-encrypted"', test_message)

    encryption = Encryption(test_session, 'ntlm')

    actual = encryption.parse_encrypted_response(test_response)

    assert actual == b'unencrypted message'


def test_decrypt_message_length_mismatch():
    test_session = SessionTest()
    test_encrypted_message = b"dW5lbmNyeXB0ZWQgbWVzc2FnZQ=="
    test_signature = b"1234"
    test_signature_length = struct.pack("<i", len(test_signature))
    test_message = b"--Encrypted Boundary\r\n" \
                   b"\tContent-Type: application/HTTP-SPNEGO-session-encrypted\r\n" \
                   b"\tOriginalContent: type=application/soap+xml;charset=UTF-8;Length=20\r\n" \
                   b"--Encrypted Boundary\r\n" \
                   b"\tContent-Type: application/octet-stream\r\n" + \
                   test_signature_length + test_signature + test_encrypted_message + \
                   b"--Encrypted Boundary--\r\n"
    test_response = ResponseTest('protocol="application/HTTP-SPNEGO-session-encrypted"', test_message)

    encryption = Encryption(test_session, 'ntlm')

    with pytest.raises(WinRMError) as excinfo:
        encryption.parse_encrypted_response(test_response)

    assert "Encrypted length from server does not match the expected size, message has been tampered with" in str(excinfo.value)


def test_decrypt_large_credssp_message():
    test_session = SessionTest()

    test_unencrypted_message = b"unencrypted message " * 2048
    test_encrypted_message_chunks = [test_unencrypted_message[i:i + 16384] for i in range(0, len(test_unencrypted_message), 16384)]

    test_encrypted_message1 = base64.b64encode(test_encrypted_message_chunks[0])
    test_encrypted_message2 = base64.b64encode(test_encrypted_message_chunks[1])
    test_encrypted_message3 = base64.b64encode(test_encrypted_message_chunks[2])

    test_message = b"--Encrypted Boundary\r\n" \
                   b"\tContent-Type: application/HTTP-CredSSP-session-encrypted\r\n" \
                   b"\tOriginalContent: type=application/soap+xml;charset=UTF-8;Length=16384\r\n" \
                   b"--Encrypted Boundary\r\n" \
                   b"\tContent-Type: application/octet-stream\r\n" + \
                   struct.pack("<i", 5443) + test_encrypted_message1 + \
                   b"--Encrypted Boundary\r\n" \
                   b"\tContent-Type: application/HTTP-CredSSP-session-encrypted\r\n" \
                   b"\tOriginalContent: type=application/soap+xml;charset=UTF-8;Length=16384\r\n" \
                   b"--Encrypted Boundary\r\n" \
                   b"\tContent-Type: application/octet-stream\r\n" + \
                   struct.pack("<i", 5443) + test_encrypted_message2 + \
                   b"--Encrypted Boundary\r\n" \
                   b"\tContent-Type: application/HTTP-CredSSP-session-encrypted\r\n" \
                   b"\tOriginalContent: type=application/soap+xml;charset=UTF-8;Length=8192\r\n" \
                   b"--Encrypted Boundary\r\n" \
                   b"\tContent-Type: application/octet-stream\r\n" + \
                   struct.pack("<i", 2711) + test_encrypted_message3 + \
                   b"--Encrypted Boundary--\r\n"

    test_response = ResponseTest('protocol="application/HTTP-CredSSP-session-encrypted"', test_message)

    encryption = Encryption(test_session, 'credssp')

    actual = encryption.parse_encrypted_response(test_response)

    assert actual == test_unencrypted_message


def test_decrypt_message_decryption_not_needed():
    test_session = SessionTest()
    test_response = ResponseTest('application/soap+xml', 'unencrypted message')

    encryption = Encryption(test_session, 'ntlm')

    actual = encryption.parse_encrypted_response(test_response)

    assert actual == 'unencrypted message'


def test_get_credssp_trailer_length_gcm():
    test_session = SessionTest()
    encryption = Encryption(test_session, 'credssp')
    expected = 16
    actual = encryption._get_credssp_trailer_length(30, 'ECDHE-RSA-AES128-GCM-SHA256')

    assert actual == expected


def test_get_credssp_trailer_length_md5_rc4():
    test_session = SessionTest()
    encryption = Encryption(test_session, 'credssp')
    expected = 16
    actual = encryption._get_credssp_trailer_length(30, 'RC4-MD5')

    assert actual == expected


def test_get_credssp_trailer_length_sha256_3des():
    test_session = SessionTest()
    encryption = Encryption(test_session, 'credssp')
    expected = 34
    actual = encryption._get_credssp_trailer_length(30, 'ECDH-ECDSA-3DES-SHA256')

    assert actual == expected


def test_get_credssp_trailer_length_sha384_aes():
    test_session = SessionTest()
    encryption = Encryption(test_session, 'credssp')
    expected = 50
    actual = encryption._get_credssp_trailer_length(30, 'ECDH-RSA-AES-SHA384')

    assert actual == expected


def test_get_credssp_trailer_length_no_hash():
    test_session = SessionTest()
    encryption = Encryption(test_session, 'credssp')
    expected = 2
    actual = encryption._get_credssp_trailer_length(30, 'ECDH-RSA-AES')

    assert actual == expected


class SessionTest(object):
    def __init__(self):
        self.auth = AuthTest()

    def prepare_request(self, request):
        request.body = request.data
        return request


class AuthTest(object):
    def __init__(self):
        # used with NTLM
        self.session_security = SessionSecurityTest()
        # used with CredSSP
        self.cipher_negotiated = 'ECDH-RSA-AES256-SHA'

    # used with CredSSP
    def wrap(self, message):
        encoded_message, signature = self.session_security.wrap(message)
        return encoded_message

    # used with CredSSP
    def unwrap(self, message):
        decoded_mesage = self.session_security.unwrap(message, b"1234")
        return decoded_mesage


class SessionSecurityTest(object):
    def wrap(self, message):
        encoded_message = base64.b64encode(message)
        signature = b"1234"
        return encoded_message, signature

    def unwrap(self, message, signature):
        assert signature == b"1234"
        decoded_message = base64.b64decode(message)
        return decoded_message


class RequestTest(object):
    def __init__(self):
        self.url = 'http://testhost.com/path'


class ResponseTest(object):
    def __init__(self, content_type, content):
        self.headers = {
            'Content-Type': content_type
        }
        self.content = content
        self.text = content
        self.request = RequestTest()
