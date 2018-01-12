# coding=utf-8
import os
import tempfile
from winrm.transport import Transport


def test_build_session_cert_validate():
    t_default = Transport(endpoint="Endpoint",
                          server_cert_validation='validate',
                          username='test',
                          password='test',
                          auth_method='basic',
                          )
    t_ca_override = Transport(endpoint="Endpoint",
                              server_cert_validation='validate',
                              username='test',
                              password='test',
                              auth_method='basic',
                              ca_trust_path='overridepath',
                              )
    try:
        os.environ['REQUESTS_CA_BUNDLE'] = 'path_to_REQUESTS_CA_CERT'
        t_default.build_session()
        t_ca_override.build_session()
        assert(t_default.session.verify == 'path_to_REQUESTS_CA_CERT')
        assert(t_ca_override.session.verify == 'overridepath')
    finally:
        del os.environ['REQUESTS_CA_BUNDLE']

    try:
        os.environ['CURL_CA_BUNDLE'] = 'path_to_CURL_CA_CERT'
        t_default.build_session()
        t_ca_override.build_session()
        assert(t_default.session.verify == 'path_to_CURL_CA_CERT')
        assert (t_ca_override.session.verify == 'overridepath')
    finally:
        del os.environ['CURL_CA_BUNDLE']


def test_build_session_cert_ignore():
    t_default = Transport(endpoint="Endpoint",
                          server_cert_validation='ignore',
                          username='test',
                          password='test',
                          auth_method='basic',
                          )
    t_ca_override = Transport(endpoint="Endpoint",
                              server_cert_validation='ignore',
                              username='test',
                              password='test',
                              auth_method='basic',
                              ca_trust_path='boguspath'
                              )
    try:
        os.environ['REQUESTS_CA_BUNDLE'] = 'path_to_REQUESTS_CA_CERT'
        os.environ['CURL_CA_BUNDLE'] = 'path_to_CURL_CA_CERT'
        t_default.build_session()
        t_ca_override.build_session()
        assert(isinstance(t_default.session.verify, bool) and not t_default.session.verify)
        assert (isinstance(t_ca_override.session.verify, bool) and not t_ca_override.session.verify)
    finally:
        del os.environ['REQUESTS_CA_BUNDLE']
        del os.environ['CURL_CA_BUNDLE']
