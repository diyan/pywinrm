import uuid

from winrm.contants import MessageTypes
from winrm.psrp.fragmenter import Fragmenter
from winrm.psrp.messages import SessionCapability, InitRunspacePool, Message

class PsrpHandler(object):
    def __init__(self, transport):
        self.transport = transport
        self.fragmenter = Fragmenter()

    def create_runspace_pool(self):
        session_capability = SessionCapability()
        session_capability_msg = session_capability.create_message_data("2.2", "2.0", "1.1.0.1")

        init_runspace_pool = InitRunspacePool()
        init_runspace_pool_msg= init_runspace_pool.create_message_data("1", "2")

        sc_msg = Message()
        sc = sc_msg.create_message(Message.DESTINATION_SERVER, MessageTypes.SESSION_CAPABILITY, uuid.uuid4(), uuid.uuid4(), session_capability_msg)

        init_pool_msg = Message()
        init_pool = init_pool_msg.create_message(Message.DESTINATION_SERVER, MessageTypes.INIT_RUNSPACEPOOL, uuid.uuid4(), uuid.uuid4(), init_runspace_pool_msg)

        a = ''