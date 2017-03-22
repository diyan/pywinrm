from winrm.client import convert_seconds_to_iso8601_duration


class WsmvObject(object):
    @staticmethod
    def command_line(command, arguments, command_id=None):
        """
        [MS-WSMV] v30.0 2017-07-14
        2.2.4.7 CommandLine

        This type describes the strucutre of the command line and its
        arguments. It is used as the body element of the Command message.

        :param command: Contains the name of the command to be executed without any arguments.
        :param arguments: Supply if one or more arguments are required
        :param command_id: If set will add the command id to the message
        :return: dict used when converting to xml
        """
        command_line = {
            'rsp:CommandLine': {
                'rsp:Command': command,
                'rsp:Arguments': arguments
            }
        }
        if command_id:
            command_line['rsp:CommandLine']['@CommandId'] = command_id

        return command_line

    @staticmethod
    def receive(desired_stream, command_id=None):
        """
        [MS-WSMV] v30.0 2017-07-14
        2.2.4.26 Receive

        Describes the output data blocks received from the server.

        :param command_id: The ID of the command to get the output for
        :param arguments: The desired stream to get the output for
        :return: dict used when converting to xml
        """
        receive = {
            'rsp:Receive': {
                'rsp:DesiredStream': {
                    '#text': desired_stream
                }
            }
        }
        if command_id:
            receive['rsp:Receive']['rsp:DesiredStream']['@CommandId'] = command_id

        return receive

    @staticmethod
    def send(stream_name, stream, command_id=None, end=False):
        """
        [MS-WSMV] v30.0 2017-07-14
        2.2.4.32 Send

        Describes the input data blocks sent to the server

        :param stream_name: The stream name, e.g. stdin or pr
        :param command_id: The CommandID that the send relates to
        :param stream: The value of the stream to send to the server
        :return: dict used when converting to xml
        """
        send = {
            'rsp:Send': {
                'rsp:Stream': {
                    '@Name': stream_name,
                    '#text': stream
                }
            }
        }
        if command_id:
            send['rsp:Send']['rsp:Stream']['@CommandId'] = command_id

        if end:
            send['rsp:Send']['rsp:Stream']['@End'] = 'true'

        return send

    @staticmethod
    def shell(**kwargs):
        """
        [MS-WSMV] v30.0 2017-07-14
        2.2.4.37 Shell

        The Shell data type is used in multiple messages.
        wst:Create - defines info required to initialize the targeted Shell
        wst:CreateResponse - properties of the created Shell instance
        wst:GetResponse - properties of an existing Shell instance

        See page 52 of MS-WSMV for more details on the parameters and structure

        :param kwargs: A dictionary used to setup a Shell object
            shell_id: Used in PSRP messages to set the Shell ID when creating the shell
            environment: A dict of environment variables to set when creating the shell
            working_directory: The working directory of the shell
            lifetime: Configures the maximum time, that the Remote Shell will stay open
            idle_time_out: The service SHOULD close and terminate the shell instance if it is idle for this much time
            input_streams: A simple token list of all input streams that are used in the execution
            output_stream: See input_streams but a list of all output streams
            open_content: Additional values that come under the Open Content model of the message, used in PSRP
        :return: dict used when converting to xml
        """
        shell_id = kwargs.get('shell_id', None)
        environment = kwargs.get('environment', None)
        working_directory = kwargs.get('working_directory', None)
        lifetime = kwargs.get('lifetime', None)
        idle_time_out = kwargs.get('idle_time_out', None)
        input_streams = kwargs.get('input_streams', 'stdin')
        output_streams = kwargs.get('output_streams', 'stdout stderr')
        open_content = kwargs.get('open_content', None) # Used in MS-PSRP

        # Create basic object
        shell = {
            'rsp:Shell': {
                'rsp:InputStreams': input_streams,
                'rsp:OutputStreams': output_streams
            }
        }

        # Append optional values if they are set
        if shell_id:
            shell['rsp:Shell']['@ShellId'] = str(shell_id).upper()

        if environment:
            environment_list = []
            for key, value in environment.items():
                environment_list.append({'@Name': key, '#text': value})
            shell['rsp:Shell']['rsp:Environment'] = {'rsp:Variable': environment_list}

        if working_directory:
            shell['rsp:Shell']['rsp:WorkingDirectory'] = working_directory

        if lifetime:
            shell['rsp:Shell']['rsp:Lifetime'] = convert_seconds_to_iso8601_duration(lifetime)

        if idle_time_out:
            shell['rsp:Shell']['rsp:IdleTimeOut'] = convert_seconds_to_iso8601_duration(idle_time_out)

        # Open content can be anything outside the normal structure.
        if open_content:
            for key in open_content.keys():
                shell['rsp:Shell'][key] = open_content[key]

        return shell

    @staticmethod
    def signal(signal_code, command_id=None):
        """
        [MS-WSMV] v30.0 2017-07-14
        2.2.4.38 Signal

        Describes the signal values that are used to control the execution of
        the specific commands or of the Shell processor itself.

        :param signal_code: The signal code to send, see contants.Signals
        :param command_id: If the signal is targeted to a command specify the id otherwise will target the shell
        :return: dict used when converting to xml
        """
        signal = {
            'rsp:Signal': {
                'rsp:Code': signal_code
            }
        }

        if command_id:
            signal['rsp:Signal']['@CommandId'] = command_id

        return signal
