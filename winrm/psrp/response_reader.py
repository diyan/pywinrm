import re

from winrm.contants import PsrpMessageType
from winrm.psrp.messages import PipelineState


class Reader(object):
    def __init__(self):
        self.stdout_buffer = []
        self.output_buffer = []
        self.verbose_buffer = []
        self.debug_buffer = []
        self.error_buffer = []
        self.warning_buffer = []
        self.return_code = 0

        self.state = None

    def parse_receive_response(self, message):
        message_type = message.message_type

        if message_type == PsrpMessageType.PIPELINE_STATE:
            pipeline_state = PipelineState.parse_message_data(message)
            self.state = pipeline_state.state
            if pipeline_state.exception_as_error_record:
                self.return_code = int(self.state)
                self._parse_error_message({"Obj": pipeline_state.exception_as_error_record})

        elif message_type == PsrpMessageType.PIPELINE_OUTPUT:
            output = message.data['S']
            if output:
                self.output_buffer.append(message.data['S'].encode())
                self.stdout_buffer.append(message.data['S'].encode())

        elif message_type == PsrpMessageType.ERROR_RECORD:
            self._parse_error_message(message.data)

        elif message_type == PsrpMessageType.DEBUG_RECORD:
            self.debug_buffer.append(message.data['Obj']['ToString'].encode())

        elif message_type == PsrpMessageType.VERBOSE_RECORD:
            self.verbose_buffer.append(message.data['Obj']['ToString'].encode())

        elif message_type == PsrpMessageType.WARNING_RECORD:
            self.warning_buffer.append(message.data['Obj']['ToString'].encode())

        elif message_type == PsrpMessageType.PIPELINE_HOST_CALL:
            self._parse_host_call(message.data)
            self._set_return_code(message.data)

    def _parse_host_call(self, message_data):
        raw_output = message_data['Obj']['MS']['Obj']
        full_output = b''
        method_identifier = get_value_of_attribute(raw_output, 'N', 'mi', 'ToString')

        output_list = get_value_of_attribute(raw_output, 'N', 'mp', 'LST')
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

        self.stdout_buffer.append(full_output)

    def _set_return_code(self, message_data):
        raw_output = message_data['Obj']['MS']['Obj']
        method_identifier = get_value_of_attribute(raw_output, 'N', 'mi', 'ToString')
        if method_identifier == 'SetShouldExit':
            return_code = get_value_of_attribute(raw_output, 'N', 'mp', 'LST').get('I32', None)
            if return_code:
                self.return_code = int(return_code)

    def _parse_error_message(self, message_data):
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

        self.error_buffer.append(error_string.encode())


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
    for node in root:
        key = node['@%s' % attribute_key]
        if key == attribute_value:
            if element_value:
                value = node.get(element_value, None)
            else:
                value = node
            break
    return value