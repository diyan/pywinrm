import re

from winrm.protocol import Protocol


class Response(object):
    """Response from a remote command execution"""
    def __init__(self, args):
        self.std_out, self.std_err, self.status_code = args

    def __repr__(self):
        #TODO put tree dots at the end if out/err was truncated
        return '<Response code {0}, out "{1}", err "{2}">'.format(
            self.status_code, self.std_out[:20], self.std_err[:20])


class Session(object):
    #TODO implement context manager methods
    def __init__(self, target, auth, transport='plaintext'):
        username, password = auth
        self.url = self._build_url(target, transport)
        self.protocol = Protocol(self.url, transport=transport, username=username, password=password)

    def run_cmd(self, command, args=()):
        #TODO optimize perf. Do not call open/close shell every time
        shell_id = self.protocol.open_shell()
        command_id = self.protocol.run_command(shell_id, command, args)
        rs = Response(self.protocol.get_command_output(shell_id, command_id))
        self.protocol.cleanup_command(shell_id, command_id)
        self.protocol.close_shell(shell_id)
        return rs

    @staticmethod
    def _build_url(target, transport):
        match = re.match(
            '(?i)^((?P<scheme>http[s]?)://)?(?P<host>[0-9a-z-_]+)(:(?P<port>\d+))?(?P<path>(/)?(wsman)?)?', target)
        scheme = match.group('scheme')
        if not scheme:
            scheme = 'https' if transport == 'ssl' else 'http'  # TODO do we have anything other than HTTP/HTTPS
        host = match.group('host')
        port = match.group('port')
        if not port:
            port = 5986 if transport == 'ssl' else 5985
        path = match.group('path')
        if not path:
            path = 'wsman'
        return '{0}://{1}:{2}/{3}'.format(scheme, host, port, path.lstrip('/'))