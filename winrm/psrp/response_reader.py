import re

from winrm.contants import PsrpMessageType
from winrm.psrp.messages import PipelineState


class Reader(object):
    def __init__(self):
        """
        Takes in ReceiveResponse messages from the server and extracts each
        output stream and state information from the pipeline command. More
        info on how streams work and what they should contain can be found here
        https://blogs.technet.microsoft.com/heyscriptingguy/2015/07/04/weekend-scripter-welcome-to-the-powershell-information-stream/

        Attributes:
            stdout: The output to the host program, as set by the command run. Does not include the error stream
            stderr: A copy of the error stream, used to show error messages in the execution
            output: The output stream (1) in Powershell
            error: The error stream (2) in Powershell
            warning: The warning stream (3) in Powershell
            verbose: The verbose stream (4) in Powershell
            debug: The debug stream (5) in Powershell
            information: A list of entries sent in the information stream (6) in Powershell. This
                was added in Powershell v5.0. Each list entry contains the following attributes;
                    computer: The computer that generated this informational record
                    message_data: The message data for this informational record
                    source: The source of this information record (script path, function name, etc.)
                    tags: A list of tags associated with this information record (if any)
                    time_generated: The time this informational record was generated
                    user: The user that generated this informational record
            return_code: The return code of the script, if no return code set this will be 0 by default
        """
        self.stdout = b''
        self.stderr = b''
        self.output = b''
        self.error = b''
        self.warning = b''
        self.verbose = b''
        self.debug = b''
        self.information = []
        self.return_code = 0

    def parse_receive_response(self, message):
        """
        Will take in the ReceiveResponse message from the server and populate
        each powershell stream and return information for later use.

        :param message: A ReceiveResponse message from the server
        :return: The returned state of the pipeline from the receive response
        """
        state = None
        message_type = message.message_type

        if message_type == PsrpMessageType.PIPELINE_STATE:
            pipeline_state = PipelineState.parse_message_data(message)
            state = pipeline_state.state
            if pipeline_state.exception_as_error_record:
                self.return_code = int(state)
                self._parse_error_message({"Obj": pipeline_state.exception_as_error_record})

        elif message_type == PsrpMessageType.PIPELINE_OUTPUT:
            output = message.data['S']
            if output:
                self.output += message.data['S'].encode() + b"\n"
                self.stdout += message.data['S'].encode() + b"\n"

        elif message_type == PsrpMessageType.ERROR_RECORD:
            self._parse_error_message(message.data)

        elif message_type == PsrpMessageType.DEBUG_RECORD:
            self.debug += message.data['Obj']['ToString'].encode() + b"\n"

        elif message_type == PsrpMessageType.VERBOSE_RECORD:
            self.verbose += message.data['Obj']['ToString'].encode() + b"\n"

        elif message_type == PsrpMessageType.WARNING_RECORD:
            self.warning += message.data['Obj']['ToString'].encode() + b"\n"

        elif message_type == PsrpMessageType.INFORMATION_RECORD:
            self._parse_information_stream(message.data)

        elif message_type == PsrpMessageType.PIPELINE_HOST_CALL:
            self._parse_host_call(message.data)
            self._set_return_code(message.data)

        return state

    def _parse_host_call(self, message_data):
        """
        Parses a pipeline host call and gets the standard output

        :param message_data: The PipelineHostCall stream
        """
        raw_output = message_data['Obj']['MS']['Obj']
        full_output = b''
        method_identifier = self.get_value_of_attribute(raw_output, 'N', 'mi', 'ToString')

        output_list = self.get_value_of_attribute(raw_output, 'N', 'mp', 'LST')
        if isinstance(output_list, dict):
            output_list = [output_list]

        if method_identifier != 'SetShouldExit' and method_identifier != 'WriteProgress':
            for output in output_list:
                full_output += output['S'].encode()

        if method_identifier == 'WriteDebugLine':
            full_output = b'DEBUG: %s' % full_output
        elif method_identifier == 'WriteWarningLine':
            full_output = b'WARNING: %s' % full_output
        elif method_identifier == 'WriteVerboseLine':
            full_output = b'VERBOSE: %s' % full_output

        self.stdout += full_output + b"\n"

    def _parse_information_stream(self, message_data):
        """
        Parses the information record stream and extracts the metadata for
        the information record as well as the record itself

        :param message_data: The InformationRecord stream
        """
        raw_output = message_data['Obj']['MS']
        raw_tags = self.get_value_of_attribute(raw_output['Obj'], 'N', 'Tags', 'LST')
        tags = []
        if raw_tags is not None:
            tags = raw_tags['S']
            if isinstance(tags, str):
                tags = [tags]

        time_generated = self.get_value_of_attribute(raw_output['DT'], 'N', 'TimeGenerated', '#text')
        message_data = self.get_value_of_attribute(raw_output['S'], 'N', 'MessageData', '#text')
        source = self.get_value_of_attribute(raw_output['S'], 'N', 'Source', '#text')
        user = self.get_value_of_attribute(raw_output['S'], 'N', 'User', '#text')
        computer = self.get_value_of_attribute(raw_output['S'], 'N', 'Computer', '#text')

        if message_data is None:
            message_data = self.get_value_of_attribute(raw_output['Obj'], 'N', 'MessageData').get('ToString', '')

        information_record = {
            'tags': tags,
            'time_generated': time_generated,
            'message_data': message_data,
            'source': source,
            'user': user,
            'computer': computer,
        }
        self.information.append(information_record)

    def _set_return_code(self, message_data):
        """
        Searches the pipeline host call stream to see if the exit code has
        been set.

        :param message_data: The PipelineHostCall stream
        """
        raw_output = message_data['Obj']['MS']['Obj']
        method_identifier = self.get_value_of_attribute(raw_output, 'N', 'mi', 'ToString')
        if method_identifier == 'SetShouldExit':
            return_code = self.get_value_of_attribute(raw_output, 'N', 'mp', 'LST').get('I32', None)
            if return_code:
                self.return_code = int(return_code)

    def _parse_error_message(self, message_data):
        """
        Parse an error message stream and convert it to a human readable
        format that is like what you see in Powershell

        :param message_data: The raw error data stream
        """
        error_message = message_data['Obj']['ToString']

        error_info = message_data['Obj']['MS']['S']
        fq_error_id = self.get_value_of_attribute(error_info, 'N', 'FullyQualifiedErrorId', '#text')
        error_category_message = self.get_value_of_attribute(error_info, 'N', 'ErrorCategory_Message', '#text')

        invocation_info = self.get_value_of_attribute(message_data['Obj']['MS']['Obj'], 'N', 'InvocationInfo')
        position_message = self.get_value_of_attribute(invocation_info['Props']['S'], 'N', 'PositionMessage', '#text')
        my_command = self.get_value_of_attribute(invocation_info['Props']['S'], 'N', 'MyCommand', '#text')

        error_string = "%s\n" % error_message

        if position_message:
            error_string += "%s\n" % position_message

        if my_command:
            error_string = "%s : %s" % (my_command, error_string)

        error_string += "   + CategoryInfo          : %s\n" \
                        "   + FullyQualifiedErrorId : %s" % (error_category_message, fq_error_id)


        pattern = '_x([0-9A-F]*)_'
        hex_strings = re.findall(pattern, error_string, re.I)
        for hex_string in hex_strings:
            error_string = error_string.replace("_x%s_" % hex_string, chr(int(hex_string, 16)))

        self.stderr += error_string.encode() + b"\n"
        self.error += error_string.encode() + b"\n"

    @staticmethod
    def get_value_of_attribute(root, attribute_key, attribute_value, element_value=None):
        """
        Helper method to search through a list of elements in an xml node and
        retrieve the element with the attribute specified. If no values are
        found None is returned instead

        :param root: The xml root to search in
        :param attribute_key: The attribute key to search for the value
        :param attribute_value: The value of the attribute based on the attribute_key
        :param element_value: If set will return the value of the element found
        :return:
        """
        value = None
        if isinstance(root, dict):
            root = [root]
        for node in root:
            key = node['@%s' % attribute_key]
            if key == attribute_value:
                if element_value:
                    value = node.get(element_value, None)
                else:
                    value = node
                break
        return value
