import pytest

from winrm.client import Client, convert_seconds_to_iso8601_duration, get_value_of_attribute
from winrm.exceptions import WinRMError


def test_iso8601_duration_from_string():
    expected = 'PT60S'
    actual = convert_seconds_to_iso8601_duration(expected)

    assert actual == expected


def test_iso8601_duration_from_string_as_int():
    expected = 'PT60S'
    actual = convert_seconds_to_iso8601_duration('60')

    assert actual == expected


def test_iso8601_duration_greater_than_week():
    expected = 'P2W3DT15H23S'
    actual = convert_seconds_to_iso8601_duration(1522823)

    assert actual == expected


def test_iso8601_duration_greater_than_day():
    expected = 'P2DT12H30M'
    actual = convert_seconds_to_iso8601_duration(217800)

    assert actual == expected


def test_iso8601_duration_greater_than_day_no_():
    expected = 'PT10M35S'
    actual = convert_seconds_to_iso8601_duration(635)

    assert actual == expected


def test_get_value_of_attribute():
    dict = [
        "",
        {"@Key": "Another", "#text": "notworking"},
        {"@Key": "Value", "#text": "working"}
    ]
    actual = get_value_of_attribute(dict, 'Key', 'Value', '#text')
    assert actual == 'working'


def test_get_value_of_attribute_without_element_key():
    dict = [
        "",
        {"@Key": "Another", "#text": "notworking"},
        {"@Key": "Value", "#text": "working"}
    ]
    actual = get_value_of_attribute(dict, 'Key', 'Value')
    assert actual == {'@Key': 'Value', '#text': 'working'}


def test_get_value_of_attribute_only_one_element():
    dict = {"@Key": "Value", "#text": "working"}
    actual = get_value_of_attribute(dict, 'Key', 'Value', '#text')
    assert actual == 'working'


def test_get_value_of_attribute_invalid_key():
    dict = [
        "",
        {"@DifferentKey": "Another", "#text": "notworking"},
        {"@Key": "Value", "#text": "working"}
    ]
    actual = get_value_of_attribute(dict, 'Key', 'Value', '#text')
    assert actual == 'working'


def test_get_value_of_attribute_no_value():
    dict = [
        "",
        {"@DifferentKey": "Another", "#text": "notworking"},
    ]
    actual = get_value_of_attribute(dict, 'Key', 'Value', '#text')
    assert actual is None


def test_operation_timeout_greater_then_read_timeout():
    with pytest.raises(WinRMError) as excinfo:
        Client({'read_timeout_sec': 1}, 2, 'en-US', 'utf-8', 1, '')

    assert str(excinfo.value) == 'read_timeout_sec must exceed operation_timeout_sec, and both must be non-zero'
