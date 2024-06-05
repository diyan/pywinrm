# coding=utf-8
import os
import unittest

import mock

from winrm import transport
from winrm.exceptions import InvalidCredentialsError, WinRMError


class TestTransport(unittest.TestCase):
    maxDiff = 2048
    _old_env = None

    def setUp(self):
        super(TestTransport, self).setUp()
        self._old_env = {}
        os.environ.pop("REQUESTS_CA_BUNDLE", None)
        os.environ.pop("TRAVIS_APT_PROXY", None)
        os.environ.pop("CURL_CA_BUNDLE", None)
        os.environ.pop("HTTPS_PROXY", None)
        os.environ.pop("HTTP_PROXY", None)
        os.environ.pop("NO_PROXY", None)
        transport.DISPLAYED_PROXY_WARNING = False
        transport.DISPLAYED_CA_TRUST_WARNING = False

    def tearDown(self):
        super(TestTransport, self).tearDown()
        os.environ.pop("REQUESTS_CA_BUNDLE", None)
        os.environ.pop("TRAVIS_APT_PROXY", None)
        os.environ.pop("CURL_CA_BUNDLE", None)
        os.environ.pop("HTTPS_PROXY", None)
        os.environ.pop("HTTP_PROXY", None)
        os.environ.pop("NO_PROXY", None)

    def test_build_session_cert_validate_default(self):
        t_default = transport.Transport(
            endpoint="https://example.com",
            username="test",
            password="test",
            auth_method="basic",
        )
        t_default.build_session()
        self.assertEqual(True, t_default.session.verify)

    def test_build_session_cert_validate_default_env(self):
        os.environ["REQUESTS_CA_BUNDLE"] = "path_to_REQUESTS_CA_CERT"

        t_default = transport.Transport(
            endpoint="https://example.com",
            username="test",
            password="test",
            auth_method="basic",
        )
        t_default.build_session()
        self.assertEqual("path_to_REQUESTS_CA_CERT", t_default.session.verify)

    def test_build_session_cert_validate_1(self):
        os.environ["REQUESTS_CA_BUNDLE"] = "path_to_REQUESTS_CA_CERT"

        t_default = transport.Transport(
            endpoint="https://example.com",
            server_cert_validation="validate",
            username="test",
            password="test",
            auth_method="basic",
        )
        t_default.build_session()
        self.assertEqual("path_to_REQUESTS_CA_CERT", t_default.session.verify)

    def test_build_session_cert_validate_2(self):
        os.environ["CURL_CA_BUNDLE"] = "path_to_CURL_CA_CERT"

        t_default = transport.Transport(
            endpoint="https://example.com",
            server_cert_validation="validate",
            username="test",
            password="test",
            auth_method="basic",
        )
        t_default.build_session()
        self.assertEqual("path_to_CURL_CA_CERT", t_default.session.verify)

    def test_build_session_cert_override_1(self):
        os.environ["REQUESTS_CA_BUNDLE"] = "path_to_REQUESTS_CA_CERT"

        t_default = transport.Transport(
            endpoint="https://example.com",
            server_cert_validation="validate",
            username="test",
            password="test",
            auth_method="basic",
            ca_trust_path="overridepath",
        )
        t_default.build_session()
        self.assertEqual("overridepath", t_default.session.verify)

    def test_build_session_cert_override_2(self):
        os.environ["CURL_CA_BUNDLE"] = "path_to_CURL_CA_CERT"

        t_default = transport.Transport(
            endpoint="https://example.com",
            server_cert_validation="validate",
            username="test",
            password="test",
            auth_method="basic",
            ca_trust_path="overridepath",
        )
        t_default.build_session()
        self.assertEqual("overridepath", t_default.session.verify)

    def test_build_session_cert_override_3(self):
        os.environ["CURL_CA_BUNDLE"] = "path_to_CURL_CA_CERT"

        t_default = transport.Transport(
            endpoint="https://example.com",
            server_cert_validation="validate",
            username="test",
            password="test",
            auth_method="basic",
            ca_trust_path=None,
        )
        t_default.build_session()
        self.assertEqual(True, t_default.session.verify)

    def test_build_session_cert_ignore_1(self):
        os.environ["REQUESTS_CA_BUNDLE"] = "path_to_REQUESTS_CA_CERT"
        os.environ["CURL_CA_BUNDLE"] = "path_to_CURL_CA_CERT"

        t_default = transport.Transport(
            endpoint="https://example.com",
            server_cert_validation="ignore",
            username="test",
            password="test",
            auth_method="basic",
        )

        t_default.build_session()
        self.assertIs(False, t_default.session.verify)

    def test_build_session_cert_ignore_2(self):
        os.environ["REQUESTS_CA_BUNDLE"] = "path_to_REQUESTS_CA_CERT"
        os.environ["CURL_CA_BUNDLE"] = "path_to_CURL_CA_CERT"

        t_default = transport.Transport(
            endpoint="https://example.com", server_cert_validation="ignore", username="test", password="test", auth_method="basic", ca_trust_path="boguspath"
        )

        t_default.build_session()
        self.assertIs(False, t_default.session.verify)

    def test_build_session_proxy_none(self):
        os.environ["HTTP_PROXY"] = "random_proxy"
        os.environ["HTTPS_PROXY"] = "random_proxy_2"

        t_default = transport.Transport(
            endpoint="https://example.com", server_cert_validation="validate", username="test", password="test", auth_method="basic", proxy=None
        )

        t_default.build_session()
        self.assertEqual({"no_proxy": "*"}, t_default.session.proxies)

    def test_build_session_proxy_defined(self):
        t_default = transport.Transport(
            endpoint="https://example.com", server_cert_validation="validate", username="test", password="test", auth_method="basic", proxy="test_proxy"
        )

        t_default.build_session()
        self.assertEqual({"http": "test_proxy", "https": "test_proxy"}, t_default.session.proxies)

    def test_build_session_proxy_defined_and_env(self):
        os.environ["HTTPS_PROXY"] = "random_proxy"

        t_default = transport.Transport(
            endpoint="https://example.com", server_cert_validation="validate", username="test", password="test", auth_method="basic", proxy="test_proxy"
        )

        t_default.build_session()
        self.assertEqual({"http": "test_proxy", "https": "test_proxy"}, t_default.session.proxies)

    def test_build_session_proxy_with_env_https(self):
        os.environ["HTTPS_PROXY"] = "random_proxy"

        t_default = transport.Transport(
            endpoint="https://example.com",
            server_cert_validation="validate",
            username="test",
            password="test",
            auth_method="basic",
        )

        t_default.build_session()
        self.assertEqual({"https": "random_proxy"}, t_default.session.proxies)

    def test_build_session_proxy_with_env_http(self):
        os.environ["HTTP_PROXY"] = "random_proxy"

        t_default = transport.Transport(
            endpoint="https://example.com",
            server_cert_validation="validate",
            username="test",
            password="test",
            auth_method="basic",
        )

        t_default.build_session()
        self.assertEqual({"http": "random_proxy"}, t_default.session.proxies)

    def test_build_session_server_cert_validation_invalid(self):
        with self.assertRaises(WinRMError) as exc:
            transport.Transport(
                endpoint="Endpoint",
                server_cert_validation="invalid_value",
                username="test",
                password="test",
                auth_method="basic",
            )
        self.assertEqual("invalid server_cert_validation mode: invalid_value", str(exc.exception))

    def test_build_session_krb_delegation_as_str(self):
        winrm_transport = transport.Transport(
            endpoint="Endpoint", server_cert_validation="validate", username="test", password="test", auth_method="kerberos", kerberos_delegation="True"
        )
        self.assertTrue(winrm_transport.kerberos_delegation)

    def test_build_session_krb_delegation_as_invalid_str(self):
        with self.assertRaises(ValueError) as exc:
            transport.Transport(
                endpoint="Endpoint",
                server_cert_validation="validate",
                username="test",
                password="test",
                auth_method="kerberos",
                kerberos_delegation="invalid_value",
            )
        self.assertEqual("invalid truth value 'invalid_value'", str(exc.exception))

    def test_build_session_no_username(self):
        with self.assertRaises(InvalidCredentialsError) as exc:
            transport.Transport(
                endpoint="Endpoint",
                server_cert_validation="validate",
                password="test",
                auth_method="basic",
            )
        self.assertEqual("auth method basic requires a username", str(exc.exception))

    def test_build_session_no_password(self):
        with self.assertRaises(InvalidCredentialsError) as exc:
            transport.Transport(
                endpoint="Endpoint",
                server_cert_validation="validate",
                username="test",
                auth_method="basic",
            )
        self.assertEqual("auth method basic requires a password", str(exc.exception))

    def test_build_session_invalid_auth(self):
        winrm_transport = transport.Transport(
            endpoint="Endpoint",
            server_cert_validation="validate",
            username="test",
            password="test",
            auth_method="invalid_value",
        )

        with self.assertRaises(WinRMError) as exc:
            winrm_transport.build_session()
        self.assertEqual("unsupported auth method: invalid_value", str(exc.exception))

    def test_build_session_invalid_encryption(self):

        with self.assertRaises(WinRMError) as exc:
            transport.Transport(
                endpoint="Endpoint",
                server_cert_validation="validate",
                username="test",
                password="test",
                auth_method="basic",
                message_encryption="invalid_value",
            )
        self.assertEqual("invalid message_encryption arg: invalid_value. Should be 'auto', 'always', or 'never'", str(exc.exception))

    @mock.patch("requests.Session")
    def test_close_session(self, mock_session):
        t_default = transport.Transport(
            endpoint="Endpoint",
            server_cert_validation="ignore",
            username="test",
            password="test",
            auth_method="basic",
        )
        t_default.build_session()
        t_default.close_session()
        mock_session.return_value.close.assert_called_once_with()
        self.assertIsNone(t_default.session)

    @mock.patch("requests.Session")
    def test_close_session_not_built(self, mock_session):
        t_default = transport.Transport(
            endpoint="Endpoint",
            server_cert_validation="ignore",
            username="test",
            password="test",
            auth_method="basic",
        )
        t_default.close_session()
        self.assertFalse(mock_session.return_value.close.called)
        self.assertIsNone(t_default.session)
