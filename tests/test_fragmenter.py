import uuid

from winrm.client import Client
from winrm.contants import WsmvConstant, PsrpMessageType
from winrm.psrp.fragmenter import Fragmenter
from winrm.psrp.message_objects import Message, PrimitiveMessage


def test_fragment_single_message():
    primitive_message = PrimitiveMessage(PsrpMessageType.SESSION_CAPABILITY, {"S": "message"})
    test_message = Message(Message.DESTINATION_SERVER, uuid.UUID(WsmvConstant.EMPTY_UUID),
                           uuid.UUID(WsmvConstant.EMPTY_UUID), primitive_message)
    test_client = Client({'endpoint': 'windows-host', 'username': 'test', 'password': 'test', 'auth_method': 'basic'},
                         2, 'en-US', 'utf-8', 3096, '')

    fragmenter = Fragmenter(test_client)
    actual = fragmenter.fragment_messages(test_message)
    assert actual == [b'AAAAAAAAAAEAAAAAAAAAAAMAAAA5AgAAAAIAAQAAAAAAAAAAAAAAAAA'
                      b'AAAAAAAAAAAAAAAAAAAAAAAAAAO+7vzxTPm1lc3NhZ2U8L1M+']


def test_fragment_single_message_multiple_fragments():
    test_data = "long message" * 50
    primitive_message = PrimitiveMessage(PsrpMessageType.SESSION_CAPABILITY, {"S": test_data})
    test_message = Message(Message.DESTINATION_SERVER, uuid.UUID(WsmvConstant.EMPTY_UUID),
                           uuid.UUID(WsmvConstant.EMPTY_UUID), primitive_message)
    test_client = Client({'endpoint': 'windows-host', 'username': 'test', 'password': 'test', 'auth_method': 'basic'},
                         2, 'en-US', 'utf-8', 3096, '')

    fragmenter = Fragmenter(test_client)
    actual = fragmenter.fragment_messages(test_message)
    assert actual == [b'AAAAAAAAAAEAAAAAAAAAAAEAAAI6AgAAAAIAAQAAAAAAAAAAAAAAAAA'
                      b'AAAAAAAAAAAAAAAAAAAAAAAAAAO+7vzxTPmxvbmcgbWVzc2FnZWxvbm'
                      b'cgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc'
                      b'2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxv'
                      b'bmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWV'
                      b'zc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZW'
                      b'xvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgb'
                      b'WVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2Fn'
                      b'ZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmc'
                      b'gbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2'
                      b'FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvb'
                      b'mcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVz'
                      b'c2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWx'
                      b'vbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbW'
                      b'Vzc2FnZWxvbmcgbWVz',
                      b'AAAAAAAAAAEAAAAAAAAAAQIAAABQc2FnZWxvbmcgbWVzc2FnZWxvbmc'
                      b'gbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2'
                      b'FnZWxvbmcgbWVzc2FnZTwvUz4=']


def test_fragment_multiple_messages_small():
    primitive_message = PrimitiveMessage(PsrpMessageType.SESSION_CAPABILITY, {"S": "message"})
    test_message = Message(Message.DESTINATION_SERVER, uuid.UUID(WsmvConstant.EMPTY_UUID),
                           uuid.UUID(WsmvConstant.EMPTY_UUID), primitive_message)
    test_client = Client({'endpoint': 'windows-host', 'username': 'test', 'password': 'test', 'auth_method': 'basic'},
                         2, 'en-US', 'utf-8', 3096, '')

    fragmenter = Fragmenter(test_client)
    actual = fragmenter.fragment_messages([test_message, test_message])
    assert actual == [b'AAAAAAAAAAEAAAAAAAAAAAMAAAA5AgAAAAIAAQAAAAAAAAAAAAAAAAA'
                      b'AAAAAAAAAAAAAAAAAAAAAAAAAAO+7vzxTPm1lc3NhZ2U8L1M+AAAAAA'
                      b'AAAAIAAAAAAAAAAAMAAAA5AgAAAAIAAQAAAAAAAAAAAAAAAAAAAAAAA'
                      b'AAAAAAAAAAAAAAAAAAAAO+7vzxTPm1lc3NhZ2U8L1M+']


def test_fragment_multiple_messages_small_and_big():
    primitive_message = PrimitiveMessage(PsrpMessageType.SESSION_CAPABILITY, {"S": "message"})
    test_message = Message(Message.DESTINATION_SERVER, uuid.UUID(WsmvConstant.EMPTY_UUID),
                           uuid.UUID(WsmvConstant.EMPTY_UUID), primitive_message)
    primitive_message_large = PrimitiveMessage(PsrpMessageType.SESSION_CAPABILITY, {"S": "long message" * 50})
    test_message_large = Message(Message.DESTINATION_SERVER, uuid.UUID(WsmvConstant.EMPTY_UUID),
                                 uuid.UUID(WsmvConstant.EMPTY_UUID), primitive_message_large)

    test_client = Client({'endpoint': 'windows-host', 'username': 'test', 'password': 'test', 'auth_method': 'basic'},
                         2, 'en-US', 'utf-8', 3096, '')

    fragmenter = Fragmenter(test_client)
    actual = fragmenter.fragment_messages([test_message, test_message_large])
    assert actual == [b'AAAAAAAAAAEAAAAAAAAAAAMAAAA5AgAAAAIAAQAAAAAAAAAAAAAAAAA'
                      b'AAAAAAAAAAAAAAAAAAAAAAAAAAO+7vzxTPm1lc3NhZ2U8L1M+',
                      b'AAAAAAAAAAIAAAAAAAAAAAEAAAI6AgAAAAIAAQAAAAAAAAAAAAAAAAA'
                      b'AAAAAAAAAAAAAAAAAAAAAAAAAAO+7vzxTPmxvbmcgbWVzc2FnZWxvbm'
                      b'cgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc'
                      b'2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxv'
                      b'bmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWV'
                      b'zc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZW'
                      b'xvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgb'
                      b'WVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2Fn'
                      b'ZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmc'
                      b'gbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2'
                      b'FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvb'
                      b'mcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVz'
                      b'c2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWx'
                      b'vbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbW'
                      b'Vzc2FnZWxvbmcgbWVz',
                      b'AAAAAAAAAAIAAAAAAAAAAQIAAABQc2FnZWxvbmcgbWVzc2FnZWxvbmc'
                      b'gbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2'
                      b'FnZWxvbmcgbWVzc2FnZTwvUz4=']


def test_fragment_two_smalls_two_fragments():
    primitive_message = PrimitiveMessage(PsrpMessageType.SESSION_CAPABILITY, {"S": "long message" * 25})
    test_message = Message(Message.DESTINATION_SERVER, uuid.UUID(WsmvConstant.EMPTY_UUID),
                           uuid.UUID(WsmvConstant.EMPTY_UUID), primitive_message)

    test_client = Client({'endpoint': 'windows-host', 'username': 'test', 'password': 'test', 'auth_method': 'basic'},
                         2, 'en-US', 'utf-8', 3096, '')

    fragmenter = Fragmenter(test_client)
    actual = fragmenter.fragment_messages([test_message, test_message])
    assert actual == [b'AAAAAAAAAAEAAAAAAAAAAAMAAAFeAgAAAAIAAQAAAAAAAAAAAAAAAAA'
                      b'AAAAAAAAAAAAAAAAAAAAAAAAAAO+7vzxTPmxvbmcgbWVzc2FnZWxvbm'
                      b'cgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc'
                      b'2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxv'
                      b'bmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWV'
                      b'zc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZW'
                      b'xvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgb'
                      b'WVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2Fn'
                      b'ZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZTwvUz4'
                      b'=',
                      b'AAAAAAAAAAIAAAAAAAAAAAMAAAFeAgAAAAIAAQAAAAAAAAAAAAAAAAA'
                      b'AAAAAAAAAAAAAAAAAAAAAAAAAAO+7vzxTPmxvbmcgbWVzc2FnZWxvbm'
                      b'cgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc'
                      b'2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxv'
                      b'bmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWV'
                      b'zc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZW'
                      b'xvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgb'
                      b'WVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2Fn'
                      b'ZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZWxvbmcgbWVzc2FnZTwvUz4'
                      b'=']
