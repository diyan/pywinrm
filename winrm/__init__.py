import logging
import re
import sys

if sys.version_info[:2] > (2, 6):
    from logging import NullHandler
else:
    from logging import Handler

    class NullHandler(Handler):
        def emit(self, record):
            pass

from winrm.psrp.psrp import PsrpClient
from winrm.wsmv.wsmv import WsmvClient


# Feature support attributes for multi-version clients.
# These values can be easily checked for with hasattr(winrm, "FEATURE_X"),
# "'auth_type' in winrm.FEATURE_SUPPORTED_AUTHTYPES", etc for clients to sniff features
# supported by a particular version of pywinrm
FEATURE_SUPPORTED_AUTHTYPES=['basic', 'certificate', 'ntlm', 'kerberos', 'plaintext', 'ssl', 'credssp']
FEATURE_READ_TIMEOUT=True
FEATURE_OPERATION_TIMEOUT=True
FEATURE_PSRP_CLIENT=True
FEATURE_WSMV_CLIENT=True

logging.getLogger(__name__).addHandler(NullHandler())
#ogging.basicConfig(level=logging.DEBUG)


class Session(object):

    def __init__(self, **transport_opts):
        self.transport_opts = transport_opts
        self.transport_opts['endpoint'] = self._build_url(self.transport_opts['endpoint'])
        if 'auth_method' not in self.transport_opts.keys():
            self.transport_opts['auth_method'] = 'basic'

    def run_cmd(self, command, arguments=()):
        protocol = WsmvClient(self.transport_opts)
        try:
            protocol.open_shell()
            output = protocol.run_command(command, arguments)
        finally:
            protocol.close_shell()

        return output

    def run_ps(self, command, parameters=(), responses=()):
        protocol = PsrpClient(self.transport_opts)
        try:
            protocol.open_shell()
            output = protocol.run_command(command, parameters, responses)
        finally:
            protocol.close_shell()

        return output


    @staticmethod
    def _build_url(target):
        match = re.match(
            '(?i)^((?P<scheme>http[s]?)://)?(?P<host>[0-9a-z-_.]+)(:(?P<port>\d+))?(?P<path>(/)?(wsman)?)?', target)
        scheme = match.group('scheme')
        host = match.group('host')
        port = match.group('port')
        path = match.group('path')

        if not scheme:
            if port:
                if port == '5985':
                    scheme = 'http'
                else:
                    scheme = 'https'
            else:
                scheme = 'https'
        if not port:
            if scheme == 'https':
                port = 5986
            else:
                port = 5985
        if not path:
            path = 'wsman'
        return '{0}://{1}:{2}/{3}'.format(scheme, host, port, path.lstrip('/'))
