import os
from ctypes import (cdll, Structure, c_size_t, c_void_p,
                    c_uint32, c_char_p, cast, byref)
C = cdll.LoadLibrary('libgssapi_krb5.so')
mech = C.GSS_C_NT_HOSTBASED_SERVICE

# ctypes tutorial - http://python.net/crew/theller/ctypes/tutorial.html

GSS_C_GSS_CODE = 1
GSS_C_MECH_CODE = 2


class gss_OID(Structure):
    """
    typedef uint32_t    gss_uint32;
    typedef gss_uint32  OM_uint32;

    typedef struct gss_OID_desc_struct {
        OM_uint32   length;
        void        *elements;
    } gss_OID_desc, *gss_OID;
    """
    _fields_ = [('length', c_uint32), ('elements', c_void_p)]


class gss_buffer_t(Structure):
    """
    typedef struct gss_buffer_desc_struct {
        size_t  length;
        void    *value;
    } gss_buffer_desc *gss_buffer_t;
    """
    _fields_ = [('length', c_size_t), ('value', c_void_p)]


class gss_name_t(Structure):
    """
    typedef struct gss_name_struct {
      size_t    length;
      char      *value;
      gss_OID   type;
    } gss_name_desc;

    typedef struct gss_name_struct * gss_name_t;
    """
    _fields_ = [('length', c_size_t), ('value', c_char_p), ('type', gss_OID)]


# TODO this does not work
# GSS_C_NT_HOSTBASED_SERVICE = gss_OID(10, cast(c_char_p('\x2a\x86\x48\x86\xf7\x12\x01\x02\x01\x04'), c_void_p))  # NOQA
# GSS_C_NT_HOSTBASED_SERVICE = gss_OID(10, cast(create_string_buffer('\x2a\x86\x48\x86\xf7\x12\x01\x02\x01\x04', 10), c_void_p))  # NOQA

"""
/*
* The implementation must reserve static storage for a
* gss_OID_desc object containing the value
* {10, (void *)"\x2a\x86\x48\x86\xf7\x12"
*              "\x01\x02\x01\x04"}, corresponding to an
* object-identifier value of {iso(1) member-body(2)
* Unites States(840) mit(113554) infosys(1) gssapi(2)
* generic(1) service_name(4)}.  The constant
* GSS_C_NT_HOSTBASED_SERVICE should be initialized
* to point to that gss_OID_desc.
"""


def _str_to_gss_buffer(in_str):
    return gss_buffer_t(len(in_str), cast(c_char_p(in_str), c_void_p))


def _gss_buffer_to_str(gss_buffer):
    raise NotImplementedError()


class GSSInternalError(Exception):
    pass


class GSSError(Exception):
    pass


class CredentialsCacheNotFound(GSSError):
    pass


# TODO find better name
class ServerNotFoundInKerberosDatabase(GSSError):
    pass


class KerberosServerNotFound(GSSError):
    """Usually have following message: Cannot resolve servers for KDC in realm
    'SOME.REALM'"""
    pass


def validate_gss_status(major_value, minor_value):
    if major_value == 0:
        return

    minor_status = c_uint32()
    message_ctx = c_uint32()
    status_str_buf = gss_buffer_t()
    mech_type = gss_OID(0, None)  # ?
    major_status = C.gss_display_status(
        byref(minor_status), major_value, GSS_C_GSS_CODE, mech_type,
        byref(message_ctx), status_str_buf)
    if major_status != 0:
        raise GSSInternalError(
            'Failed to get GSS major display status for last API call')
    raise NotImplementedError()


def authenticate_gss_client_init(service, principal):
    if not service:
        raise GSSError('Service was not provided. Please specify '
                       'service in "service@server-host" format')

    if not principal:
        raise GSSError('Principal was not provided. Please specify '
                       'principal in "username@realm" format')

    minor_status = c_uint32()

    service_buf = _str_to_gss_buffer(service)
    out_server_name = gss_name_t()

    major_status = C.gss_import_name(
        # GSS_C_NT_HOSTBASED_SERVICE,
        byref(minor_status), service_buf, gss_OID(0, None),
        byref(out_server_name))
    validate_gss_status(major_status, minor_status.value)


if __name__ == '__main__':
    krb_service = os.environ.get('WINRM_KRB_SERVICE', 'HTTP@server-host')
    krb_principal = os.environ.get('WINRM_KRB_PRINCIPAL', 'username@realm')

    # FIXME: Investigate how to pass server name and fix following error
    # NOTE cffi helped write binding for both gss_import_name and
    # gss_display_status with some type checks;
    #   while ctypes looks like a walking on mining field
    # __main__.GSSInternalError: Failed to get GSS major display status for
    # last API call
    authenticate_gss_client_init(krb_service, krb_principal)
