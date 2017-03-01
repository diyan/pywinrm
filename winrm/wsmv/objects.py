from winrm.contants import WsmvConstant


class WsmvObject(object):
    @staticmethod
    def command_line(command, arguments):
        """
        [MS-WSMV] v30.0 2017-07-14
        2.2.4.7 CommandLine

        This type describes the strucutre of the command line and its
        arguments. It is used as the body element of the Command message.

        :param command: Contains the name of the command to be executed without any arguments.
        :param arguments: Supply if one or more arguments are required
        :return: dict to use when using xmltodict to convert to a dict
        """
        command_line = {
            'rsp:CommandLine': {
                'rsp:Command': command,
                'rsp:Arguments': arguments
            }
        }

        return command_line

    @staticmethod
    def receive(desired_stream, command_id=None):
        """
        [MS-WSMV] v30.0 2017-07-14
        2.2.4.26 Receive

        Describes the output data blocks received from the server.

        :param command_id: The ID of the command to get the output for
        :param arguments: The desired stream to get the output for
        :return: dict to use when using xmltodict to convert to a dict
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
    def shell(**kwargs):
        """
        [MS-WSMV] v30.0 2017-07-14
        2.2.4.37 Shell

        The Shell data type is used in multiple messages.
        wst:Create - defines info required to initialize the targeted Shell
        wst:CreateResponse - properties of the created Shell instance
        wst:GetResponse - properties of an existing Shell instance

        :param kwargs: A dictionary used to setup a Shell object
        :return: dict to use when using xmltodict to convert to a dict
        """
        shell_id = kwargs.get('shell_id', None)
        name = kwargs.get('name', None)
        owner = kwargs.get('owner', None)
        client_ip = kwargs.get('client_ip', None)
        process_id = kwargs.get('process_id', None)
        environment = kwargs.get('environment', None)
        working_directory = kwargs.get('working_directory', None)
        #TODO lifetime = kwargs.get('lifetime', None)
        idle_time_out = kwargs.get('idle_time_out', None)
        input_streams = kwargs.get('input_streams', 'stdin')
        output_streams = kwargs.get('output_streams', 'stdout stderr')
        max_idle_time_out = kwargs.get('max_idle_time_out', None)
        locale = kwargs.get('locale', WsmvConstant.DEFAULT_LOCALE)
        data_locale = kwargs.get('data_locale', WsmvConstant.DEFAULT_LOCALE)
        #TODO compression_mode = kwargs.get('compression_mode', None)
        profile_loaded = kwargs.get('profile_loaded', True)
        encoding = kwargs.get('encoding', WsmvConstant.DEFAULT_ENCODING)
        #TODO buffer_mode = kwargs.get('buffer_mode', None)
        #TODO state = kwargs.get('state', None)
        shell_run_time = kwargs.get('shell_run_time', None)
        shell_inactivity = kwargs.get('shell_inactivity', None)
        open_content = kwargs.get('open_content', None) # Used in MS-PSRP

        # Create basic object
        shell = {
            'rsp:Shell': {
                'rsp:InputStreams': input_streams,
                'rsp:OutputStreams': output_streams,
                'rsp:Locale': locale,
                'rsp:DataLocale': data_locale
            }
        }

        # Append optional values if they are set
        if shell_id:
            shell['rsp:Shell']['@ShellId'] = str(shell_id).upper()

        if name:
            shell['rsp:Shell']['@Name'] = name

        if owner:
            shell['rsp:Shell']['rsp:Owner'] = owner

        if client_ip:
            shell['rsp:Shell']['rsp:ClientIP'] = client_ip

        if process_id:
            shell['rsp:Shell']['rsp:ProcessId'] = process_id

        if environment:
            environment_list = []
            for key, value in environment.items():
                environment_list.append({'@Name': key, '#text': value})
            shell['rsp:Shell']['rsp:Environment'] = {'Variable': environment_list}

        if working_directory:
            shell['rsp:Shell']['rsp:WorkingDirectory'] = working_directory

        if idle_time_out:
            shell['rsp:Shell']['rsp:IdleTimeOut'] = idle_time_out

        if max_idle_time_out:
            shell['rsp:Shell']['rsp:MaxIdleTimeOut'] = max_idle_time_out

        if profile_loaded:
            shell['rsp:Shell']['rsp:ProfileLoaded'] = profile_loaded

        if encoding:
            shell['rsp:Shell']['rsp:Encoding'] = encoding

        if shell_run_time:
            shell['rsp:Shell']['rsp:ShellRunTime'] = shell_run_time

        if shell_inactivity:
            shell['rsp:Shell']['rsp:ShellInactivity'] = locale

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

        Describes the signal values that are used to control the exeuciton of
        the specific commands or of the Shell processor itself.

        :param signal_code: The signal code to send, see contants.Signals
        :param command_id: If the signal is targeted to a command specify the id otherwisee will target the shell
        :return dict to use when using xmltodict to convert to a dict
        """
        signal = {
            'rsp:Signal': {
                'rsp:Code': signal_code
            }
        }

        if command_id:
            signal['rsp:Signal']['@CommandId'] = command_id

        return signal
