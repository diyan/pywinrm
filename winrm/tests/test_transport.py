# coding=utf-8
import os
import unittest

from winrm import transport


class TestTransport(unittest.TestCase):
    maxDiff = 2048
    _old_env = None

    def setUp(self):
        super(TestTransport, self).setUp()
        self._old_env = {}
        os.environ.pop('REQUESTS_CA_BUNDLE', None)
        os.environ.pop('TRAVIS_APT_PROXY', None)
        os.environ.pop('CURL_CA_BUNDLE', None)
        os.environ.pop('HTTPS_PROXY', None)
        os.environ.pop('HTTP_PROXY', None)
        os.environ.pop('NO_PROXY', None)
        transport.DISPLAYED_PROXY_WARNING = False

    def tearDown(self):
        super(TestTransport, self).tearDown()
        os.environ.pop('REQUESTS_CA_BUNDLE', None)
        os.environ.pop('TRAVIS_APT_PROXY', None)
        os.environ.pop('CURL_CA_BUNDLE', None)
        os.environ.pop('HTTPS_PROXY', None)
        os.environ.pop('HTTP_PROXY', None)
        os.environ.pop('NO_PROXY', None)

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
