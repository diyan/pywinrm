# flake8: noqa
import os
import uuid
import xmltodict
from pytest import skip, fixture
from mock import patch

def sort_dict(ordered_dict):
    items = sorted(ordered_dict.items(), key=lambda x: x[0])
    ordered_dict.clear()
    for key, value in items:
        if isinstance(value, dict):
            sort_dict(value)
        ordered_dict[key] = value


def xml_str_compare(first, second):
    first_dict = xmltodict.parse(first)
    second_dict = xmltodict.parse(second)
    sort_dict(first_dict)
    sort_dict(second_dict)
    abc = first_dict == second_dict
    if not abc:
        print(xmltodict.unparse(first_dict, pretty=True))
        print(xmltodict.unparse(second_dict, pretty=True))

    return abc


@fixture(scope='module')
def wsmv_client_fake(request):
    uuid4_patcher = patch('uuid.uuid4')
    uuid4_mock = uuid4_patcher.start()
    uuid4_mock.return_value = uuid.UUID(
        '11111111-1111-1111-1111-111111111111')

    from winrm.protocol import Protocol

    protocol_fake = Protocol(
        endpoint='http://windows-host:5985/wsman',
        transport='plaintext',
        username='john.smith',
        password='secret')

    protocol_fake.transport = TransportStub()

    def uuid4_patch_stop():
        uuid4_patcher.stop()

    request.addfinalizer(uuid4_patch_stop)
    return protocol_fake



@fixture(scope='module')
def protocol_fake(request):
    uuid4_patcher = patch('uuid.uuid4')
    uuid4_mock = uuid4_patcher.start()
    uuid4_mock.return_value = uuid.UUID(
        '11111111-1111-1111-1111-111111111111')

    from winrm.protocol import Protocol

    protocol_fake = Protocol(
        endpoint='http://windows-host:5985/wsman',
        transport='plaintext',
        username='john.smith',
        password='secret')

    protocol_fake.transport = TransportStub()

    def uuid4_patch_stop():
        uuid4_patcher.stop()

    request.addfinalizer(uuid4_patch_stop)
    return protocol_fake


@fixture(scope='module')
def protocol_real():
    endpoint = os.environ.get('WINRM_ENDPOINT', None)
    transport = os.environ.get('WINRM_TRANSPORT', None)
    username = os.environ.get('WINRM_USERNAME', None)
    password = os.environ.get('WINRM_PASSWORD', None)
    if endpoint:
        settings = dict(
            endpoint=endpoint,
            operation_timeout_sec=5,
            read_timeout_sec=7
        )
        if transport:
            settings['transport'] = transport
        if username:
            settings['username'] = username
        if password:
            settings['password'] = password

        from winrm.protocol import Protocol
        protocol = Protocol(**settings)
        return protocol
    else:
        skip('WINRM_ENDPOINT environment variable was not set. Integration tests will be skipped')
