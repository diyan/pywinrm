import os
from cffi import FFI

ffi = FFI()
ffi.cdef("""
// Original source could be found here:
// https://github.com/krb5/krb5/blob/master/src/lib/gssapi/generic/gssapi.hin

/* -*- mode: c; indent-tabs-mode: nil -*- */
/*
 * Copyright 1993 by OpenVision Technologies, Inc.
 *
 * Permission to use, copy, modify, distribute, and sell this software
 * and its documentation for any purpose is hereby granted without fee,
 * provided that the above copyright notice appears in all copies and
 * that both that copyright notice and this permission notice appear in
 * supporting documentation, and that the name of OpenVision not be used
 * in advertising or publicity pertaining to distribution of the software
 * without specific, written prior permission. OpenVision makes no
 * representations about the suitability of this software for any
 * purpose. It is provided "as is" without express or implied warranty.
 *
 * OPENVISION DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE,
 * INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS, IN NO
 * EVENT SHALL OPENVISION BE LIABLE FOR ANY SPECIAL, INDIRECT OR
 * CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF
 * USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
 * OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
 * PERFORMANCE OF THIS SOFTWARE.
 */


/*
 * $Id$
 */

/*
 * First, define the three platform-dependent pointer types.
 */

struct gss_name_struct;
typedef struct gss_name_struct * gss_name_t;

struct gss_cred_id_struct;
typedef struct gss_cred_id_struct * gss_cred_id_t;

struct gss_ctx_id_struct;
typedef struct gss_ctx_id_struct * gss_ctx_id_t;

/*
 * The following type must be defined as the smallest natural unsigned integer
 * supported by the platform that has at least 32 bits of precision.
 */
typedef uint32_t gss_uint32;
typedef int32_t gss_int32;

// TODO Reference implementation defines gss_OID_desc, *gss_OID using
// using the definition for OM_object identifier.

typedef gss_uint32 OM_uint32;

typedef struct gss_OID_desc_struct {
    OM_uint32 length;
    void *elements;
} gss_OID_desc, *gss_OID;

typedef struct gss_OID_set_desc_struct {
    size_t count;
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

/*
 * For now, define a QOP-type as an OM_uint32 (pending resolution of ongoing
 * discussions).
 */
typedef OM_uint32 gss_qop_t;
typedef int gss_cred_usage_t;

/*
 * Flag bits for context-level services.
 */
#define GSS_C_DELEG_FLAG ...
#define GSS_C_MUTUAL_FLAG ...
#define GSS_C_REPLAY_FLAG ...
#define GSS_C_SEQUENCE_FLAG ...
#define GSS_C_CONF_FLAG ...
#define GSS_C_INTEG_FLAG ...
#define GSS_C_ANON_FLAG ...
#define GSS_C_PROT_READY_FLAG ...
#define GSS_C_TRANS_FLAG ...
#define GSS_C_DELEG_POLICY_FLAG ...

/*
 * Credential usage options
 */
#define GSS_C_BOTH ...
#define GSS_C_INITIATE ...
#define GSS_C_ACCEPT ...

/*
 * Status code types for gss_display_status
 */
#define GSS_C_GSS_CODE ...
#define GSS_C_MECH_CODE ...

/*
 * The constant definitions for channel-bindings address families
 */
#define GSS_C_AF_UNSPEC ...
#define GSS_C_AF_LOCAL ...
#define GSS_C_AF_INET ...
#define GSS_C_AF_IMPLINK ...
#define GSS_C_AF_PUP ...
#define GSS_C_AF_CHAOS ...
#define GSS_C_AF_NS ...
#define GSS_C_AF_NBS ...
#define GSS_C_AF_ECMA ...
#define GSS_C_AF_DATAKIT ...
#define GSS_C_AF_CCITT ...
#define GSS_C_AF_SNA ...
#define GSS_C_AF_DECnet ...
#define GSS_C_AF_DLI ...
#define GSS_C_AF_LAT ...
#define GSS_C_AF_HYLINK ...
#define GSS_C_AF_APPLETALK ...
#define GSS_C_AF_BSC ...
#define GSS_C_AF_DSS ...
#define GSS_C_AF_OSI ...
#define GSS_C_AF_NETBIOS ...
#define GSS_C_AF_X25 ...

#define GSS_C_AF_NULLADDR ...

/*
 * Various Null values.
 */
#define GSS_C_NO_NAME ...
#define GSS_C_NO_BUFFER ...
#define GSS_C_NO_OID ...
#define GSS_C_NO_OID_SET ...
#define GSS_C_NO_CONTEXT ...
#define GSS_C_NO_CREDENTIAL ...
#define GSS_C_NO_CHANNEL_BINDINGS ...
// NOTE: CFFI supports only integer macros, so we declare value as const
// FIXME: Unable to compile declaration below
// static const gss_buffer_t GSS_C_EMPTY_BUFFER;

/*
 * Some alternate names for a couple of the above values. These are defined
 * for V1 compatibility.
 */
#define GSS_C_NULL_OID ...
#define GSS_C_NULL_OID_SET ...

/*
 * Define the default Quality of Protection for per-message services. Note
 * that an implementation that offers multiple levels of QOP may either reserve
 * a value (for example zero, as assumed here) to mean "default protection", or
 * alternatively may simply equate GSS_C_QOP_DEFAULT to a specific explicit
 * QOP value. However a value of 0 should always be interpreted by a GSSAPI
 * implementation as a request for the default protection level.
 */
#define GSS_C_QOP_DEFAULT ...

/*
 * Expiration time of 2^32-1 seconds means infinite lifetime for a
 * credential or security context
 */
#define GSS_C_INDEFINITE ...


/* Major status codes */

#define GSS_S_COMPLETE ...

/*
 * Some "helper" definitions to make the status code macros obvious.
 */
#define GSS_C_CALLING_ERROR_OFFSET ...
#define GSS_C_ROUTINE_ERROR_OFFSET ...
#define GSS_C_SUPPLEMENTARY_OFFSET ...
#define GSS_C_CALLING_ERROR_MASK ...
#define GSS_C_ROUTINE_ERROR_MASK ...
#define GSS_C_SUPPLEMENTARY_MASK ...

/*
 * The macros that test status codes for error conditions. Note that the
 * GSS_ERROR() macro has changed slightly from the V1 GSSAPI so that it now
 * evaluates its argument only once.
 * NOTE: CFFI can not parse calling macros but allows declare them as functions
 */
OM_uint32 GSS_CALLING_ERROR(OM_uint32);
OM_uint32 GSS_ROUTINE_ERROR(OM_uint32);
OM_uint32 GSS_SUPPLEMENTARY_INFO(OM_uint32);
OM_uint32 GSS_ERROR(OM_uint32);

/*
 * Now the actual status code definitions
 */

/*
 * Calling errors:
 */
#define GSS_S_CALL_INACCESSIBLE_READ ...
#define GSS_S_CALL_INACCESSIBLE_WRITE ...
#define GSS_S_CALL_BAD_STRUCTURE ...

/*
 * Routine errors:
 */
#define GSS_S_BAD_MECH ...
#define GSS_S_BAD_NAME ...
#define GSS_S_BAD_NAMETYPE ...
#define GSS_S_BAD_BINDINGS ...
#define GSS_S_BAD_STATUS ...
#define GSS_S_BAD_SIG ...
#define GSS_S_NO_CRED ...
#define GSS_S_NO_CONTEXT ...
#define GSS_S_DEFECTIVE_TOKEN ...
#define GSS_S_DEFECTIVE_CREDENTIAL ...
#define GSS_S_CREDENTIALS_EXPIRED ...
#define GSS_S_CONTEXT_EXPIRED ...
#define GSS_S_FAILURE ...
#define GSS_S_BAD_QOP ...
#define GSS_S_UNAUTHORIZED ...
#define GSS_S_UNAVAILABLE ...
#define GSS_S_DUPLICATE_ELEMENT ...
#define GSS_S_NAME_NOT_MN ...
#define GSS_S_BAD_MECH_ATTR ...

/*
 * Supplementary info bits:
 */
#define GSS_S_CONTINUE_NEEDED ...
#define GSS_S_DUPLICATE_TOKEN ...
#define GSS_S_OLD_TOKEN ...
#define GSS_S_UNSEQ_TOKEN ...
#define GSS_S_GAP_TOKEN ...


/*
 * Finally, function prototypes for the GSSAPI routines.
 */


/* Reserved static storage for GSS_oids. Comments are quotes from RFC 2744.
 *
 * The implementation must reserve static storage for a
 * gss_OID_desc object containing the value
 * {10, (void *)"\x2a\x86\x48\x86\xf7\x12\x01\x02\x01\x01"},
 * corresponding to an object-identifier value of
 * {iso(1) member-body(2) United States(840) mit(113554)
 * infosys(1) gssapi(2) generic(1) user_name(1)}. The constant
 * GSS_C_NT_USER_NAME should be initialized to point
 * to that gss_OID_desc.
 */
extern gss_OID GSS_C_NT_USER_NAME;

/*
 * The implementation must reserve static storage for a
 * gss_OID_desc object containing the value
 * {10, (void *)"\x2a\x86\x48\x86\xf7\x12\x01\x02\x01\x02"},
 * corresponding to an object-identifier value of
 * {iso(1) member-body(2) United States(840) mit(113554)
 * infosys(1) gssapi(2) generic(1) machine_uid_name(2)}.
 * The constant GSS_C_NT_MACHINE_UID_NAME should be
 * initialized to point to that gss_OID_desc.
 */
extern gss_OID GSS_C_NT_MACHINE_UID_NAME;

/*
 * The implementation must reserve static storage for a
 * gss_OID_desc object containing the value
 * {10, (void *)"\x2a\x86\x48\x86\xf7\x12\x01\x02\x01\x03"},
 * corresponding to an object-identifier value of
 * {iso(1) member-body(2) United States(840) mit(113554)
 * infosys(1) gssapi(2) generic(1) string_uid_name(3)}.
 * The constant GSS_C_NT_STRING_UID_NAME should be
 * initialized to point to that gss_OID_desc.
 */
extern gss_OID GSS_C_NT_STRING_UID_NAME;

/*
 * The implementation must reserve static storage for a
 * gss_OID_desc object containing the value
 * {6, (void *)"\x2b\x06\x01\x05\x06\x02"},
 * corresponding to an object-identifier value of
 * {iso(1) org(3) dod(6) internet(1) security(5)
 * nametypes(6) gss-host-based-services(2)). The constant
 * GSS_C_NT_HOSTBASED_SERVICE_X should be initialized to point
 * to that gss_OID_desc. This is a deprecated OID value, and
 * implementations wishing to support hostbased-service names
 * should instead use the GSS_C_NT_HOSTBASED_SERVICE OID,
 * defined below, to identify such names;
 * GSS_C_NT_HOSTBASED_SERVICE_X should be accepted a synonym
 * for GSS_C_NT_HOSTBASED_SERVICE when presented as an input
 * parameter, but should not be emitted by GSS-API
 * implementations
 */
extern gss_OID GSS_C_NT_HOSTBASED_SERVICE_X;

/*
 * The implementation must reserve static storage for a
 * gss_OID_desc object containing the value
 * {10, (void *)"\x2a\x86\x48\x86\xf7\x12"
 * "\x01\x02\x01\x04"}, corresponding to an
 * object-identifier value of {iso(1) member-body(2)
 * Unites States(840) mit(113554) infosys(1) gssapi(2)
 * generic(1) service_name(4)}. The constant
 * GSS_C_NT_HOSTBASED_SERVICE should be initialized
 * to point to that gss_OID_desc.
 */
extern gss_OID GSS_C_NT_HOSTBASED_SERVICE;

/*
 * The implementation must reserve static storage for a
 * gss_OID_desc object containing the value
 * {6, (void *)"\x2b\x06\01\x05\x06\x03"},
 * corresponding to an object identifier value of
 * {1(iso), 3(org), 6(dod), 1(internet), 5(security),
 * 6(nametypes), 3(gss-anonymous-name)}. The constant
 * and GSS_C_NT_ANONYMOUS should be initialized to point
 * to that gss_OID_desc.
 */
extern gss_OID GSS_C_NT_ANONYMOUS;


/*
 * The implementation must reserve static storage for a
 * gss_OID_desc object containing the value
 * {6, (void *)"\x2b\x06\x01\x05\x06\x04"},
 * corresponding to an object-identifier value of
 * {1(iso), 3(org), 6(dod), 1(internet), 5(security),
 * 6(nametypes), 4(gss-api-exported-name)}. The constant
 * GSS_C_NT_EXPORT_NAME should be initialized to point
 * to that gss_OID_desc.
 */
extern gss_OID GSS_C_NT_EXPORT_NAME;

/* Function Prototypes */

OM_uint32
gss_acquire_cred(
    OM_uint32 *, /* minor_status */
    gss_name_t, /* desired_name */
    OM_uint32, /* time_req */
    gss_OID_set, /* desired_mechs */
    gss_cred_usage_t, /* cred_usage */
    gss_cred_id_t *, /* output_cred_handle */
    gss_OID_set *, /* actual_mechs */
    OM_uint32 *); /* time_rec */

OM_uint32
gss_release_cred(
    OM_uint32 *, /* minor_status */
    gss_cred_id_t *); /* cred_handle */

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
gss_accept_sec_context(
    OM_uint32 *, /* minor_status */
    gss_ctx_id_t *, /* context_handle */
    gss_cred_id_t, /* acceptor_cred_handle */
    gss_buffer_t, /* input_token_buffer */
    gss_channel_bindings_t, /* input_chan_bindings */
    gss_name_t *, /* src_name */
    gss_OID *, /* mech_type */
    gss_buffer_t, /* output_token */
    OM_uint32 *, /* ret_flags */
    OM_uint32 *, /* time_rec */
    gss_cred_id_t *); /* delegated_cred_handle */

OM_uint32
gss_process_context_token(
    OM_uint32 *, /* minor_status */
    gss_ctx_id_t, /* context_handle */
    gss_buffer_t); /* token_buffer */


OM_uint32
gss_delete_sec_context(
    OM_uint32 *, /* minor_status */
    gss_ctx_id_t *, /* context_handle */
    gss_buffer_t); /* output_token */


OM_uint32
gss_context_time(
    OM_uint32 *, /* minor_status */
    gss_ctx_id_t, /* context_handle */
    OM_uint32 *); /* time_rec */


/* New for V2 */
OM_uint32
gss_get_mic(
    OM_uint32 *, /* minor_status */
    gss_ctx_id_t, /* context_handle */
    gss_qop_t, /* qop_req */
    gss_buffer_t, /* message_buffer */
    gss_buffer_t); /* message_token */


/* New for V2 */
OM_uint32
gss_verify_mic(OM_uint32 *, /* minor_status */
               gss_ctx_id_t, /* context_handle */
               gss_buffer_t, /* message_buffer */
               gss_buffer_t, /* message_token */
               gss_qop_t * /* qop_state */
);

/* New for V2 */
OM_uint32
gss_wrap(
    OM_uint32 *, /* minor_status */
    gss_ctx_id_t, /* context_handle */
    int, /* conf_req_flag */
    gss_qop_t, /* qop_req */
    gss_buffer_t, /* input_message_buffer */
    int *, /* conf_state */
    gss_buffer_t); /* output_message_buffer */


/* New for V2 */
OM_uint32
gss_unwrap(
    OM_uint32 *, /* minor_status */
    gss_ctx_id_t, /* context_handle */
    gss_buffer_t, /* input_message_buffer */
    gss_buffer_t, /* output_message_buffer */
    int *, /* conf_state */
    gss_qop_t *); /* qop_state */


OM_uint32
gss_display_status(
    OM_uint32 *, /* minor_status */
    OM_uint32, /* status_value */
    int, /* status_type */
    gss_OID, /* mech_type (used to be const) */
    OM_uint32 *, /* message_context */
    gss_buffer_t); /* status_string */


OM_uint32
gss_indicate_mechs(
    OM_uint32 *, /* minor_status */
    gss_OID_set *); /* mech_set */


OM_uint32
gss_compare_name(
    OM_uint32 *, /* minor_status */
    gss_name_t, /* name1 */
    gss_name_t, /* name2 */
    int *); /* name_equal */


OM_uint32
gss_display_name(
    OM_uint32 *, /* minor_status */
    gss_name_t, /* input_name */
    gss_buffer_t, /* output_name_buffer */
    gss_OID *); /* output_name_type */


OM_uint32
gss_import_name(
    OM_uint32 *, /* minor_status */
    gss_buffer_t, /* input_name_buffer */
    gss_OID, /* input_name_type(used to be const) */
    gss_name_t *); /* output_name */

OM_uint32
gss_release_name(
    OM_uint32 *, /* minor_status */
    gss_name_t *); /* input_name */

OM_uint32
gss_release_buffer(
    OM_uint32 *, /* minor_status */
    gss_buffer_t); /* buffer */

OM_uint32
gss_release_oid_set(
    OM_uint32 *, /* minor_status */
    gss_OID_set *); /* set */

OM_uint32
gss_inquire_cred(
    OM_uint32 *, /* minor_status */
    gss_cred_id_t, /* cred_handle */
    gss_name_t *, /* name */
    OM_uint32 *, /* lifetime */
    gss_cred_usage_t *, /* cred_usage */
    gss_OID_set *); /* mechanisms */

/* Last argument new for V2 */
OM_uint32
gss_inquire_context(
    OM_uint32 *, /* minor_status */
    gss_ctx_id_t, /* context_handle */
    gss_name_t *, /* src_name */
    gss_name_t *, /* targ_name */
    OM_uint32 *, /* lifetime_rec */
    gss_OID *, /* mech_type */
    OM_uint32 *, /* ctx_flags */
    int *, /* locally_initiated */
    int *); /* open */

/* New for V2 */
OM_uint32
gss_wrap_size_limit(
    OM_uint32 *, /* minor_status */
    gss_ctx_id_t, /* context_handle */
    int, /* conf_req_flag */
    gss_qop_t, /* qop_req */
    OM_uint32, /* req_output_size */
    OM_uint32 *); /* max_input_size */

/* FIXME: gss_import_name_object, gss_export_name_object declarations
 * was excluded because libgssapi_krb5.so does not export this function
 */

/* New for V2 */
OM_uint32
gss_add_cred(
    OM_uint32 *, /* minor_status */
    gss_cred_id_t, /* input_cred_handle */
    gss_name_t, /* desired_name */
    gss_OID, /* desired_mech */
    gss_cred_usage_t, /* cred_usage */
    OM_uint32, /* initiator_time_req */
    OM_uint32, /* acceptor_time_req */
    gss_cred_id_t *, /* output_cred_handle */
    gss_OID_set *, /* actual_mechs */
    OM_uint32 *, /* initiator_time_rec */
    OM_uint32 *); /* acceptor_time_rec */

/* New for V2 */
OM_uint32
gss_inquire_cred_by_mech(
    OM_uint32 *, /* minor_status */
    gss_cred_id_t, /* cred_handle */
    gss_OID, /* mech_type */
    gss_name_t *, /* name */
    OM_uint32 *, /* initiator_lifetime */
    OM_uint32 *, /* acceptor_lifetime */
    gss_cred_usage_t *); /* cred_usage */

/* New for V2 */
OM_uint32
gss_export_sec_context(
    OM_uint32 *, /* minor_status */
    gss_ctx_id_t *, /* context_handle */
    gss_buffer_t); /* interprocess_token */

/* New for V2 */
OM_uint32
gss_import_sec_context(
    OM_uint32 *, /* minor_status */
    gss_buffer_t, /* interprocess_token */
    gss_ctx_id_t *); /* context_handle */

/* New for V2 */
OM_uint32
gss_release_oid(
    OM_uint32 *, /* minor_status */
    gss_OID *); /* oid */

/* New for V2 */
OM_uint32
gss_create_empty_oid_set(
    OM_uint32 *, /* minor_status */
    gss_OID_set *); /* oid_set */

/* New for V2 */
OM_uint32
gss_add_oid_set_member(
    OM_uint32 *, /* minor_status */
    gss_OID, /* member_oid */
    gss_OID_set *); /* oid_set */

/* New for V2 */
OM_uint32
gss_test_oid_set_member(
    OM_uint32 *, /* minor_status */
    gss_OID, /* member */
    gss_OID_set, /* set */
    int *); /* present */

/* New for V2 */
OM_uint32
gss_str_to_oid(
    OM_uint32 *, /* minor_status */
    gss_buffer_t, /* oid_str */
    gss_OID *); /* oid */

/* New for V2 */
OM_uint32
gss_oid_to_str(
    OM_uint32 *, /* minor_status */
    gss_OID, /* oid */
    gss_buffer_t); /* oid_str */

/* New for V2 */
OM_uint32
gss_inquire_names_for_mech(
    OM_uint32 *, /* minor_status */
    gss_OID, /* mechanism */
    gss_OID_set *); /* name_types */

/* New for V2 */
OM_uint32
gss_inquire_mechs_for_name(
    OM_uint32 *, /* minor_status */
    const gss_name_t, /* input_name */
    gss_OID_set *); /* mech_types */

/*
 * The following routines are obsolete variants of gss_get_mic, gss_wrap,
 * gss_verify_mic and gss_unwrap. They should be provided by GSSAPI V2
 * implementations for backwards compatibility with V1 applications. Distinct
 * entrypoints (as opposed to #defines) should be provided, to allow GSSAPI
 * V1 applications to link against GSSAPI V2 implementations.
 */
OM_uint32
gss_sign(
    OM_uint32 *, /* minor_status */
    gss_ctx_id_t, /* context_handle */
    int, /* qop_req */
    gss_buffer_t, /* message_buffer */
    gss_buffer_t); /* message_token */

OM_uint32
gss_verify(
    OM_uint32 *, /* minor_status */
    gss_ctx_id_t, /* context_handle */
    gss_buffer_t, /* message_buffer */
    gss_buffer_t, /* token_buffer */
    int *); /* qop_state */

OM_uint32
gss_seal(
    OM_uint32 *, /* minor_status */
    gss_ctx_id_t, /* context_handle */
    int, /* conf_req_flag */
    int, /* qop_req */
    gss_buffer_t, /* input_message_buffer */
    int *, /* conf_state */
    gss_buffer_t); /* output_message_buffer */

OM_uint32
gss_unseal(
    OM_uint32 *, /* minor_status */
    gss_ctx_id_t, /* context_handle */
    gss_buffer_t, /* input_message_buffer */
    gss_buffer_t, /* output_message_buffer */
    int *, /* conf_state */
    int *); /* qop_state */

/* New for V2 */
OM_uint32
gss_export_name(
    OM_uint32 *, /* minor_status */
    const gss_name_t, /* input_name */
    gss_buffer_t); /* exported_name */

/* New for V2 */
OM_uint32
gss_duplicate_name(
    OM_uint32 *, /* minor_status */
    const gss_name_t, /* input_name */
    gss_name_t *); /* dest_name */

/* New for V2 */
OM_uint32
gss_canonicalize_name(
    OM_uint32 *, /* minor_status */
    const gss_name_t, /* input_name */
    const gss_OID, /* mech_type */
    gss_name_t *); /* output_name */

/* RFC 4401 */

#define GSS_C_PRF_KEY_FULL ...
#define GSS_C_PRF_KEY_PARTIAL ...

OM_uint32
gss_pseudo_random(
    OM_uint32 *, /* minor_status */
    gss_ctx_id_t, /* context */
    int, /* prf_key */
    const gss_buffer_t, /* prf_in */
    ssize_t, /* desired_output_len */
    gss_buffer_t); /* prf_out */

OM_uint32
gss_store_cred(
    OM_uint32 *, /* minor_status */
    const gss_cred_id_t,/* input_cred_handle */
    gss_cred_usage_t, /* input_usage */
    const gss_OID, /* desired_mech */
    OM_uint32, /* overwrite_cred */
    OM_uint32, /* default_cred */
    gss_OID_set *, /* elements_stored */
    gss_cred_usage_t *);/* cred_usage_stored */

OM_uint32
gss_set_neg_mechs(
    OM_uint32 *, /* minor_status */
    gss_cred_id_t, /* cred_handle */
    const gss_OID_set); /* mech_set */


/* XXXX these are not part of the GSSAPI C bindings! (but should be)
 * NOTE: CFFI can not parse calling macros but allows declare them as functions
 */
OM_uint32 GSS_CALLING_ERROR_FIELD(OM_uint32);
OM_uint32 GSS_ROUTINE_ERROR_FIELD(OM_uint32);
OM_uint32 GSS_SUPPLEMENTARY_INFO_FIELD(OM_uint32);

/* XXXX This is a necessary evil until the spec is fixed */
#define GSS_S_CRED_UNAVAIL ...

/*
 * RFC 5587
 */
typedef const gss_buffer_desc *gss_const_buffer_t;
typedef const struct gss_channel_bindings_struct *gss_const_channel_bindings_t;
typedef const struct gss_ctx_id_struct gss_const_ctx_id_t;
typedef const struct gss_cred_id_struct gss_const_cred_id_t;
typedef const struct gss_name_struct gss_const_name_t;
typedef const gss_OID_desc *gss_const_OID;
typedef const gss_OID_set_desc *gss_const_OID_set;

OM_uint32
gss_indicate_mechs_by_attrs(
    OM_uint32 *, /* minor_status */
    gss_const_OID_set, /* desired_mech_attrs */
    gss_const_OID_set, /* except_mech_attrs */
    gss_const_OID_set, /* critical_mech_attrs */
    gss_OID_set *); /* mechs */

OM_uint32
gss_inquire_attrs_for_mech(
    OM_uint32 *, /* minor_status */
    gss_const_OID, /* mech */
    gss_OID_set *, /* mech_attrs */
    gss_OID_set *); /* known_mech_attrs */

OM_uint32
gss_display_mech_attr(
    OM_uint32 *, /* minor_status */
    gss_const_OID, /* mech_attr */
    gss_buffer_t, /* name */
    gss_buffer_t, /* short_desc */
    gss_buffer_t); /* long_desc */

extern gss_const_OID GSS_C_MA_MECH_CONCRETE;
extern gss_const_OID GSS_C_MA_MECH_PSEUDO;
extern gss_const_OID GSS_C_MA_MECH_COMPOSITE;
extern gss_const_OID GSS_C_MA_MECH_NEGO;
extern gss_const_OID GSS_C_MA_MECH_GLUE;
extern gss_const_OID GSS_C_MA_NOT_MECH;
extern gss_const_OID GSS_C_MA_DEPRECATED;
extern gss_const_OID GSS_C_MA_NOT_DFLT_MECH;
extern gss_const_OID GSS_C_MA_ITOK_FRAMED;
extern gss_const_OID GSS_C_MA_AUTH_INIT;
extern gss_const_OID GSS_C_MA_AUTH_TARG;
extern gss_const_OID GSS_C_MA_AUTH_INIT_INIT;
extern gss_const_OID GSS_C_MA_AUTH_TARG_INIT;
extern gss_const_OID GSS_C_MA_AUTH_INIT_ANON;
extern gss_const_OID GSS_C_MA_AUTH_TARG_ANON;
extern gss_const_OID GSS_C_MA_DELEG_CRED;
extern gss_const_OID GSS_C_MA_INTEG_PROT;
extern gss_const_OID GSS_C_MA_CONF_PROT;
extern gss_const_OID GSS_C_MA_MIC;
extern gss_const_OID GSS_C_MA_WRAP;
extern gss_const_OID GSS_C_MA_PROT_READY;
extern gss_const_OID GSS_C_MA_REPLAY_DET;
extern gss_const_OID GSS_C_MA_OOS_DET;
extern gss_const_OID GSS_C_MA_CBINDINGS;
extern gss_const_OID GSS_C_MA_PFS;
extern gss_const_OID GSS_C_MA_COMPRESS;
extern gss_const_OID GSS_C_MA_CTX_TRANS;

/*
 * RFC 5801
 */
OM_uint32
gss_inquire_saslname_for_mech(
    OM_uint32 *, /* minor_status */
    const gss_OID, /* desired_mech */
    gss_buffer_t, /* sasl_mech_name */
    gss_buffer_t, /* mech_name */
    gss_buffer_t /* mech_description */
);

OM_uint32
gss_inquire_mech_for_saslname(
    OM_uint32 *, /* minor_status */
    const gss_buffer_t, /* sasl_mech_name */
    gss_OID * /* mech_type */
);
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
    assert C.GSS_S_CALL_INACCESSIBLE_READ == 16777216
    assert C.GSS_S_CALL_INACCESSIBLE_WRITE == 33554432
    assert C.GSS_S_CALL_BAD_STRUCTURE == 50331648

    assert C.GSS_S_BAD_MECH == 65536
    assert C.GSS_S_BAD_NAME == 131072
    assert C.GSS_S_BAD_NAMETYPE == 196608
    assert C.GSS_S_BAD_BINDINGS == 262144
    assert C.GSS_S_BAD_STATUS == 327680
    assert C.GSS_S_BAD_SIG == 393216
    assert C.GSS_S_NO_CRED == 458752
    assert C.GSS_S_NO_CONTEXT == 524288
    assert C.GSS_S_DEFECTIVE_TOKEN == 589824

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
        # ,('Unknown error', 0))
        # __main__.GSSError: ((
        #    'A required output parameter could not be written', 34078720),
        # ('Unknown error', 0))
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

    gss_flags = C.GSS_C_MUTUAL_FLAG | C.GSS_C_SEQUENCE_FLAG | \
        C.GSS_C_CONF_FLAG | C.GSS_C_INTEG_FLAG
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
