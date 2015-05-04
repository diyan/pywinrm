from __future__ import unicode_literals


class WinRMError(Exception):
    """"Generic WinRM error"""
    code = 500


class AuthenticationError(WinRMError):
    """Authorization Error"""
    code = 401


class BasicAuthDisabledError(AuthenticationError):
    message = 'WinRM/HTTP Basic authentication is not enabled on remote host'


class InvalidCredentialsError(AuthenticationError):
    pass