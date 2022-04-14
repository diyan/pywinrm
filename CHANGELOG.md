# Changelog

### Version 0.4.3
- Fix invalid regex escape sequences.
- Decoding CLIXML failures for `run_ps` will create a `UserWarning` rather than printing the warning.
- Remove usage of deprecated Python API to support Python 3.11

### Version 0.4.2
- Dropped Python 3.5 from support matrix as it is EOL.
- Remove dependency on `distutils` that is deprecated in Python 3.10.

### Version 0.4.1
- HOT FIX: Fixing an issue with `requests_kerberos` not imported correctly from the changes in `0.4.0`.

### Version 0.4.0
- Ensure `server_cert_validation=ignore` supersedes ca_trust_path/env overrides
- Added deprecated warnings if CA trusts defined by environment variables are used.
- Set minimum version of requests-credssp to support Kerberos auth over CredSSP and other changes
- Added `proxy` support where it can be defined within the application, with the ability to specify the proxy within the application
- Fix for shell not setting all environment variables.
- Fix session clixml encoding on Python 3
- `Protocol.close_shell(shell_id)` will now close the session(and TCP connections) to the Windows machine. `close_session` option has been added in case of leaving the session alone.
- Add a function to send input to a running process.

### Version 0.3.0
- Added support for message encryption over HTTP when using NTLM/Kerberos/CredSSP
- Added parameter to disable TLSv1.2 when using CredSSP for Server 2008 support
- Error detail from SOAP fault (if present) is now included with HTTP 500 errors
- Fixed CA path override (incl envvar)
- Fixed Kerberos service override
- Try harder to suppress urllib3 InsecureRequestWarnings on various OSs
- Fixed timeout values to parse correctly if passed as strings
- Various updates to CI/tests

### Version 0.2.2
- Added support for CredSSP authenication (via requests-credssp)
- Improved README, see 'Valid transport options' section
- Run unit tests on Linux / Travis CI on Python 2.6-2.7, 3.3-3.6, PyPy2
- Run integration tests on Windows / AppVeyor on Python 2.7, 3.3-3.5
- Drop support for Python 3.0-3.2 due to lack of explicit unicode literal, see pep-0414
- Drop support for Python 2.6 on Windows
- Add support for Python 3.6-dev on Linux

### Version 0.2.1
- Minor import bugfix for error "'module' object has no attribute 'util'" when using Kerberos delegation on older Python builds

### Version 0.2.0
- Switched core HTTP transport from urllib2 to requests
- Added support for NTLM (via requests_ntlm)
- Added support for kerberos delegation (via requests_kerberos)
- Added support for explicit kerberos principals (in conjuction w/ pykerberos bugfix)
- Timeouts are more configurable

### Version 0.1.1
- Force basic auth header to avoid additional HTTP request and reduce latency
- Python 2.7.9+. Allow server cert validation to be ignored using SSLContext.verify_mode
- Tests. Enable Python 3.4 on Travis CI

### Version 0.0.3

- Use xmltodict instead of not supported xmlwitch
- Add certificate authentication support
- Setup PyPI classifiers
- Fix. Include UUID when sending request
- Fix. Python 2.6.6/CentOS. Use tuples instead of lists in setup.py
- Fix. Python 2.6. String formatting
- Handle unauthorized response and raise UnauthorizeError
- Convert different forms of short urls into full well-formed endpoint
- Add Session.run_ps() helper to execute PowerShell scripts
