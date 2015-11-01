# Changelog

### Version 0.1.0
- Force basic auth header to avoid additional HTTP request and reduce latency
- Python 2.7.9+. Allow server cert validation to be ignored using SSLContext.verify_mode

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