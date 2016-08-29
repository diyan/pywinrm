from __future__ import unicode_literals
import xmltodict


class WinRMError(Exception):
    """"Generic WinRM error"""

    code = 500
    winrm_response = None

    def __init__(self, *args, **kwargs):
        try:
            self.winrm_response = kwargs.pop('winrm_resposne')
        except KeyError:
            pass

        try:
            self.code = kwargs.pop('code')
        except KeyError:
            pass
        super(WinRMError, self).__init__(*args, **kwargs)

    def dict_response(self):
        try:
            return xmltodict.parse(self.winrm_response)
        except xmltodict.expat.ExpatError:
            pass

        return None


class WinRMTransportError(WinRMError):
    """WinRM errors specific to transport-level problems (unexpcted HTTP error codes, etc)"""
    code = 500

class WinRMOperationTimeoutError(WinRMError):
    """
    Raised when a WinRM-level operation timeout (not a connection-level timeout) has occurred. This is
    considered a normal error that should be retried transparently by the client when waiting for output from
    a long-running process.
    """
    code = 500

class AuthenticationError(WinRMError):
    """Authorization Error"""
    code = 401


class BasicAuthDisabledError(AuthenticationError):
    message = 'WinRM/HTTP Basic authentication is not enabled on remote host'


class InvalidCredentialsError(AuthenticationError):
    pass