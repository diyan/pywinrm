import re

from winrm.client import get_value_of_attribute
from winrm.contants import PsrpMessageType
from winrm.psrp.message_objects import PipelineState


class Reader(object):
    def __init__(self, input_callback):
        """
        Takes in ReceiveResponse messages from the server and extracts each
        output stream and state information from the pipeline command. More
        info on how streams work and what they should contain can be found here
        https://blogs.technet.microsoft.com/heyscriptingguy/2015/07/04/weekend-scripter-welcome-to-the-powershell-information-stream/

        :param input_callback: The method to run when a PIPELINE_HOST_CALL message return Prompt as the mi

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
        self.input_callback = input_callback

    def __getitem__(self, item):
        return self.__getattribute__(item)

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
        method_identifier = get_value_of_attribute(raw_output, 'N', 'mi', 'ToString')

        output_list = get_value_of_attribute(raw_output, 'N', 'mp', 'LST')
        if isinstance(output_list, dict):
            output_list = [output_list]

        if method_identifier == 'Prompt':
            method_identifier_id = get_value_of_attribute(raw_output, 'N', 'mi', 'I32')
            raw_prompt_info = output_list[0]['Obj']['LST']['Obj']['MS']['S']
            name = get_value_of_attribute(raw_prompt_info, 'N', 'name', '#text')
            self.input_callback(method_identifier_id, name, method_identifier)
        else:
            if method_identifier != 'SetShouldExit' and method_identifier != 'WriteProgress':
                for output in output_list:
                    test = output.get('S', None)
                    if test:
                        full_output += test.encode()

            if method_identifier == 'WriteDebugLine':
                full_output = b'DEBUG: ' + full_output
            elif method_identifier == 'WriteWarningLine':
                full_output = b'WARNING: ' + full_output
            elif method_identifier == 'WriteVerboseLine':
                full_output = b'VERBOSE: ' + full_output

            self.stdout += full_output + b"\n"

    def _parse_information_stream(self, message_data):
        """
        Parses the information record stream and extracts the metadata for
        the information record as well as the record itself

        :param message_data: The InformationRecord stream
        """
        raw_output = message_data['Obj']['MS']
        raw_tags = get_value_of_attribute(raw_output['Obj'], 'N', 'Tags', 'LST')
        tags = []
        if raw_tags is not None:
            tags = raw_tags['S']
            if isinstance(tags, str):
                tags = [tags]

        time_generated = get_value_of_attribute(raw_output['DT'], 'N', 'TimeGenerated', '#text')
        message_data = get_value_of_attribute(raw_output['S'], 'N', 'MessageData', '#text')
        source = get_value_of_attribute(raw_output['S'], 'N', 'Source', '#text')
        user = get_value_of_attribute(raw_output['S'], 'N', 'User', '#text')
        computer = get_value_of_attribute(raw_output['S'], 'N', 'Computer', '#text')

        if message_data is None:
            message_data = get_value_of_attribute(raw_output['Obj'], 'N', 'MessageData').get('ToString', '')

        information_record = {
            'tags': tags,
            'time_generated': time_generated.encode(),
            'message_data': message_data.encode(),
            'source': source.encode(),
            'user': user.encode(),
            'computer': computer.encode(),
        }
        self.information.append(information_record)

    def _set_return_code(self, message_data):
        """
        Searches the pipeline host call stream to see if the exit code has
        been set.

        :param message_data: The PipelineHostCall stream
        """
        raw_output = message_data['Obj']['MS']['Obj']
        method_identifier = get_value_of_attribute(raw_output, 'N', 'mi', 'ToString')
        if method_identifier == 'SetShouldExit':
            return_code = get_value_of_attribute(raw_output, 'N', 'mp', 'LST').get('I32', None)
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
        fq_error_id = get_value_of_attribute(error_info, 'N', 'FullyQualifiedErrorId', '#text')
        error_category_message = get_value_of_attribute(error_info, 'N', 'ErrorCategory_Message', '#text')

        invocation_info = get_value_of_attribute(message_data['Obj']['MS']['Obj'], 'N', 'InvocationInfo')
        position_message = get_value_of_attribute(invocation_info['Props']['S'], 'N', 'PositionMessage', '#text')
        my_command = get_value_of_attribute(invocation_info['Props']['S'], 'N', 'MyCommand', '#text')

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
        # Replace all occurrences of \r\n with just \n
        error_string = error_string.replace('\r\n', '\n')

        self.stderr += error_string.encode() + b"\n"
        self.error += error_string.encode() + b"\n"
