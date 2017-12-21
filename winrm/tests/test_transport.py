# coding=utf-8
import os
import pytest
from winrm.transport import Transport
from winrm.exceptions import WinRMError, InvalidCredentialsError


def test_ca_build_session():
    transport = Transport(endpoint="Endpoint",
                          server_cert_validation='validate',
                          username='test',
                          password='test',
                          auth_method='basic',
                          )
    os.environ['REQUESTS_CA_BUNDLE'] = 'path_to_REQUESTS_CA_CERT'
    transport.build_session()
    assert(transport.session.verify == 'path_to_REQUESTS_CA_CERT')
    del os.environ['REQUESTS_CA_BUNDLE']

    os.environ['CURL_CA_BUNDLE'] = 'path_to_CURL_CA_CERT'
    transport.build_session()
    assert(transport.session.verify == 'path_to_CURL_CA_CERT')
    del os.environ['CURL_CA_BUNDLE']


def test_build_session_ca_trust_path():
    transport = Transport(endpoint="Endpoint",
                          server_cert_validation='validate',
                          username='test',
                          password='test',
                          auth_method='basic',
                          ca_trust_path=True
                          )
    transport.build_session()
    assert(transport.ca_trust_path is True)
    assert(transport.session.verify is True)

    transport = Transport(endpoint="Endpoint",
                          server_cert_validation='ignore',
                          username='test',
                          password='test',
                          auth_method='basic',
                          ca_trust_path=True
                          )
    transport.build_session()
    assert(transport.ca_trust_path is True)
    assert(transport.session.verify is True)


def test_build_session_server_cert_validation_ignore():
    transport = Transport(endpoint="Endpoint",
                          server_cert_validation='ignore',
                          username='test',
                          password='test',
                          auth_method='basic',
                          )
    transport.build_session()
    assert(transport.session.verify is False)


def test_build_session_server_cert_validation_invalid():
    with pytest.raises(WinRMError) as exc:
        transport = Transport(endpoint="Endpoint",
                              server_cert_validation='invalid_value',
                              username='test',
                              password='test',
                              auth_method='basic',
                              )
    assert str(exc.value) == 'invalid server_cert_validation mode: invalid_value'


def test_build_session_krb_delegation_as_str():
    transport = Transport(endpoint="Endpoint",
                          server_cert_validation='validate',
                          username='test',
                          password='test',
                          auth_method='kerberos',
                          kerberos_delegation='True'
                          )
    assert(transport.kerberos_delegation is True)


def test_build_session_krb_delegation_as_invalid_str():
    with pytest.raises(ValueError) as exc:
        transport = Transport(endpoint="Endpoint",
                              server_cert_validation='validate',
                              username='test',
                              password='test',
                              auth_method='kerberos',
                              kerberos_delegation='invalid_value'
                              )
    assert str(exc.value) == "invalid truth value 'invalid_value'"


def test_build_session_no_username():
    with pytest.raises(InvalidCredentialsError) as exc:
        transport = Transport(endpoint="Endpoint",
                              server_cert_validation='validate',
                              password='test',
                              auth_method='basic',
                              )
        transport.build_session()

    assert str(exc.value) == "auth method basic requires a username"


def test_build_session_no_password():
    with pytest.raises(InvalidCredentialsError) as exc:
        transport = Transport(endpoint="Endpoint",
                              server_cert_validation='validate',
                              username='test',
                              auth_method='basic',
                              )
        transport.build_session()

    assert str(exc.value) == "auth method basic requires a password"


def test_build_session_invalid_auth():
    with pytest.raises(WinRMError) as exc:
        transport = Transport(endpoint="Endpoint",
                              server_cert_validation='validate',
                              username='test',
                              password='test',
                              auth_method='invalid_value',
                              )
        transport.build_session()

    assert str(exc.value) == "unsupported auth method: invalid_value"


def test_build_session_invalid_encryption():
    with pytest.raises(WinRMError) as exc:
        transport = Transport(endpoint="Endpoint",
                              server_cert_validation='validate',
                              username='test',
                              password='test',
                              auth_method='basic',
                              message_encryption='invalid_value'
                              )
        transport.build_session()

    assert str(exc.value) == "invalid message_encryption arg: invalid_value. Should be 'auto', 'always', or 'never'"
