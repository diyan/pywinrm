import base64


class Reader(object):

    def __init__(self):
        """
        Takes in ReceiveResponse messages from the server and extracts the
        stdout, stderr and return code from the command.

        Attributes:
            stdout: The standard output of the command
            stderr: The error output of the command
            return_code: The return code of the command
        """
        self.stdout = b''
        self.stderr = b''
        self.return_code = -1

    def __getitem__(self, item):
        return self.__getattribute__(item)

    def parse_receive_response(self, message):
        receive_response = message['s:Envelope']['s:Body']['rsp:ReceiveResponse']
        try:
            for stream_node in receive_response['rsp:Stream']:
                raw_text = stream_node['#text']
                text = base64.b64decode(raw_text.encode('ascii'))
                if stream_node['@Name'] == 'stdout':
                    self.stdout += text
                elif stream_node['@Name'] == 'stderr':
                    self.stderr += text
        except KeyError:
            pass

        command_state = message['s:Envelope']['s:Body']['rsp:ReceiveResponse']['rsp:CommandState']['@State']
        return_code = message['s:Envelope']['s:Body']['rsp:ReceiveResponse']['rsp:CommandState'].get('rsp:ExitCode',
                                                                                                     None)
        if return_code:
            self.return_code = int(return_code)

        return command_state
