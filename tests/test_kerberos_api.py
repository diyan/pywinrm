from cffi import FFI

ffi = FFI()
ffi.cdef("""
/// Comments with three slashes means commented out for now, does not required yet

// gssapi.h

// The following type must be defined as the smallest natural unsigned integer
// supported by the platform that has at least 32 bits of precision.

typedef uint32_t gss_uint32;
/// typedef int32_t gss_int32;

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

/*
struct gss_name_struct {
    size_t length;
    char *value;
    gss_OID type;
};

typedef struct gss_name_desc * gss_name_t;
*/

/* x.c */
struct gss_name_struct;
typedef struct gss_name_struct * gss_name_t;

struct gss_name_struct {
    int x;
    char *y;
};

///struct gss_name_struct; // CFFI requires full struct declaration
///typedef struct gss_name_struct *gss_name_t; // CFFI requires full struct declaration

struct gss_cred_id_struct;
typedef struct gss_cred_id_struct * gss_cred_id_t;

typedef int gss_cred_usage_t;

struct gss_ctx_id_struct;
typedef struct gss_ctx_id_struct * gss_ctx_id_t;

// Credential usage options
///#define GSS_C_BOTH ...
#define GSS_C_INITIATE ...
///#define GSS_C_ACCEPT ...


// Status code types for gss_display_status
#define GSS_C_GSS_CODE  ...
#define GSS_C_MECH_CODE ...

// Various Null values.

#define GSS_C_NO_NAME ...
///#define GSS_C_NO_BUFFER ...
#define GSS_C_NO_OID ...
#define GSS_C_NO_OID_SET ...
///#define GSS_C_NO_CONTEXT ...
///#define GSS_C_NO_CREDENTIAL ...
///#define GSS_C_NO_CHANNEL_BINDINGS ...
///#define GSS_C_EMPTY_BUFFER ... // CompileError: command 'gcc' failed with exit status 1

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
///#define GSS_C_QOP_DEFAULT ...

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
    /// #include <gssapi/gssapi_generic.h>
    /// #include <gssapi/gssapi_krb5.h>
    """,
    #include_dirs=['/usr/include/gssapi'],  # This is not required
    libraries=['gssapi_krb5'])


class GSSInternalError(Exception):
    pass


class GSSError(Exception):
    pass


def validate_gss_status(major_value, minor_value):
    if major_value == 0:
        return

    minor_status_p = ffi.new('OM_uint32 *')
    message_ctx_p = ffi.new('OM_uint32 *')
    status_str_buf = ffi.new('gss_buffer_t')
    mech_type = ffi.new('gss_OID', [C.GSS_C_NO_OID])
    major_status = C.gss_display_status(minor_status_p, major_value,
                                        C.GSS_C_GSS_CODE, mech_type,
                                        message_ctx_p, status_str_buf)
    if major_status != 0:
        raise GSSInternalError('Failed to get GSS major display status for last API call')
    major_status_str = ffi.string(ffi.cast('char *', status_str_buf.value))
    C.gss_release_buffer(minor_status_p, status_str_buf)

    mech_type = ffi.new('gss_OID', [C.GSS_C_NULL_OID])
    major_status = C.gss_display_status(minor_status_p, minor_value,
                                        C.GSS_C_MECH_CODE, mech_type,
                                        message_ctx_p, status_str_buf)
    if major_status != 0:
        raise GSSInternalError('Failed to get GSS minor display status for last API call')
    minor_status_str = ffi.string(ffi.cast('char *', status_str_buf.value))
    C.gss_release_buffer(minor_status_p, status_str_buf)
    # TODO investigate how to de-allocate memory
    raise GSSError((major_status_str, major_value), (minor_status_str, minor_value))


def authenticate_gss_client_init(service, principal):
    if not service:
        raise GSSError('Service was not provided. Please specify service in "service@server-host" format')

    if not principal:
        raise GSSError('Principal was not provided. Please specify principal in "username@realm" format')

    minor_status_p = ffi.new('OM_uint32 *')
    service_buf = ffi.new('gss_buffer_t', [len(service), ffi.new('char[]', service)])
    nt_service_name_type = ffi.new('gss_OID', C.GSS_C_NT_HOSTBASED_SERVICE[0])
    # Investigate how to init gss_name_t * with GSS_C_NO_NAME value
    #output_name_p = ffi.new('gss_name_t *', C.GSS_C_NO_NAME[0])
    #out_server_name_p = ffi.new('gss_name_t', [0, ffi.new('gss_OID', [C.GSS_C_NO_NAME]), ffi.new('char[]', '')])
    out_server_name_p = ffi.new('gss_name_t')

    major_status = C.gss_import_name(minor_status_p, service_buf, nt_service_name_type, out_server_name_p)
    validate_gss_status(major_status, minor_status_p[0])

    principal_buf = ffi.new('gss_buffer_t', [len(principal), ffi.new('char[]', principal)])
    nt_user_name_type = ffi.new('gss_OID', C.GSS_C_NT_USER_NAME[0])
    out_user_name_p = ffi.new('gss_name_t *')
    major_status = C.gss_import_name(minor_status_p, principal_buf, nt_user_name_type, out_user_name_p)
    validate_gss_status(major_status, minor_status_p[0])

    #client_credentials = ffi.new('gss_cred_id_t')
    #major_status = C.gss_acquire_cred(
    #    minor_status_p, out_user_name_p[0], C.GSS_C_INDEFINITE,
    #    C.GSS_C_NO_OID_SET, C.GSS_C_INITIATE, client_credentials, ffi.NULL, ffi.NULL)
    #validate_gss_status(major_status, minor_status_p[0])


authenticate_gss_client_init('HTTP@server-host', 'username@realm')

"""
138	    if (principal && *principal)
139	    {
140	        gss_name_t name;
141	        principal_token.length = strlen(principal);
142	        principal_token.value = (char *)principal;
143
144	        maj_stat = gss_import_name(&min_stat, &principal_token, GSS_C_NT_USER_NAME, &name);
145	        if (GSS_ERROR(maj_stat))
146	        {
147	            set_gss_error(maj_stat, min_stat);
148	            ret = AUTH_GSS_ERROR;
149	            goto end;
150	        }
151
152	        maj_stat = gss_acquire_cred(&min_stat, name, GSS_C_INDEFINITE, GSS_C_NO_OID_SET, GSS_C_INITIATE,
153	                                    &state->client_creds, NULL, NULL);
154	        if (GSS_ERROR(maj_stat))
155	        {
156	            set_gss_error(maj_stat, min_stat);
157	            ret = AUTH_GSS_ERROR;
158	            goto end;
159	        }
160
161	        maj_stat = gss_release_name(&min_stat, &name);
162	        if (GSS_ERROR(maj_stat))
"""