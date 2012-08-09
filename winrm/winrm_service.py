# Test how in-place editor works on GitHub
from datetime import timedelta
from http.transport import HttpPlaintext
from isodate.isoduration import duration_isoformat

class WinRMWebService(object):
    """
    This is the main class that does the SOAP request/response logic. There are a few helper classes, but pretty
    much everything comes through here first.
    """
    def set_timeout(self, seconds):
        """
        Operation timeout, see http://msdn.microsoft.com/en-us/library/ee916629(v=PROT.13).aspx
        @type  seconds: number
        @param seconds: the number of seconds to set the timeout to. It will be converted to an ISO8601 format.
        """
        # in Ruby library there is an alias - op_timeout method
        return duration_isoformat(timedelta(seconds))

endpoint = ''
transport = HttpPlaintext(endpoint)