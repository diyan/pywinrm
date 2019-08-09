import os
import mock
import unittest
import requests_mock
from winrm import transport

if os.environ.get('PYWINRM_TEST_CREDSSP') == '1':
    EXPECT_CREDSSP = True
elif os.environ.get('PYWINRM_TEST_CREDSSP') == '0':
    EXPECT_CREDSSP = False
else:
    EXPECT_CREDSSP = transport.HAVE_CREDSSP

if os.environ.get('PYWINRM_TEST_KERBEROS') == '1':
    EXPECT_KERBEROS = True
elif os.environ.get('PYWINRM_TEST_KERBEROS') == '0':
    EXPECT_KERBEROS = False
else:
    EXPECT_KERBEROS = transport.HAVE_KERBEROS


class BaseTest(unittest.TestCase):
    maxDiff = 2048
    _old_env = None

    def setUp(self):
        super(BaseTest, self).setUp()
        self.mocked_request = requests_mock.Mocker()
        self.mocked_request.start()
        self._old_env = {}
        os.environ.pop('REQUESTS_CA_BUNDLE', None)
        os.environ.pop('TRAVIS_APT_PROXY', None)
        os.environ.pop('CURL_CA_BUNDLE', None)
        os.environ.pop('HTTPS_PROXY', None)
        os.environ.pop('HTTP_PROXY', None)
        os.environ.pop('NO_PROXY', None)

    def tearDown(self):
        super(BaseTest, self).tearDown()
        os.environ.pop('REQUESTS_CA_BUNDLE', None)
        os.environ.pop('TRAVIS_APT_PROXY', None)
        os.environ.pop('CURL_CA_BUNDLE', None)
        os.environ.pop('HTTPS_PROXY', None)
        os.environ.pop('HTTP_PROXY', None)
        os.environ.pop('NO_PROXY', None)
        self.mocked_request.stop()

    def auto_patch(self, to_patch, spec=True):
        """
        Allow for mocking setup within setUp and tearDown in a single method.

        :param to_patch: Name of object to patch
        :param spec: Whether mock should adhere to the spec
        :return: The mock.Mock object.
        """
        patcher = mock.patch(to_patch, spec=spec)
        patched = patcher.start()
        self.addCleanup(patcher.stop)
        return patched
