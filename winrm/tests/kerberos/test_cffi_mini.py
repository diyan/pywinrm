import os
from cffi import FFI

ffi = FFI()
ffi.cdef("""
// Original source could be found here:
// https://github.com/krb5/krb5/blob/master/src/lib/gssapi/generic/gssapi.hin

typedef uint32_t    gss_uint32;
typedef gss_uint32  OM_uint32;

typedef struct gss_OID_desc_struct {
    OM_uint32   length;
    void        *elements;
} gss_OID_desc, *gss_OID;

typedef struct gss_buffer_desc_struct {
    size_t  length;
    void    *value;
} gss_buffer_desc, *gss_buffer_t;

// TODO investigate why we can not inspect gss_name_t
struct gss_name_struct;
typedef struct gss_name_struct * gss_name_t;

//typedef struct gss_name_struct {
//    size_t    length;
//    char      *value;
//    gss_OID   type;
//} gss_name_desc, *gss_name_t;


struct gss_cred_id_struct;
typedef struct gss_cred_id_struct * gss_cred_id_t;

struct gss_ctx_id_struct;
typedef struct gss_ctx_id_struct * gss_ctx_id_t;

typedef struct gss_channel_bindings_struct {
    OM_uint32 initiator_addrtype;
    gss_buffer_desc initiator_address;
    OM_uint32 acceptor_addrtype;
    gss_buffer_desc acceptor_address;
    gss_buffer_desc application_data;
} *gss_channel_bindings_t;

#define GSS_C_GSS_CODE ...
#define GSS_C_MECH_CODE ...

#define GSS_C_NO_NAME ...
#define GSS_C_NO_BUFFER ...
#define GSS_C_NO_OID ...
#define GSS_C_NO_OID_SET ...
#define GSS_C_NO_CONTEXT ...
#define GSS_C_NO_CREDENTIAL ...
#define GSS_C_NO_CHANNEL_BINDINGS ...

#define GSS_C_NO_OID ...
#define GSS_C_NO_CHANNEL_BINDINGS ...
#define GSS_C_NULL_OID ...
#define GSS_C_INDEFINITE ...

extern gss_OID GSS_C_NT_HOSTBASED_SERVICE;

OM_uint32
gss_import_name(
    OM_uint32 *,        /* minor_status */
    gss_buffer_t,       /* input_name_buffer */
    gss_OID,            /* input_name_type(used to be const) */
    gss_name_t *);      /* output_name */

OM_uint32
gss_init_sec_context(
    OM_uint32 *,        /* minor_status */
    gss_cred_id_t,      /* claimant_cred_handle */
    gss_ctx_id_t *,     /* context_handle */
    gss_name_t,         /* target_name */
    gss_OID,            /* mech_type (used to be const) */
    OM_uint32,          /* req_flags */
    OM_uint32,          /* time_req */
    gss_channel_bindings_t,     /* input_chan_bindings */
    gss_buffer_t,       /* input_token */
    gss_OID *,          /* actual_mech_type */
    gss_buffer_t,       /* output_token */
    OM_uint32 *,        /* ret_flags */
    OM_uint32 *);       /* time_rec */

OM_uint32
gss_display_status(
    OM_uint32 *,        /* minor_status */
    OM_uint32,          /* status_value */
    int,                /* status_type */
    gss_OID,            /* mech_type (used to be const) */
    OM_uint32 *,        /* message_context */
    gss_buffer_t);      /* status_string */

OM_uint32
gss_release_buffer(
    OM_uint32 *,        /* minor_status */
    gss_buffer_t);      /* buffer */
""")

C = ffi.verify(
    """
    #include <gssapi/gssapi.h>
    #include <gssapi/gssapi_generic.h>
    #include <gssapi/gssapi_krb5.h>
    """,
    # include_dirs=['/usr/include/gssapi'],  # This is not required
    libraries=['gssapi_krb5'])


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


def _gss_buffer_to_str(gss_buffer):
    out_str = ffi.string(ffi.cast('char *', gss_buffer.value))
    C.gss_release_buffer(ffi.new('OM_uint32 *'), gss_buffer)
    return out_str


def _str_to_gss_buffer(in_str):
    return ffi.new('gss_buffer_t', [len(in_str), ffi.new('char[]', in_str)])


def validate_gss_status(major_value, minor_value):
    if major_value == 0:
        return

    minor_status_p = ffi.new('OM_uint32 *')
    message_ctx_p = ffi.new('OM_uint32 *')
    status_str_buf = ffi.new('gss_buffer_t')
    mech_type = ffi.new('gss_OID', [C.GSS_C_NO_OID])
    major_status = C.gss_display_status(
        minor_status_p, major_value, C.GSS_C_GSS_CODE, mech_type,
        message_ctx_p, status_str_buf)
    if major_status != 0:
        raise GSSInternalError(
            'Failed to get GSS major display status for last API call')
    major_status_str = _gss_buffer_to_str(status_str_buf)

    mech_type = ffi.new('gss_OID', [C.GSS_C_NULL_OID])
    major_status = C.gss_display_status(
        minor_status_p, minor_value, C.GSS_C_MECH_CODE, mech_type,
        message_ctx_p, status_str_buf)
    if major_status != 0:
        raise GSSInternalError(
            'Failed to get GSS minor display status for last API call')
    minor_status_str = _gss_buffer_to_str(status_str_buf)
    # TODO investigate how to de-allocate memory
    # TODO replace hardcoded integers into constants/flags from cffi
    if major_value == 851968 and minor_value == 2529639107:
        # TODO In addition to minor_value check we need to check that kerberos
        # client is installed.
        raise CredentialsCacheNotFound(
            minor_status_str
            + '. Make sure that Kerberos Linux Client was installed. '
            + 'Run "sudo apt-get install krb5-user" for Debian/Ubuntu Linux.')
    elif major_value == 851968 and minor_value == 2529638919:
        raise ServerNotFoundInKerberosDatabase(minor_status_str)
    elif major_value == 851968 and minor_value == 2529639132:
        raise KerberosServerNotFound(
            minor_status_str
            + '. Make sure that Kerberos Server is reachable over network. '
            + 'Try use ping or telnet tools in order to check that.')
    else:
        # __main__.GSSError: (('An unsupported mechanism was requested', 65536)
        #  ,('Unknown error', 0))
        # __main__.GSSError: (('A required output parameter could not be
        # written', 34078720), ('Unknown error', 0))
        raise GSSError((major_status_str, major_value), (
            minor_status_str, minor_value))


def authenticate_gss_client_init(service, principal):
    if not service:
        raise GSSError('Service was not provided. Please specify '
                       'service in "service@server-host" format')

    if not principal:
        raise GSSError('Principal was not provided. Please specify '
                       'principal in "username@realm" format')

    minor_status_p = ffi.new('OM_uint32 *')

    service_buf = _str_to_gss_buffer(service)
    out_server_name_p = ffi.new('gss_name_t *')
    major_status = C.gss_import_name(
        minor_status_p, service_buf,
        C.GSS_C_NT_HOSTBASED_SERVICE,  # ffi.cast('gss_OID', C.GSS_C_NO_OID),
        out_server_name_p)
    validate_gss_status(major_status, minor_status_p[0])

    # gss_flags = C.GSS_C_MUTUAL_FLAG | C.GSS_C_SEQUENCE_FLAG |
    # C.GSS_C_CONF_FLAG | C.GSS_C_INTEG_FLAG
    gss_flags = 0
    input_token = ffi.new('gss_buffer_t')
    output_token = ffi.new('gss_buffer_t')
    ret_flags = ffi.new('OM_uint32 *')

    major_status = C.gss_init_sec_context(
        minor_status_p, ffi.NULL, ffi.cast(
            'gss_ctx_id_t *', C.GSS_C_NO_CONTEXT), out_server_name_p[0],
        ffi.cast('gss_OID', C.GSS_C_NO_OID),
        gss_flags,
        0,
        # ffi.cast('gss_channel_bindings_t', C.GSS_C_NO_CHANNEL_BINDINGS),
        ffi.NULL,
        input_token,
        # ffi.cast('gss_OID *', C.GSS_C_NO_OID),
        ffi.NULL,
        output_token,
        ret_flags,
        # ffi.cast('OM_uint32 *', C.GSS_C_INDEFINITE))
        ffi.NULL)
    validate_gss_status(major_status, minor_status_p[0])

if __name__ == '__main__':
    krb_service = os.environ.get('WINRM_KRB_SERVICE', 'HTTP@server-host')
    krb_principal = os.environ.get('WINRM_KRB_PRINCIPAL', 'username@realm')

    # FIXME: Investigate how to pass server name and fix following error
    # __main__.GSSError: (('A required output parameter could not be written',
    # 34078720), ('Unknown error', 0))
    authenticate_gss_client_init(krb_service, krb_principal)
