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
UNIT_VALUES["seconds"] = UNIT_VALUES["s"] = 1
UNIT_VALUES["minutes"] = UNIT_VALUES["min"] = 60
UNIT_VALUES["hours"] = UNIT_VALUES["h"] = 3600
UNIT_VALUES["days"] = UNIT_VALUES["d"] = 24 * 3600
UNIT_VALUES["weeks"] = UNIT_VALUES["w"] = 7 * 24 * 3600
UNIT_VALUES["months"] = UNIT_VALUES["mon"] = 30 * 24 * 3600
UNIT_VALUES["years"] = UNIT_VALUES["y"] = 365 * 24 * 3600


def interval_to_seconds(interval_str):
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
    raise NotImplementedError("Absolute time specifiers not supported.")


def parse_time(time_str, now):
    if time_str.startswith("-"):
        interval = interval_to_seconds(time_str[1:])
        return now - timedelta(seconds=interval)
    return parse_absolute_time(time_str)
