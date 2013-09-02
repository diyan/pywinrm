import os
import json
from pytest import skip, fixture


@fixture(scope='module')
def protocol_real():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if os.path.isfile(config_path):
        # TODO consider replace json with yaml for integration test settings
        # TODO json does not support comments
        settings = json.load(open(config_path))

        from winrm.protocol import Protocol
        protocol = Protocol(**settings)
        return protocol
    else:
        skip('config.json was not found. Integration tests will be skipped')