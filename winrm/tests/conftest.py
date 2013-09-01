import os
import json
import sys
from pytest import skip, fixture


def pytest_cmdline_preparse(config, args):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../winrm'))
    sys.path.insert(0, os.path.dirname(__file__))


@fixture(scope='module')
def winrm_real(request):
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if os.path.isfile(config_path):
        # TODO consider replace json with yaml for integration test settings
        # TODO json does not support comments
        settings = json.load(open(config_path))

        from winrm_service import WinRMWebService
        winrm = WinRMWebService(**settings)
        return winrm
    else:
        skip('config.json was not found. Integration tests will be skipped')