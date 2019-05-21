from __future__ import unicode_literals


class WinRMError(Exception):
    """"Generic WinRM error"""
    code = 500


class WinRMTransportError(Exception):
    """WinRM errors specific to transport-level problems (unexpcted HTTP error codes, etc)"""

    @property
    def protocol(self):
        return self.args[0]

    @property
    def code(self):
        return self.args[1]

    @property
    def message(self):
        return 'Bad HTTP response returned from server. Code {0}'.format(self.code)

    @property
    def response_text(self):
        return self.args[2]

    def __str__(self):
        return self.message


class WinRMOperationTimeoutError(Exception):
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
