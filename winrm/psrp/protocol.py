import uuid
import xmltodict

from winrm.contants import WsmvConstant, WsmvResourceURI, WsmvAction, PsrpMessageType, PsrpRunspacePoolState
from winrm.exceptions import WinRMError, WinRMTransportError, WinRMOperationTimeoutError

from winrm.wsmv.objects import WsmvObject
from winrm.wsmv.protocol import WsmvProtocol

from winrm.psrp.fragmenter import Fragmenter, Defragmenter
from winrm.psrp.messages import SessionCapability, InitRunspacePool, Message, RunspacePoolState

class PsrpProtocol(object):
    def __init__(
            self, transport,
            read_timeout_sec=WsmvConstant.DEFAULT_READ_TIMEOUT_SEC,
            operation_timeout_sec=WsmvConstant.DEFAULT_OPERATION_TIMEOUT_SEC,
            locale=WsmvConstant.DEFAULT_LOCALE,
            encoding=WsmvConstant.DEFAULT_ENCODING):

        self.wsmv_protocol = WsmvProtocol(transport, read_timeout_sec, operation_timeout_sec, locale, encoding)
        self.max_envelope_size = self.wsmv_protocol.max_envelope_size
        self.fragmenter = Fragmenter(self.wsmv_protocol)
        self.defragmenter = Defragmenter()
        self.runspace_pool_state = PsrpRunspacePoolState.BEFORE_OPEN

    def create_runspace_pool(self):
        self.runspace_pool_state = PsrpRunspacePoolState.OPENING
        session_capability = SessionCapability("2.3", "2.0", "1.1.0.1")
        init_runspace_pool = InitRunspacePool("1", "1")

        sc = Message(Message.DESTINATION_SERVER, PsrpMessageType.SESSION_CAPABILITY, uuid.uuid4(), uuid.uuid4(), session_capability)
        init_pool = Message(Message.DESTINATION_SERVER, PsrpMessageType.INIT_RUNSPACEPOOL, uuid.uuid4(), uuid.uuid4(), init_runspace_pool)

        fragments = self.fragmenter.fragment_messages([sc, init_pool])
        #fragments = ['AAAAAAAAABEAAAAAAAAAAAMAAALwAgAAAAIAAQDXwZTLiq2cQZ0n2Y7yDEVZAAAAAAAAAAAAAAAAAAAAAO+7vzxPYmogUmVmSWQ9IjAiPjxNUz48VmVyc2lvbiBOPSJwcm90b2NvbHZlcnNpb24iPjIuMzwvVmVyc2lvbj48VmVyc2lvbiBOPSJQU1ZlcnNpb24iPjIuMDwvVmVyc2lvbj48VmVyc2lvbiBOPSJTZXJpYWxpemF0aW9uVmVyc2lvbiI+MS4xLjAuMTwvVmVyc2lvbj48QkEgTj0iVGltZVpvbmUiPkFBRUFBQUQvLy8vL0FRQUFBQUFBQUFBRUFRQUFBQnhUZVhOMFpXMHVRM1Z5Y21WdWRGTjVjM1JsYlZScGJXVmFiMjVsQkFBQUFCZHRYME5oWTJobFpFUmhlV3hwWjJoMFEyaGhibWRsY3cxdFgzUnBZMnR6VDJabWMyVjBEbTFmYzNSaGJtUmhjbVJPWVcxbERtMWZaR0Y1YkdsbmFIUk9ZVzFsQXdBQkFSeFRlWE4wWlcwdVEyOXNiR1ZqZEdsdmJuTXVTR0Z6YUhSaFlteGxDUWtDQUFBQUFCQ3MwVk1BQUFBS0NnUUNBQUFBSEZONWMzUmxiUzVEYjJ4c1pXTjBhVzl1Y3k1SVlYTm9kR0ZpYkdVSEFBQUFDa3h2WVdSR1lXTjBiM0lIVm1WeWMybHZiZ2hEYjIxd1lYSmxjaEJJWVhOb1EyOWtaVkJ5YjNacFpHVnlDRWhoYzJoVGFYcGxCRXRsZVhNR1ZtRnNkV1Z6QUFBREF3QUZCUXNJSEZONWMzUmxiUzVEYjJ4c1pXTjBhVzl1Y3k1SlEyOXRjR0Z5WlhJa1UzbHpkR1Z0TGtOdmJHeGxZM1JwYjI1ekxrbElZWE5vUTI5a1pWQnliM1pwWkdWeUNPeFJPRDhBQUFBQUNnb0RBQUFBQ1FNQUFBQUpCQUFBQUJBREFBQUFBQUFBQUJBRUFBQUFBQUFBQUFzPTwvQkE+PC9NUz48L09iaj4AAAAAAAAAEgAAAAAAAAAAAwAADoICAAAABAABANfBlMuKrZxBnSfZjvIMRVkAAAAAAAAAAAAAAAAAAAAA77u/PE9iaiBSZWZJZD0iMCI+PE1TPjxJMzIgTj0iTWluUnVuc3BhY2VzIj4xPC9JMzI+PEkzMiBOPSJNYXhSdW5zcGFjZXMiPjE8L0kzMj48T2JqIE49IlBTVGhyZWFkT3B0aW9ucyIgUmVmSWQ9IjEiPjxUTiBSZWZJZD0iMCI+PFQ+U3lzdGVtLk1hbmFnZW1lbnQuQXV0b21hdGlvbi5SdW5zcGFjZXMuUFNUaHJlYWRPcHRpb25zPC9UPjxUPlN5c3RlbS5FbnVtPC9UPjxUPlN5c3RlbS5WYWx1ZVR5cGU8L1Q+PFQ+U3lzdGVtLk9iamVjdDwvVD48L1ROPjxUb1N0cmluZz5EZWZhdWx0PC9Ub1N0cmluZz48STMyPjA8L0kzMj48L09iaj48T2JqIE49IkFwYXJ0bWVudFN0YXRlIiBSZWZJZD0iMiI+PFROIFJlZklkPSIxIj48VD5TeXN0ZW0uVGhyZWFkaW5nLkFwYXJ0bWVudFN0YXRlPC9UPjxUPlN5c3RlbS5FbnVtPC9UPjxUPlN5c3RlbS5WYWx1ZVR5cGU8L1Q+PFQ+U3lzdGVtLk9iamVjdDwvVD48L1ROPjxUb1N0cmluZz5Vbmtub3duPC9Ub1N0cmluZz48STMyPjI8L0kzMj48L09iaj48T2JqIE49IkFwcGxpY2F0aW9uQXJndW1lbnRzIiBSZWZJZD0iMyI+PFROIFJlZklkPSIyIj48VD5TeXN0ZW0uTWFuYWdlbWVudC5BdXRvbWF0aW9uLlBTUHJpbWl0aXZlRGljdGlvbmFyeTwvVD48VD5TeXN0ZW0uQ29sbGVjdGlvbnMuSGFzaHRhYmxlPC9UPjxUPlN5c3RlbS5PYmplY3Q8L1Q+PC9UTj48RENUPjxFbj48UyBOPSJLZXkiPlBTVmVyc2lvblRhYmxlPC9TPjxPYmogTj0iVmFsdWUiIFJlZklkPSI0Ij48VE5SZWYgUmVmSWQ9IjIiIC8+PERDVD48RW4+PFMgTj0iS2V5Ij5QU1ZlcnNpb248L1M+PFZlcnNpb24gTj0iVmFsdWUiPjUuMS4xNDM5My42OTM8L1ZlcnNpb24+PC9Fbj48RW4+PFMgTj0iS2V5Ij5QU0VkaXRpb248L1M+PFMgTj0iVmFsdWUiPkRlc2t0b3A8L1M+PC9Fbj48RW4+PFMgTj0iS2V5Ij5QU0NvbXBhdGlibGVWZXJzaW9uczwvUz48T2JqIE49IlZhbHVlIiBSZWZJZD0iNSI+PFROIFJlZklkPSIzIj48VD5TeXN0ZW0uVmVyc2lvbltdPC9UPjxUPlN5c3RlbS5BcnJheTwvVD48VD5TeXN0ZW0uT2JqZWN0PC9UPjwvVE4+PExTVD48VmVyc2lvbj4xLjA8L1ZlcnNpb24+PFZlcnNpb24+Mi4wPC9WZXJzaW9uPjxWZXJzaW9uPjMuMDwvVmVyc2lvbj48VmVyc2lvbj40LjA8L1ZlcnNpb24+PFZlcnNpb24+NS4wPC9WZXJzaW9uPjxWZXJzaW9uPjUuMS4xNDM5My42OTM8L1ZlcnNpb24+PC9MU1Q+PC9PYmo+PC9Fbj48RW4+PFMgTj0iS2V5Ij5DTFJWZXJzaW9uPC9TPjxWZXJzaW9uIE49IlZhbHVlIj40LjAuMzAzMTkuNDIwMDA8L1ZlcnNpb24+PC9Fbj48RW4+PFMgTj0iS2V5Ij5CdWlsZFZlcnNpb248L1M+PFZlcnNpb24gTj0iVmFsdWUiPjEwLjAuMTQzOTMuNjkzPC9WZXJzaW9uPjwvRW4+PEVuPjxTIE49IktleSI+V1NNYW5TdGFja1ZlcnNpb248L1M+PFZlcnNpb24gTj0iVmFsdWUiPjMuMDwvVmVyc2lvbj48L0VuPjxFbj48UyBOPSJLZXkiPlBTUmVtb3RpbmdQcm90b2NvbFZlcnNpb248L1M+PFZlcnNpb24gTj0iVmFsdWUiPjIuMzwvVmVyc2lvbj48L0VuPjxFbj48UyBOPSJLZXkiPlNlcmlhbGl6YXRpb25WZXJzaW9uPC9TPjxWZXJzaW9uIE49IlZhbHVlIj4xLjEuMC4xPC9WZXJzaW9uPjwvRW4+PC9EQ1Q+PC9PYmo+PC9Fbj48L0RDVD48L09iaj48T2JqIE49Ikhvc3RJbmZvIiBSZWZJZD0iNiI+PE1TPjxPYmogTj0iX2hvc3REZWZhdWx0RGF0YSIgUmVmSWQ9IjciPjxNUz48T2JqIE49ImRhdGEiIFJlZklkPSI4Ij48VE4gUmVmSWQ9IjQiPjxUPlN5c3RlbS5Db2xsZWN0aW9ucy5IYXNodGFibGU8L1Q+PFQ+U3lzdGVtLk9iamVjdDwvVD48L1ROPjxEQ1Q+PEVuPjxJMzIgTj0iS2V5Ij45PC9JMzI+PE9iaiBOPSJWYWx1ZSIgUmVmSWQ9IjkiPjxNUz48UyBOPSJUIj5TeXN0ZW0uU3RyaW5nPC9TPjxTIE49IlYiPldpbmRvd3MgUG93ZXJTaGVsbDwvUz48L01TPjwvT2JqPjwvRW4+PEVuPjxJMzIgTj0iS2V5Ij44PC9JMzI+PE9iaiBOPSJWYWx1ZSIgUmVmSWQ9IjEwIj48TVM+PFMgTj0iVCI+U3lzdGVtLk1hbmFnZW1lbnQuQXV0b21hdGlvbi5Ib3N0LlNpemU8L1M+PE9iaiBOPSJWIiBSZWZJZD0iMTEiPjxNUz48STMyIE49IndpZHRoIj40OTE8L0kzMj48STMyIE49ImhlaWdodCI+MTE0PC9JMzI+PC9NUz48L09iaj48L01TPjwvT2JqPjwvRW4+PEVuPjxJMzIgTj0iS2V5Ij43PC9JMzI+PE9iaiBOPSJWYWx1ZSIgUmVmSWQ9IjEyIj48TVM+PFMgTj0iVCI+U3lzdGVtLk1hbmFnZW1lbnQuQXV0b21hdGlvbi5Ib3N0LlNpemU8L1M+PE9iaiBOPSJWIiBSZWZJZD0iMTMiPjxNUz48STMyIE49IndpZHRoIj4xMjA8L0kzMj48STMyIE49ImhlaWdodCI+MTE0PC9JMzI+PC9NUz48L09iaj48L01TPjwvT2JqPjwvRW4+PEVuPjxJMzIgTj0iS2V5Ij42PC9JMzI+PE9iaiBOPSJWYWx1ZSIgUmVmSWQ9IjE0Ij48TVM+PFMgTj0iVCI+U3lzdGVtLk1hbmFnZW1lbnQuQXV0b21hdGlvbi5Ib3N0LlNpemU8L1M+PE9iaiBOPSJWIiBSZWZJZD0iMTUiPjxNUz48STMyIE49IndpZHRoIj4xMjA8L0kzMj48STMyIE49ImhlaWdodCI+NTA8L0kzMj48L01TPjwvT2JqPjwvTVM+PC9PYmo+PC9Fbj48RW4+PEkzMiBOPSJLZXkiPjU8L0kzMj48T2JqIE49IlZhbHVlIiBSZWZJZD0iMTYiPjxNUz48UyBOPSJUIj5TeXN0ZW0uTWFuYWdlbWVudC5BdXRvbWF0aW9uLkhvc3QuU2l6ZTwvUz48T2JqIE49IlYiIFJlZklkPSIxNyI+PE1TPjxJMzIgTj0id2lkdGgiPjEyMDwvSTMyPjxJMzIgTj0iaGVpZ2h0Ij4zMDAwPC9JMzI+PC9NUz48L09iaj48L01TPjwvT2JqPjwvRW4+PEVuPjxJMzIgTj0iS2V5Ij40PC9JMzI+PE9iaiBOPSJWYWx1ZSIgUmVmSWQ9IjE4Ij48TVM+PFMgTj0iVCI+U3lzdGVtLkludDMyPC9TPjxJMzIgTj0iViI+MjU8L0kzMj48L01TPjwvT2JqPjwvRW4+PEVuPjxJMzIgTj0iS2V5Ij4zPC9JMzI+PE9iaiBOPSJWYWx1ZSIgUmVmSWQ9IjE5Ij48TVM+PFMgTj0iVCI+U3lzdGVtLk1hbmFnZW1lbnQuQXV0b21hdGlvbi5Ib3N0LkNvb3JkaW5hdGVzPC9TPjxPYmogTj0iViIgUmVmSWQ9IjIwIj48TVM+PEkzMiBOPSJ4Ij4wPC9JMzI+PEkzMiBOPSJ5Ij4wPC9JMzI+PC9NUz48L09iaj48L01TPjwvT2JqPjwvRW4+PEVuPjxJMzIgTj0iS2V5Ij4yPC9JMzI+PE9iaiBOPSJWYWx1ZSIgUmVmSWQ9IjIxIj48TVM+PFMgTj0iVCI+U3lzdGVtLk1hbmFnZW1lbnQuQXV0b21hdGlvbi5Ib3N0LkNvb3JkaW5hdGVzPC9TPjxPYmogTj0iViIgUmVmSWQ9IjIyIj48TVM+PEkzMiBOPSJ4Ij4wPC9JMzI+PEkzMiBOPSJ5Ij4yMTwvSTMyPjwvTVM+PC9PYmo+PC9NUz48L09iaj48L0VuPjxFbj48STMyIE49IktleSI+MTwvSTMyPjxPYmogTj0iVmFsdWUiIFJlZklkPSIyMyI+PE1TPjxTIE49IlQiPlN5c3RlbS5Db25zb2xlQ29sb3I8L1M+PEkzMiBOPSJWIj41PC9JMzI+PC9NUz48L09iaj48L0VuPjxFbj48STMyIE49IktleSI+MDwvSTMyPjxPYmogTj0iVmFsdWUiIFJlZklkPSIyNCI+PE1TPjxTIE49IlQiPlN5c3RlbS5Db25zb2xlQ29sb3I8L1M+PEkzMiBOPSJWIj42PC9JMzI+PC9NUz48L09iaj48L0VuPjwvRENUPjwvT2JqPjwvTVM+PC9PYmo+PEIgTj0iX2lzSG9zdE51bGwiPmZhbHNlPC9CPjxCIE49Il9pc0hvc3RVSU51bGwiPmZhbHNlPC9CPjxCIE49Il9pc0hvc3RSYXdVSU51bGwiPmZhbHNlPC9CPjxCIE49Il91c2VSdW5zcGFjZUhvc3QiPmZhbHNlPC9CPjwvTVM+PC9PYmo+PC9NUz48L09iaj4=']

        for fragment in fragments:
            open_content = {
                'creationXml': {
                    '@xmlns': 'http://schemas.microsoft.com/powershell',
                    '#text': fragment
                }
            }
            shell_id = str(uuid.uuid4()).upper()
            shell_body = WsmvObject.shell(shell_id=shell_id, input_streams='stdin pr', output_streams='stdout', open_content=open_content, max_envelope_size=self.max_envelope_size)
            option_set = {
                'protocolversion': '2.3'
            }
            res = self.wsmv_protocol.send(WsmvAction.CREATE, WsmvResourceURI.SHELL_POWERSHELL, body=shell_body, option_set=option_set)

        self.runspace_pool_state = PsrpRunspacePoolState.NEGOTIATION_SENT
        receive_body = WsmvObject.receive('stdout')
        option_set = {
            'WSMAN_CMDSHELL_OPTION_KEEPALIVE': 'TRUE'
        }

        selector_set = {
            'ShellId': shell_id
        }

        while self.runspace_pool_state != PsrpRunspacePoolState.OPENED:
            receive_responses = self.wsmv_protocol.send(WsmvAction.RECEIVE, WsmvResourceURI.SHELL_POWERSHELL, receive_body, selector_set, option_set)
            streams = receive_responses['s:Envelope']['s:Body']['rsp:ReceiveResponse']['rsp:Stream']
            messages = []
            if isinstance(streams, list):
                for stream in streams:
                    messages.append(self.defragmenter.defragment_message(stream['#text']))
            else:
                messages.append(self.defragmenter.defragment_message(streams['#text']))

            for message in messages:
                if isinstance(message, Message):
                    message_type = message.message_type
                    if message_type == PsrpMessageType.SESSION_CAPABILITY:
                        self.runspace_pool_state = PsrpRunspacePoolState.NEGOTIATION_SUCCEEDED
                        session_capability = SessionCapability.parse_message_data(message)
                        # Check the PS Version and adjust the max envelope size accordingly
                        if self.wsmv_protocol.max_envelope_size == WsmvConstant.DEFAULT_MAX_ENVELOPE_SIZE:
                            if session_capability.protocol_version > '2.1':
                                self.wsmv_protocol.max_envelope_size = 512000
                            else:
                                self.wsmv_protocol.max_envelope_size = 153600
                    elif message_type == PsrpMessageType.RUNSPACEPOOL_STATE:
                        runspace_state = RunspacePoolState.parse_message_data(message)
                        self.runspace_pool_state = runspace_state.state

        self.runspace_pool_state = PsrpRunspacePoolState.OPENED

        return shell_id

    def run_command(self, command):
        a = ''