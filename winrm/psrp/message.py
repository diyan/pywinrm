import xmltodict


from winrm.psrp.property_types import Version

class MessageBase(object):
    """
    [MS-PSRP] v16.0 2016-07-14
    2 Messages

    This is the base message structure used by the various messages involved
    with PSRP.
    """
