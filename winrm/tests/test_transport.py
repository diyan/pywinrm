# coding=utf-8
import os
from winrm.transport import Transport


def test_build_session():
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
