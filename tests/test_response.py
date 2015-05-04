from __future__ import unicode_literals

from winrm import Response


def test_response_repr():
    rs = Response((
        'too long stdout will be truncated',
        'too long stderr will be truncated',
        0))
    assert str(rs) == '<Response code 0, out "too long stdout will", err "too long stderr will">'  # noqa