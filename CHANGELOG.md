# Changelog

### Version 1.0.0

This is a major release which changes the inner workings of Pywinrm

#### Features
- Added support for sending commands through PSRP and the many benefits that brings
- Better error handling to output error details on 500 messages
- More message validation between the client and the server
- Added more shell options when using WSMV
- Many fixes over the previous WSMV like multiple environment variable support and better Python 3 compatibility
- Updated README to cover all the changes in this release
- Tests, tests and more tests
- Added some initial logging events for easier debugging

#### Deprecations
- Deprecated the existing protocol class in favour of WsmvClient or PsrpClient. Will be removed in a future version
- Deprecated the plaintext and ssl transport auth methods in favour of the WinRM named options

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