import os
import mock
import unittest
import requests_mock

if os.environ.get('PYWINRM_TEST_CREDSSP') == '1':
    EXPECT_CREDSSP = True
elif os.environ.get('PYWINRM_TEST_CREDSSP') == '0':
    EXPECT_CREDSSP = False
else:
    try:
        from requests_credssp import HttpCredSSPAuth  # NOQA

        EXPECT_CREDSSP = True
    except ImportError as ie:
        EXPECT_CREDSSP = False

if os.environ.get('PYWINRM_TEST_KERBEROS') == '1':
    EXPECT_KERBEROS = True
elif os.environ.get('PYWINRM_TEST_KERBEROS') == '0':
    EXPECT_KERBEROS = False
else:
    try:
        from .vendor.requests_kerberos import HTTPKerberosAuth, REQUIRED  # NOQA

        EXPECT_KERBEROS = True
    except ImportError as ie:
        EXPECT_KERBEROS = False


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
