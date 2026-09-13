from datetime import date, datetime, timedelta

import pytest

from jadawel.core.formula.argument_types import (
    DateTimeJadawelRuntimeFormulaArgumentType,
    DatetimeFormatJadawelRuntimeFormulaArgumentType,
    DecimalSeparatorJadawelRuntimeFormulaArgumentType,
    DictJadawelRuntimeFormulaArgumentType,
    DurationJadawelRuntimeFormulaArgumentType,
    DurationFormatJadawelRuntimeFormulaArgumentType,
    NumberJadawelRuntimeFormulaArgumentType,
    TextJadawelRuntimeFormulaArgumentType,
    ThousandSeparatorJadawelRuntimeFormulaArgumentType,
    TimezoneJadawelRuntimeFormulaArgumentType,
)


@pytest.mark.parametrize(
    "value,expected",
    [
        (-5, True),
        (-5.5, True),
        ("-5.5", True),
        (0, True),
        (10, True),
        ("10", True),
        (16.25, True),
        ("16.25", True),
        ("foo", False),
        (" 1 ", False),
        ("", False),
        (None, False),
    ],
)
def test_number_test_method(value, expected):
    assert NumberJadawelRuntimeFormulaArgumentType().test(value) is expected


@pytest.mark.parametrize(
    "value,expected",
    [
        (-5, -5),
        ("-5", -5),
        (0, 0),
        ("0", 0),
        (15.6, 15.6),
        ("15.6", 15.6),
    ],
)
def test_number_parse_method(value, expected):
    assert NumberJadawelRuntimeFormulaArgumentType().parse(value) == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        (-5, True),
        (-5.5, True),
        ("-5.5", True),
        (0, True),
        (10, True),
        ("10", True),
        (16.25, True),
        ("16.25", True),
        ("", True),
        ({}, True),
        ([], True),
        (None, True),
    ],
)
def test_text_test_method(value, expected):
    assert TextJadawelRuntimeFormulaArgumentType().test(value) is expected


@pytest.mark.parametrize(
    "value,expected",
    [
        (-5, "-5"),
        ("-5", "-5"),
        (0, "0"),
        ("0", "0"),
        (15.6, "15.6"),
        ("15.6", "15.6"),
        ({"foo": "bar"}, '{"foo": "bar"}'),
        (["a", "b"], "a,b"),
        (None, ""),
    ],
)
def test_text_parse_method(value, expected):
    assert TextJadawelRuntimeFormulaArgumentType().parse(value) == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        ("2025-12-31", True),
        ("2025-12-31 14:22", True),
        ("2025-12-31 14:22:11", True),
        (date.today(), True),
        (datetime.now(), True),
        # None just returns True
        (None, True),
        # Invalid date format
        ("31-12-2025 14:22:11", False),
        (-5, False),
        (-5.5, False),
        (0, False),
        (10, False),
        (16.25, False),
        ("", False),
        ("-5.5", False),
        ("10", False),
        ("16.25", False),
        ([], False),
        ({}, False),
    ],
)
def test_datetime_test_method(value, expected):
    assert DateTimeJadawelRuntimeFormulaArgumentType().test(value) == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        # A date is converted to datetime with hour/minute/second to 0
        (
            "2025-12-31",
            datetime(year=2025, month=12, day=31, hour=0, minute=0, second=0),
        ),
        (
            "2025-12-31 14:22",
            datetime(year=2025, month=12, day=31, hour=14, minute=22, second=0),
        ),
        (
            "2025-12-31 14:22:11",
            datetime(year=2025, month=12, day=31, hour=14, minute=22, second=11),
        ),
        (
            date(year=2025, month=10, day=22),
            datetime(year=2025, month=10, day=22, hour=0, minute=0, second=0),
        ),
        (
            datetime(year=2025, month=10, day=22, hour=1, minute=2, second=3),
            datetime(year=2025, month=10, day=22, hour=1, minute=2, second=3),
        ),
        (None, None),
    ],
)
def test_datetime_parse_method(value, expected):
    assert DateTimeJadawelRuntimeFormulaArgumentType().parse(value) == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        ({}, True),
        ("{}", True),
        ('{"foo": "bar"}', True),
        # Invalid JSON due to single quotes
        ("{'foo': 'bar'}", False),
        ("", False),
        ([], False),
        (0, False),
        (100, False),
        ("foo", False),
        (None, False),
    ],
)
def test_dict_test_method(value, expected):
    assert DictJadawelRuntimeFormulaArgumentType().test(value) == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        ({}, {}),
        ('{"foo": "bar"}', {"foo": "bar"}),
        ({"foo": "bar"}, {"foo": "bar"}),
    ],
)
def test_dict_parse_method(value, expected):
    assert DictJadawelRuntimeFormulaArgumentType().parse(value) == expected


def test_base_argument_type_get_error_message_returns_none():
    from jadawel.core.formula.argument_types import JadawelRuntimeFormulaArgumentType

    assert JadawelRuntimeFormulaArgumentType().get_error_message("foo") is None


def test_timezone_get_error_message_returns_human_readable_string():
    arg_type = TimezoneJadawelRuntimeFormulaArgumentType()
    message = arg_type.get_error_message("Europe/Foo")
    assert "'Europe/Foo' is not a valid timezone" in message


@pytest.mark.parametrize(
    "value,expected",
    [
        (",", True),
        (".", True),
        (" ", True),
        ("", True),
        (";", False),
        ("|", False),
        ("_", False),
        (1, False),
        (None, False),
    ],
)
def test_thousand_separator_test_method(value, expected):
    assert ThousandSeparatorJadawelRuntimeFormulaArgumentType().test(value) == expected


def test_thousand_separator_get_error_message_returns_human_readable_string():
    arg_type = ThousandSeparatorJadawelRuntimeFormulaArgumentType()
    message = arg_type.get_error_message(";")
    assert "';' is not a valid thousand separator" in message


@pytest.mark.parametrize(
    "value,expected",
    [
        (",", True),
        (".", True),
        (" ", False),
        ("", False),
        (";", False),
        (1, False),
        (None, False),
    ],
)
def test_decimal_separator_test_method(value, expected):
    assert DecimalSeparatorJadawelRuntimeFormulaArgumentType().test(value) == expected


def test_decimal_separator_get_error_message_returns_human_readable_string():
    arg_type = DecimalSeparatorJadawelRuntimeFormulaArgumentType()
    message = arg_type.get_error_message(";")
    assert "';' is not a valid decimal separator" in message


@pytest.mark.parametrize(
    "value,expected",
    [
        ("1 day", True),
        ("2 days", True),
        ("3 weeks", True),
        ("4 hours", True),
        ("30 minutes", True),
        ("45 seconds", True),
        ("1 year", True),
        ("1 month", True),
        (timedelta(days=1), True),
        ("1", True),
        (1, True),
        ("1:30", True),
        ("1:30:00", True),
        ("11:12:13.14", True),
        ("1d", True),
        ("5h", True),
        ("1d 12h", True),
        ("1d 2h 3m", True),
        ("12.5", True),
        ("0 days", True),
        ("-1:30", True),
        ("foo", False),
        ("", False),
        (None, False),
    ],
)
def test_duration_string_test_method(value, expected):
    assert DurationJadawelRuntimeFormulaArgumentType().test(value) == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        ("1 day", timedelta(days=1)),
        ("2 days", timedelta(days=2)),
        ("3 weeks", timedelta(weeks=3)),
        ("4 hours", timedelta(hours=4)),
        ("30 minutes", timedelta(minutes=30)),
        ("45 seconds", timedelta(seconds=45)),
        ("1 year", timedelta(days=365)),
        ("1 month", timedelta(days=30)),
        ("1:30", timedelta(seconds=90)),
        ("1:30:00", timedelta(hours=1, minutes=30)),
        ("11:12:13.14", timedelta(hours=11, minutes=12, seconds=13.14)),
        ("1d", timedelta(days=1)),
        ("5h", timedelta(hours=5)),
        ("1d 12h", timedelta(days=1, hours=12)),
        ("1d 2h 3m", timedelta(days=1, hours=2, minutes=3)),
        ("12.5", timedelta(seconds=12.5)),
        ("0 days", timedelta(0)),
        ("-1:30", timedelta(seconds=-90)),
    ],
)
def test_duration_parse_method(value, expected):
    assert DurationJadawelRuntimeFormulaArgumentType().parse(value) == expected


def test_duration_string_get_error_message_returns_human_readable_string():
    arg_type = DurationJadawelRuntimeFormulaArgumentType()
    message = arg_type.get_error_message("not valid")
    assert "is not a valid duration" in message


@pytest.mark.parametrize(
    "value,expected",
    [
        ("YYYY-MM-DD", True),
        ("DD/MM/YYYY", True),
        ("YYYY-MM-DD HH:mm:ss", True),
        ("DD/MM/YYYY HH:mm:ss", True),
        ("YYYY-MM-DDTHH:mm:ss", True),
        ("HH:mm:ss", True),
        ("SSS", True),
        ("SS", False),
        ("S", False),
        ("Z", False),
        ("YYYY-MM-DD HH:mm:SS", False),
        ("", False),
        (123, False),
        (None, False),
    ],
)
def test_datetime_format_test_method(value, expected):
    assert DatetimeFormatJadawelRuntimeFormulaArgumentType().test(value) == expected


def test_datetime_format_get_error_message_returns_human_readable_string():
    arg_type = DatetimeFormatJadawelRuntimeFormulaArgumentType()
    message = arg_type.get_error_message("SS")
    assert "is not a valid datetime format" in message


@pytest.mark.parametrize(
    "value,expected",
    [
        ("h:mm", True),
        ("h:mm:ss", True),
        ("d h:mm:ss", True),
        ("d h mm ss", True),
        ("d", True),
        ("hh:mm:ss", True),
        # repeated token
        ("h:mm:h", False),
        # only literals, no token
        (":::", False),
        ("", False),
        (123, False),
        (None, False),
    ],
)
def test_duration_format_test_method(value, expected):
    assert DurationFormatJadawelRuntimeFormulaArgumentType().test(value) == expected


def test_duration_format_get_error_message_returns_human_readable_string():
    arg_type = DurationFormatJadawelRuntimeFormulaArgumentType()
    message = arg_type.get_error_message("not valid")
    assert "is not a valid duration format" in message
