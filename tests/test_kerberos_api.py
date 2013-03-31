from cffi import FFI

ffi = FFI()
ffi.cdef("""
/// Comments with three slashes means commented out for now, does not required yet

// gssapi.h

// The following type must be defined as the smallest natural unsigned integer
// supported by the platform that has at least 32 bits of precision.

typedef uint32_t gss_uint32;
typedef int32_t gss_int32;

typedef gss_uint32 OM_uint32;

typedef struct gss_OID_desc_struct {
    OM_uint32 length;
    void *elements;
} gss_OID_desc, *gss_OID;

typedef struct gss_OID_set_desc_struct  {
    size_t  count;
    gss_OID elements;
} gss_OID_set_desc, *gss_OID_set;

typedef struct gss_buffer_desc_struct {
    size_t length;
    void *value;
} gss_buffer_desc, *gss_buffer_t;

typedef struct gss_channel_bindings_struct {
    OM_uint32 initiator_addrtype;
    gss_buffer_desc initiator_address;
    OM_uint32 acceptor_addrtype;
    gss_buffer_desc acceptor_address;
    gss_buffer_desc application_data;
} *gss_channel_bindings_t;


struct gss_name_struct;
typedef struct gss_name_struct *gss_name_t;

struct gss_cred_id_struct;
typedef struct gss_cred_id_struct * gss_cred_id_t;

typedef int gss_cred_usage_t;

struct gss_ctx_id_struct;
typedef struct gss_ctx_id_struct * gss_ctx_id_t;

// Credential usage options
#define GSS_C_BOTH ...
#define GSS_C_INITIATE ...
#define GSS_C_ACCEPT ...


// Status code types for gss_display_status
#define GSS_C_GSS_CODE  ...
#define GSS_C_MECH_CODE ...

// Various Null values.

#define GSS_C_NO_NAME ...
#define GSS_C_NO_BUFFER ...
#define GSS_C_NO_OID ...
#define GSS_C_NO_OID_SET ...
#define GSS_C_NO_CONTEXT ...
#define GSS_C_NO_CREDENTIAL ...
#define GSS_C_NO_CHANNEL_BINDINGS ...

// FIXME: CFFI failed to process following declaration
// #define GSS_C_EMPTY_BUFFER {0, NULL}
// #define GSS_C_EMPTY_BUFFER ...

// Some alternate names for a couple of the above values.  These are defined
// for V1 compatibility.

#define GSS_C_NULL_OID ...
#define GSS_C_NULL_OID_SET ...

// Define the default Quality of Protection for per-message services.  Note
// that an implementation that offers multiple levels of QOP may either reserve
// a value (for example zero, as assumed here) to mean "default protection", or
// alternatively may simply equate GSS_C_QOP_DEFAULT to a specific explicit
// QOP value.  However a value of 0 should always be interpreted by a GSSAPI
// implementation as a request for the default protection level.
#define GSS_C_QOP_DEFAULT ...

// Expiration time of 2^32-1 seconds means infinite lifetime for a
// credential or security context
#define GSS_C_INDEFINITE ...

// Finally, function prototypes for the GSSAPI routines.

// TODO: Investigate how to process Windows DLL declarations.
// # define GSS_DLLIMP ...

// Reserved static storage for GSS_oids.

extern gss_OID GSS_C_NT_USER_NAME;

extern gss_OID GSS_C_NT_MACHINE_UID_NAME;

extern gss_OID GSS_C_NT_STRING_UID_NAME;

// This is a deprecated OID value, and
// implementations wishing to support hostbased-service names
// should instead use the GSS_C_NT_HOSTBASED_SERVICE OID,
// defined below, to identify such names;
// GSS_C_NT_HOSTBASED_SERVICE_X should be accepted a synonym
// for GSS_C_NT_HOSTBASED_SERVICE when presented as an input
// parameter, but should not be emitted by GSS-API
// implementations
extern gss_OID GSS_C_NT_HOSTBASED_SERVICE_X;

extern gss_OID GSS_C_NT_HOSTBASED_SERVICE;

extern gss_OID GSS_C_NT_ANONYMOUS;

extern gss_OID GSS_C_NT_EXPORT_NAME;


// Function Prototypes

OM_uint32
gss_acquire_cred(
    OM_uint32 *,        /* minor_status */
    gss_name_t,         /* desired_name */
    OM_uint32,          /* time_req */
    gss_OID_set,        /* desired_mechs */
    gss_cred_usage_t,   /* cred_usage */
    gss_cred_id_t *,    /* output_cred_handle */
    gss_OID_set *,      /* actual_mechs */
    OM_uint32 *);       /* time_rec */

OM_uint32
gss_release_cred(
    OM_uint32 *,        /* minor_status */
    gss_cred_id_t *);   /* cred_handle */

OM_uint32
gss_init_sec_context(
    OM_uint32 *, /* minor_status */
    gss_cred_id_t, /* claimant_cred_handle */
    gss_ctx_id_t *, /* context_handle */
    gss_name_t, /* target_name */
    gss_OID, /* mech_type (used to be const) */
    OM_uint32, /* req_flags */
    OM_uint32, /* time_req */
    gss_channel_bindings_t, /* input_chan_bindings */
    gss_buffer_t, /* input_token */
    gss_OID *, /* actual_mech_type */
    gss_buffer_t, /* output_token */
    OM_uint32 *, /* ret_flags */
    OM_uint32 *); /* time_rec */

OM_uint32
gss_display_status(
    OM_uint32 *,        /* minor_status */
    OM_uint32,          /* status_value */
    int,                /* status_type */
    gss_OID,            /* mech_type (used to be const) */
    OM_uint32 *,        /* message_context */
    gss_buffer_t);      /* status_string */

OM_uint32
gss_display_name(
    OM_uint32 *,        /* minor_status */
    gss_name_t,         /* input_name */
    gss_buffer_t,       /* output_name_buffer */
    gss_OID *);         /* output_name_type */

OM_uint32
gss_import_name(
    OM_uint32 *,        /* minor_status */
    gss_buffer_t,       /* input_name_buffer */
    gss_OID,            /* input_name_type(used to be const) */
    gss_name_t *);      /* output_name */

OM_uint32
gss_release_name(
    OM_uint32 *,        /* minor_status */
    gss_name_t *);      /* input_name */

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
    #include_dirs=['/usr/include/gssapi'],  # This is not required
    libraries=['gssapi_krb5'])


class GSSInternalError(Exception):
    pass


class GSSError(Exception):
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
        raise GSSInternalError('Failed to get GSS major display status for last API call')
    major_status_str = _gss_buffer_to_str(status_str_buf)

    mech_type = ffi.new('gss_OID', [C.GSS_C_NULL_OID])
    major_status = C.gss_display_status(
        minor_status_p, minor_value, C.GSS_C_MECH_CODE, mech_type,
        message_ctx_p, status_str_buf)
    if major_status != 0:
        raise GSSInternalError('Failed to get GSS minor display status for last API call')
    minor_status_str = _gss_buffer_to_str(status_str_buf)
    # TODO investigate how to de-allocate memory
    raise GSSError((major_status_str, major_value), (minor_status_str, minor_value))


def authenticate_gss_client_init(service, principal):
    if not service:
        raise GSSError('Service was not provided. Please specify service in "service@server-host" format')

    if not principal:
        raise GSSError('Principal was not provided. Please specify principal in "username@realm" format')

    minor_status_p = ffi.new('OM_uint32 *')

    service_buf = _str_to_gss_buffer(service)
    out_server_name_p = ffi.new('gss_name_t *')
    major_status = C.gss_import_name(
        minor_status_p, service_buf,
        ffi.cast('gss_OID', C.GSS_C_NT_HOSTBASED_SERVICE), out_server_name_p)
        #ffi.cast('gss_OID', C.GSS_C_NO_OID), out_server_name_p)
    validate_gss_status(major_status, minor_status_p[0])

    gss_ctx_id_p = ffi.new('gss_ctx_id_t *')
    gss_flags = 0
    input_token = ffi.new('gss_buffer_t')
    output_token = ffi.new('gss_buffer_t')
    major_status = C.gss_init_sec_context(
        minor_status_p, ffi.NULL, gss_ctx_id_p, out_server_name_p[0],
        ffi.cast('gss_OID', C.GSS_C_NO_OID), gss_flags, 0,
        ffi.cast('gss_channel_bindings_t', C.GSS_C_NO_CHANNEL_BINDINGS),
        input_token,
        ffi.cast('gss_OID *', C.GSS_C_NO_OID), output_token, ffi.NULL,
        ffi.new('OM_uint32 *', C.GSS_C_INDEFINITE))
    validate_gss_status(major_status, minor_status_p[0])


# FIXME: Investigate how to pass server name and fix following error
# ('Server not found in Kerberos database', 2529638919))
authenticate_gss_client_init('HTTP@server-host', 'username@realm')