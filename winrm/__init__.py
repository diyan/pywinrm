import re
import base64
import xml.etree.ElementTree as ET

from winrm.protocol import Protocol


class Response(object):
    """Response from a remote command execution"""
    def __init__(self, args):
        self.std_out, self.std_err, self.status_code = args

    def __repr__(self):
        # TODO put tree dots at the end if out/err was truncated
        return '<Response code {0}, out "{1}", err "{2}">'.format(
            self.status_code, self.std_out[:20], self.std_err[:20])


class Session(object):
    # TODO implement context manager methods
    def __init__(self, target, auth, transport='plaintext'):
        username, password = auth
        self.url = self._build_url(target, transport)
        self.protocol = Protocol(self.url, transport=transport,
                                 username=username, password=password)

    def run_cmd(self, command, args=()):
        # TODO optimize perf. Do not call open/close shell every time
        shell_id = self.protocol.open_shell()
        command_id = self.protocol.run_command(shell_id, command, args)
        rs = Response(self.protocol.get_command_output(shell_id, command_id))
        self.protocol.cleanup_command(shell_id, command_id)
        self.protocol.close_shell(shell_id)
        return rs

    def run_ps_long(self, script):
        """base64 encodes a Powershell script and executes the powershell
        encoded script command
        """

        shell_id = self.protocol.open_shell()

        def run_command(command):
            command_id = self.protocol.run_command(shell_id, command)
            rs = Response(self.protocol.get_command_output(shell_id, command_id))
            self.protocol.cleanup_command(shell_id, command_id)

            # Powershell errors are returned in XML, clean them up
            if len(rs.std_err):
                rs.std_err = self.clean_error_msg(rs.std_err)
            return rs

        def make_ps_command(ps_script):
            return ("powershell -encodedcommand %s"
                        % base64.b64encode(ps_script.encode("utf_16_le")))

        def run_and_check_ps(command, stage_message):
            rs = run_command(command)
            if len(rs.std_err) or rs.status_code != 0:
                self.protocol.close_shell(shell_id)
                raise Exception("%s\n%s" % (stage_message, rs.std_err))
            return rs.std_out

        # Get the name of a temp file
        cmd = ("$script_file = [IO.Path]::GetTempFileName() | "
                    " Rename-Item -NewName { $_ -replace 'tmp$', 'tmp.ps1' } -PassThru\n"
               '"$script_file"')
        script_file = run_and_check_ps(make_ps_command(cmd), "Creating temp script file")
        script_file = script_file.strip()

        # Append the data to the file
        base64_script = base64.b64encode(script)
        chunk_size = 2000
        for chunk_index in range(0, len(base64_script), chunk_size):
            chunk = base64_script[chunk_index:chunk_index + chunk_size]
            cmd ='ECHO %s %s "%s" ' % (chunk,
                                    ('>>' if chunk_index else '>'),
                                    script_file)
            run_and_check_ps(cmd, "writing chunk %s to temp script file" % chunk_index)

        # Execute the powershell script
        cmd = '''
            # Convert it from b64 encoded
            $b64 = get-content "%(script_file)s"
            [System.Text.Encoding]::ASCII.GetString([System.Convert]::FromBase64String($b64)) |
                out-file -Encoding Default "%(script_file)s"
        ''' % {'script_file':script_file}
        run_and_check_ps(make_ps_command(cmd),
                         "Converting temp script file back from b64 encoding")

        cmd = ("""PowerShell.exe -ExecutionPolicy Bypass -Command "& '%s' " """
                    % script_file)
        rs = run_command(cmd)

        # Finally, cleanup the temp file
        cmd = "remove-item '%s' " % script_file
        run_and_check_ps(make_ps_command(cmd), "Deleting temp script file")

        self.protocol.close_shell(shell_id)

        return rs


    def run_ps(self, script):
        # Get a temp powershell file name

        # TODO optimize perf. Do not call open/close shell every time
        shell_id = self.protocol.open_shell()

        base64_script = base64.b64encode(script.encode("utf_16_le"))

        # There is an issue with powershell scripts over 2k or 8k (platform dependent)
        # You can not have a command line + argument longer than this
        if len(base64_script) > 2000:
            return self.run_ps_long(script)

        # must use utf16 little endian on windows
        rs = self.run_cmd("powershell -encodedcommand %s" % (base64_script))
        if len(rs.std_err):
            # Clean it it up and make it human readable
            rs.std_err = self.clean_error_msg(rs.std_err)
        return rs


    def clean_error_msg(self, msg):
        """converts a Powershell CLIXML message to a more human readable string
        """

        # if the msg does not start with this, return it as is
        if msg.startswith("#< CLIXML\r\n"):
            # for proper xml, we need to remove the CLIXML part
            # (the first line)
            msg_xml = msg[11:]
            try:
                # remove the namespaces from the xml for easier processing
                msg_xml = self.strip_namespace(msg_xml)
                root = ET.fromstring(msg_xml)
                # the S node is the error message, find all S nodes
                nodes = root.findall("./S")
                new_msg = ""
                for s in nodes:
                    # append error msg string to result, also
                    # the hex chars represent CRLF so we replace with newline
                    new_msg += s.text.replace("_x000D__x000A_", "\n")
            except Exception as e:
                # if any of the above fails, the msg was not true xml
                # print a warning and return the orignal string
                print("Warning: there was a problem converting the Powershell"
                      " error message: %s" % (e))
            else:
                # if new_msg was populated, that's our error message
                # otherwise the original error message will be used
                if len(new_msg):
                    # remove leading and trailing whitespace while we are here
                    msg = new_msg.strip()
        return msg

    def strip_namespace(self, xml):
        """strips any namespaces from an xml string"""
        try:
            p = re.compile("xmlns=*[\"\"][^\"\"]*[\"\"]")
            allmatches = p.finditer(xml)
            for match in allmatches:
                xml = xml.replace(match.group(), "")
            return xml
        except Exception as e:
            raise Exception(e)

    @staticmethod
    def _build_url(target, transport):
        match = re.match(
            '(?i)^((?P<scheme>http[s]?)://)?(?P<host>[0-9a-z-_.]+)(:(?P<port>\d+))?(?P<path>(/)?(wsman)?)?', target)  # NOQA
        scheme = match.group('scheme')
        if not scheme:
            # TODO do we have anything other than HTTP/HTTPS
            scheme = 'https' if transport == 'ssl' else 'http'
        host = match.group('host')
        port = match.group('port')
        if not port:
            port = 5986 if transport == 'ssl' else 5985
        path = match.group('path')
        if not path:
            path = 'wsman'
        return '{0}://{1}:{2}/{3}'.format(scheme, host, port, path.lstrip('/'))
