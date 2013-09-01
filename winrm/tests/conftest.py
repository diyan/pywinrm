import os
import json
from pytest import skip, fixture


@fixture(scope='module')
def winrm_real():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if os.path.isfile(config_path):
        # TODO consider replace json with yaml for integration test settings
        # TODO json does not support comments
        settings = json.load(open(config_path))

        from winrm.winrm_service import WinRMWebService
        winrm = WinRMWebService(**settings)
        return winrm
    else:
        skip('config.json was not found. Integration tests will be skipped')