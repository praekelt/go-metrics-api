"""
Time period and interval parameter parsers for Graphite backend.
"""

from datetime import timedelta
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
_set_unit_value(60, "min", "minute", "minutes")
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


def parse_absolute_time(time_str):
    """
    Parse a Graphite-compatible absolute time specifier into a
    datetime object.

    NOTE: Currently unimplemented.
    """
    raise NotImplementedError("Absolute time specifiers not supported.")


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
