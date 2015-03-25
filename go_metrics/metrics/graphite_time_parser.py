"""
Time period and interval parameter parsers for Graphite backend.
"""

from datetime import datetime, timedelta
import re


class TimeParserValueError(ValueError):
    """
    A value could not be parsed.
    """


INTERVAL_RE = re.compile(r'(?P<count>\d+)(?P<unit>.+)')

UNIT_VALUES = {}


def _set_unit_value(value, *names):
    for name in names:
        UNIT_VALUES[name] = value


_set_unit_value(1, "s", "second", "seconds")
_set_unit_value(60, "min", "mins", "minute", "minutes")
_set_unit_value(3600, "h", "hour", "hours")
_set_unit_value(86400, "d", "day", "days")
_set_unit_value(7 * 86400, "w", "week", "weeks")
_set_unit_value(30 * 86400, "mon", "month", "months")
_set_unit_value(365 * 86400, "y", "year", "years")


def interval_to_seconds(interval_str):
    """
    Parse a time interval specifier of the form "<count><unit>" into the
    number of seconds contained in the interval.

    NOTE: This is stricter than Graphite's parser, which accepts any string
          starting with the shortest prefix for a unit.
    """
    parts = INTERVAL_RE.match(interval_str)
    if parts is None:
        raise TimeParserValueError(
            "Invalid interval string: %r" % (interval_str,))
    count = int(parts.groupdict()["count"])
    unit = parts.groupdict()["unit"]
    unit_multiplier = UNIT_VALUES.get(unit)
    if unit_multiplier is None:
        raise TimeParserValueError(
            "Invalid interval string: %r" % (interval_str,))
    return count * unit_multiplier


def _call_or_raise(exc, func, *args, **kw):
    """
    Call func(*args, **kw) and catch any exceptions, raising exc instead.

    This exists to avoid a bunch of boilerplate try/except blocks in
    parse_absolute_time()
    """
    try:
        return func(*args, **kw)
    except:
        raise exc


def parse_absolute_time(time_str):
    """
    Parse a Graphite-compatible absolute time specifier into a datetime object.

    This accepts `HH:MM_YYYYMMDD` and `YYYYMMDD` formats as well as unix
    timestamps.
    """
    # Build an exception to pass to _call_or_raise()
    exc = TimeParserValueError("Invalid time string: %r" % (time_str,))

    if ":" in time_str:
        return _call_or_raise(exc, datetime.strptime, time_str, "%H:%M_%Y%m%d")
    elif time_str.isdigit():
        # This is the same test graphite uses to determine whether a string is
        # a unix timestamp or a `YYYYMMDD` string. It's important that we make
        # the same decisions as graphite because differences could let very
        # expensive requests slip through and potentially break either the API
        # or graphite.
        if len(time_str) == 8 and all([int(time_str[:4]) > 1900,
                                       int(time_str[4:6]) < 13,
                                       int(time_str[6:]) < 32]):
            return _call_or_raise(exc, datetime.strptime, time_str, "%Y%m%d")
        else:
            return _call_or_raise(
                exc, datetime.utcfromtimestamp, int(time_str))
    else:
        raise exc


def parse_time(time_str, now):
    """
    Parse a Graphite-compatible absolute or relative time specifier into a
    datetime object.

    NOTE: This is stricter than Graphite's parser and accepts a narrower
          variety of formats. Currently, only relative time specifiers are
          supported.
    """
    if time_str in ["now", "today"]:
        return now
    if time_str == "yesterday":
        return now - timedelta(days=1)
    if time_str == "tomorrow":
        return now + timedelta(days=1)
    if time_str.startswith("-"):
        interval = interval_to_seconds(time_str[1:])
        return now - timedelta(seconds=interval)
    return parse_absolute_time(time_str)
