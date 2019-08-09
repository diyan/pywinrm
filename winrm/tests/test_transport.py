# coding=utf-8
import os
import mock
import unittest
import requests
from . import base as base_test
from distutils.version import StrictVersion

from winrm import transport
from winrm.exceptions import WinRMError, InvalidCredentialsError

REQUEST_VERSION = requests.__version__.split('.')


class TestTransport(base_test.BaseTest):

    def setUp(self):
        super(TestTransport, self).setUp()
        transport.DISPLAYED_PROXY_WARNING = False
        transport.DISPLAYED_CA_TRUST_WARNING = False

    def test_build_session_cert_validate_default(self):
        t_default = transport.Transport(endpoint="https://example.com",
                                        username='test',
                                        password='test',
                                        auth_method='basic',
                                        )
        t_default.build_session()
        self.assertEqual(True, t_default.session.verify)

    def test_build_session_cert_validate_default_env(self):
        os.environ['REQUESTS_CA_BUNDLE'] = 'path_to_REQUESTS_CA_CERT'

        t_default = transport.Transport(endpoint="https://example.com",
                                        username='test',
                                        password='test',
                                        auth_method='basic',
                                        )
        t_default.build_session()
        self.assertEqual('path_to_REQUESTS_CA_CERT', t_default.session.verify)

    def test_build_session_cert_validate_1(self):
        os.environ['REQUESTS_CA_BUNDLE'] = 'path_to_REQUESTS_CA_CERT'

        t_default = transport.Transport(endpoint="https://example.com",
                                        server_cert_validation='validate',
                                        username='test',
                                        password='test',
                                        auth_method='basic',
                                        )
        t_default.build_session()
        self.assertEqual('path_to_REQUESTS_CA_CERT', t_default.session.verify)

    def test_build_session_cert_validate_2(self):
        os.environ['CURL_CA_BUNDLE'] = 'path_to_CURL_CA_CERT'

        t_default = transport.Transport(endpoint="https://example.com",
                                        server_cert_validation='validate',
                                        username='test',
                                        password='test',
                                        auth_method='basic',
                                        )
        t_default.build_session()
        self.assertEqual('path_to_CURL_CA_CERT', t_default.session.verify)

    def test_build_session_cert_override_1(self):
        os.environ['REQUESTS_CA_BUNDLE'] = 'path_to_REQUESTS_CA_CERT'

        t_default = transport.Transport(endpoint="https://example.com",
                                        server_cert_validation='validate',
                                        username='test',
                                        password='test',
                                        auth_method='basic',
                                        ca_trust_path='overridepath',
                                        )
        t_default.build_session()
        self.assertEqual('overridepath', t_default.session.verify)

    def test_build_session_cert_override_2(self):
        os.environ['CURL_CA_BUNDLE'] = 'path_to_CURL_CA_CERT'

        t_default = transport.Transport(endpoint="https://example.com",
                                        server_cert_validation='validate',
                                        username='test',
                                        password='test',
                                        auth_method='basic',
                                        ca_trust_path='overridepath',
                                        )
        t_default.build_session()
        self.assertEqual('overridepath', t_default.session.verify)

    def test_build_session_cert_override_3(self):
        os.environ['CURL_CA_BUNDLE'] = 'path_to_CURL_CA_CERT'

        t_default = transport.Transport(endpoint="https://example.com",
                                        server_cert_validation='validate',
                                        username='test',
                                        password='test',
                                        auth_method='basic',
                                        ca_trust_path=None,
                                        )
        t_default.build_session()
        self.assertEqual(True, t_default.session.verify)

    def test_build_session_cert_ignore_1(self):
        os.environ['REQUESTS_CA_BUNDLE'] = 'path_to_REQUESTS_CA_CERT'
        os.environ['CURL_CA_BUNDLE'] = 'path_to_CURL_CA_CERT'

        t_default = transport.Transport(endpoint="https://example.com",
                                        server_cert_validation='ignore',
                                        username='test',
                                        password='test',
                                        auth_method='basic',
                                        )

        t_default.build_session()
        self.assertIs(False, t_default.session.verify)

    def test_build_session_cert_ignore_2(self):
        os.environ['REQUESTS_CA_BUNDLE'] = 'path_to_REQUESTS_CA_CERT'
        os.environ['CURL_CA_BUNDLE'] = 'path_to_CURL_CA_CERT'

        t_default = transport.Transport(endpoint="https://example.com",
                                        server_cert_validation='ignore',
                                        username='test',
                                        password='test',
                                        auth_method='basic',
                                        ca_trust_path='boguspath'
                                        )

        t_default.build_session()
        self.assertIs(False, t_default.session.verify)

    # TODO: I am not sure in which version changed specifically, but this can be updated if we need to find out.
    @unittest.skipIf(StrictVersion(requests.__version__) > StrictVersion('2.9.1'), reason="Skipping for versions 2.9.1 or older")
    def test_build_session_proxy_none_old_request(self):
        os.environ['HTTP_PROXY'] = 'random_proxy'
        os.environ['HTTPS_PROXY'] = 'random_proxy_2'

        t_default = transport.Transport(endpoint="https://example.com",
                                        server_cert_validation='validate',
                                        username='test',
                                        password='test',
                                        auth_method='basic',
                                        proxy=None
                                        )

        t_default.build_session()
        self.assertEqual({'no_proxy': '*', 'http': 'random_proxy', 'https': 'random_proxy_2'}, t_default.session.proxies)

    @unittest.skipIf(StrictVersion(requests.__version__) <= StrictVersion('2.9.1'), reason="Skipping for versions newer than 2.9.1")
    def test_build_session_proxy_none(self):
        os.environ['HTTP_PROXY'] = 'random_proxy'
        os.environ['HTTPS_PROXY'] = 'random_proxy_2'

        t_default = transport.Transport(endpoint="https://example.com",
                                        server_cert_validation='validate',
                                        username='test',
                                        password='test',
                                        auth_method='basic',
                                        proxy=None
                                        )

        t_default.build_session()
        self.assertEqual({'no_proxy': '*'}, t_default.session.proxies)

    def test_build_session_proxy_defined(self):
        t_default = transport.Transport(endpoint="https://example.com",
                                        server_cert_validation='validate',
                                        username='test',
                                        password='test',
                                        auth_method='basic',
                                        proxy='test_proxy'
                                        )

        t_default.build_session()
        self.assertEqual({'http': 'test_proxy', 'https': 'test_proxy'}, t_default.session.proxies)

    def test_build_session_proxy_defined_and_env(self):
        os.environ['HTTPS_PROXY'] = 'random_proxy'

        t_default = transport.Transport(endpoint="https://example.com",
                                        server_cert_validation='validate',
                                        username='test',
                                        password='test',
                                        auth_method='basic',
                                        proxy='test_proxy'
                                        )

        t_default.build_session()
        self.assertEqual({'http': 'test_proxy', 'https': 'test_proxy'}, t_default.session.proxies)

    def test_build_session_proxy_with_env_https(self):
        os.environ['HTTPS_PROXY'] = 'random_proxy'

        t_default = transport.Transport(endpoint="https://example.com",
                                        server_cert_validation='validate',
                                        username='test',
                                        password='test',
                                        auth_method='basic',
                                        )

        t_default.build_session()
        self.assertEqual({'https': 'random_proxy'}, t_default.session.proxies)

    def test_build_session_proxy_with_env_http(self):
        os.environ['HTTP_PROXY'] = 'random_proxy'

        t_default = transport.Transport(endpoint="https://example.com",
                                        server_cert_validation='validate',
                                        username='test',
                                        password='test',
                                        auth_method='basic',
                                        )

        t_default.build_session()
        self.assertEqual({'http': 'random_proxy'}, t_default.session.proxies)

    def test_build_session_server_cert_validation_invalid(self):
        with self.assertRaises(WinRMError) as exc:
            transport.Transport(endpoint="Endpoint",
                                server_cert_validation='invalid_value',
                                username='test',
                                password='test',
                                auth_method='basic',
                                )
        self.assertEqual('invalid server_cert_validation mode: invalid_value', str(exc.exception))

    def test_build_session_krb_delegation_as_str(self):
        winrm_transport = transport.Transport(endpoint="Endpoint",
                                              server_cert_validation='validate',
                                              username='test',
                                              password='test',
                                              auth_method='kerberos',
                                              kerberos_delegation='True'
                                              )
        self.assertTrue(winrm_transport.kerberos_delegation)

    def test_build_session_krb_delegation_as_invalid_str(self):
        with self.assertRaises(ValueError) as exc:
            transport.Transport(endpoint="Endpoint",
                                server_cert_validation='validate',
                                username='test',
                                password='test',
                                auth_method='kerberos',
                                kerberos_delegation='invalid_value'
                                )
        self.assertEqual("invalid truth value 'invalid_value'", str(exc.exception))

    def test_build_session_no_username(self):
        with self.assertRaises(InvalidCredentialsError) as exc:
            transport.Transport(endpoint="Endpoint",
                                server_cert_validation='validate',
                                password='test',
                                auth_method='basic',
                                )
        self.assertEqual("auth method basic requires a username", str(exc.exception))

    def test_build_session_no_password(self):
        with self.assertRaises(InvalidCredentialsError) as exc:
            transport.Transport(endpoint="Endpoint",
                                server_cert_validation='validate',
                                username='test',
                                auth_method='basic',
                                )
        self.assertEqual("auth method basic requires a password", str(exc.exception))

    def test_build_session_invalid_auth(self):
        winrm_transport = transport.Transport(endpoint="Endpoint",
                                              server_cert_validation='validate',
                                              username='test',
                                              password='test',
                                              auth_method='invalid_value',
                                              )

        with self.assertRaises(WinRMError) as exc:
            winrm_transport.build_session()
        self.assertEqual("unsupported auth method: invalid_value", str(exc.exception))

    def test_build_session_invalid_encryption(self):

        with self.assertRaises(WinRMError) as exc:
            transport.Transport(endpoint="Endpoint",
                                server_cert_validation='validate',
                                username='test',
                                password='test',
                                auth_method='basic',
                                message_encryption='invalid_value'
                                )
        self.assertEqual("invalid message_encryption arg: invalid_value. Should be 'auto', 'always', or 'never'", str(exc.exception))

    @mock.patch('requests.Session')
    def test_close_session(self, mock_session):
        t_default = transport.Transport(endpoint="Endpoint",
                                        server_cert_validation='ignore',
                                        username='test',
                                        password='test',
                                        auth_method='basic',
                                        )
        t_default.build_session()
        t_default.close_session()
        mock_session.return_value.close.assert_called_once_with()
        self.assertIsNone(t_default.session)

    @mock.patch('requests.Session')
    def test_close_session_not_built(self, mock_session):
        t_default = transport.Transport(endpoint="Endpoint",
                                        server_cert_validation='ignore',
                                        username='test',
                                        password='test',
                                        auth_method='basic',
                                        )
        t_default.close_session()
        self.assertFalse(mock_session.return_value.close.called)
        self.assertIsNone(t_default.session)


class TestTransportCredSSP(base_test.BaseTest):

    @unittest.skipIf(base_test.EXPECT_CREDSSP is False, reason="Only testing when CredSSP is available")
    def test_with_credssp(self):
        t_default = transport.Transport(endpoint="https://example.com",
                                        username='test',
                                        password='test',
                                        auth_method='credssp',
                                        )
        t_default.build_session()

    @unittest.skipIf(base_test.EXPECT_CREDSSP is True, reason="Only testing when CredSSP is unavailable")
    def test_without_credssp(self):
        t_default = transport.Transport(endpoint="https://example.com",
                                        username='test',
                                        password='test',
                                        auth_method='credssp',
                                        )
        with self.assertRaises(WinRMError) as exc:
            t_default.build_session()
        self.assertEqual(str(exc.exception), 'requests auth method is credssp, but requests-credssp is not installed')


class TestTransportKerberos(base_test.BaseTest):

    @unittest.skipIf(base_test.EXPECT_KERBEROS is False, reason="Only testing when kerberos is available")
    def test_with_kerberos(self):
        t_default = transport.Transport(endpoint="https://example.com",
                                        username='test',
                                        password='test',
                                        auth_method='kerberos',
                                        )
        t_default.build_session()

    @unittest.skipIf(base_test.EXPECT_KERBEROS is True, reason="Only testing when kerberos is unavailable")
    def test_without_kerberos(self):
        t_default = transport.Transport(endpoint="https://example.com",
                                        username='test',
                                        password='test',
                                        auth_method='kerberos',
                                        )
        with self.assertRaises(WinRMError) as exc:
            t_default.build_session()
        self.assertEqual(str(exc.exception), 'requested auth method is kerberos, but requests_kerberos is not installed')
