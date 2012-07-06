class WinRMWebServiceError(Exception):
    """Generic WinRM SOAP Error"""
    pass

class WinRMAuthorizationError(Exception):
    """Authorization Error"""
    pass

class WinRMWSManFault(Exception):
    """A Fault returned in the SOAP response. The XML node is a WSManFault"""
    pass

class WinRMHTTPTransportError(Exception):
    """"Bad HTTP Transport"""
    pass
