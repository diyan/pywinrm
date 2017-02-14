import base64
import pytest
import struct

from winrm.encryption import Encryption
from winrm.exceptions import WinRMError


def test_init_with_invalid_protocol():
    with pytest.raises(WinRMError) as excinfo:
        Encryption(None, 'invalid_protocol')

    assert "Encryption for protocol 'invalid_protocol' not yet supported in pywinrm" in str(excinfo.value)


def test_encrypt_message():
    test_session = TestSession()
    test_message = b"unencrypted message"
    test_endpoint = b"endpoint"

    encryption = Encryption(test_session, 'ntlm')

    actual = encryption.prepare_encrypted_request(test_session, test_endpoint, test_message)
    expected_encrypted_message = b"dW5lbmNyeXB0ZWQgbWVzc2FnZQ=="
    expected_signature = b"1234"
    signature_length = struct.pack("<i", len(expected_signature))

    assert actual.headers == {
        "Content-Length": "270",
        "Content-Type": 'multipart/encrypted;protocol="application/HTTP-SPNEGO-session-encrypted";boundary="Encrypted Boundary"'
    }
    assert actual.body == b"--Encrypted Boundary\r\n" \
                          b"\tContent-Type: application/HTTP-SPNEGO-session-encrypted\r\n" \
                          b"\tOriginalContent: type=application/soap+xml;charset=UTF-8;Length=19\r\n" \
                          b"--Encrypted Boundary\r\n" \
                          b"\tContent-Type: application/octet-stream\r\n" + \
                          signature_length + expected_signature + expected_encrypted_message + \
                          b"--Encrypted Boundary\r\n"


def test_decrypt_message():
    test_session = TestSession()
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
    test_response = TestResponse('protocol="application/HTTP-SPNEGO-session-encrypted"', test_message)

    encryption = Encryption(test_session, 'ntlm')

    actual = encryption.parse_encrypted_response(test_response)

    assert actual == b'unencrypted message'


def test_decrypt_message_boundary_with_end_hyphens():
    test_session = TestSession()
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
    test_response = TestResponse('protocol="application/HTTP-SPNEGO-session-encrypted"', test_message)

    encryption = Encryption(test_session, 'ntlm')

    actual = encryption.parse_encrypted_response(test_response)

    assert actual == b'unencrypted message'


def test_decrypt_message_length_mismatch():
    test_session = TestSession()
    test_encrypted_message = b"dW5lbmNyeXB0ZWQgbWVzc2FnZQ=="
    test_signature = b"1234"
    test_signature_length = struct.pack("<i", len(test_signature))
    test_message = b"--Encrypted Boundary\r\n" \
                   b"\tContent-Type: application/HTTP-SPNEGO-session-encrypted\r\n" \
                   b"\tOriginalContent: type=application/soap+xml;charset=UTF-8;Length=20\r\n" \
                   b"--Encrypted Boundary\r\n" \
                   b"\tContent-Type: application/octet-stream\r\n" + \
                   test_signature_length + test_signature + test_encrypted_message + \
                   b"--Encrypted Boundary\r\n"
    test_response = TestResponse('protocol="application/HTTP-SPNEGO-session-encrypted"', test_message)

    encryption = Encryption(test_session, 'ntlm')

    with pytest.raises(WinRMError) as excinfo:
        encryption.parse_encrypted_response(test_response)

    assert "Encrypted length from server does not match the expected size, message has been tampered with" in str(excinfo.value)


def test_decrypt_message_decryption_not_needed():
    test_session = TestSession()
    test_response = TestResponse('application/soap+xml', 'unencrypted message')

    encryption = Encryption(test_session, 'ntlm')

    actual = encryption.parse_encrypted_response(test_response)

    assert actual == 'unencrypted message'


class TestSession(object):
    def __init__(self):
        self.auth = TestAuth()

    def prepare_request(self, request):
        request.body = request.data
        return request


class TestAuth(object):
    def __init__(self):
        self.session_security = TestSessionSecurity()


class TestSessionSecurity(object):
    def wrap(self, message):
        encoded_message = base64.b64encode(message)
        signature = b"1234"
        return encoded_message, signature

    def unwrap(self, message, signature):
        assert signature == b"1234"
        decoded_message = base64.b64decode(message)
        return decoded_message


class TestResponse(object):
    def __init__(self, content_type, content):
        self.headers = {
            'Content-Type': content_type
        }
        self.content = content
        self.text = content
