from datetime import datetime

from twisted.trial.unittest import TestCase

from go_metrics.metrics.graphite_time_parser import (
    TimeParserValueError, interval_to_seconds, parse_time)


class TestGraphiteTimeParser(TestCase):
    """
    Tests for Graphite-compatible time parsing functions.
    """

    def assert_TPVE(self, *args, **kw):
        """
        Convenience wrapper for asserting TimeParserValueError is raised.
        """
        return self.assertRaises(TimeParserValueError, *args, **kw)

    def test_interval_to_seconds_with_invalid_value(self):
        """
        A TimeParserValueError is raised for various invalid values.
        """
        self.assert_TPVE(interval_to_seconds, "")
        self.assert_TPVE(interval_to_seconds, "s")
        self.assert_TPVE(interval_to_seconds, "1")
        self.assert_TPVE(interval_to_seconds, "three days")
        self.assert_TPVE(interval_to_seconds, "-1h")
        self.assert_TPVE(interval_to_seconds, "2fortnights")

    def test_interval_to_seconds_with_seconds(self):
        """
        With a suffix of "s" or "seconds", the interval is parsed in seconds.
        """
        self.assertEqual(interval_to_seconds("0s"), 0)
        self.assertEqual(interval_to_seconds("0seconds"), 0)
        self.assertEqual(interval_to_seconds("1s"), 1)
        self.assertEqual(interval_to_seconds("1seconds"), 1)
        self.assertEqual(interval_to_seconds("60s"), 60)
        self.assertEqual(interval_to_seconds("60seconds"), 60)
        self.assertEqual(interval_to_seconds("1234567s"), 1234567)
        self.assertEqual(interval_to_seconds("1234567seconds"), 1234567)
        self.assertEqual(interval_to_seconds("012s"), 12)
        self.assertEqual(interval_to_seconds("012seconds"), 12)

    def test_interval_to_seconds_with_minutes(self):
        """
        With a suffix of "min" or "minutes", the interval is parsed in minutes.
        """
        self.assertEqual(interval_to_seconds("0min"), 0)
        self.assertEqual(interval_to_seconds("0minutes"), 0)
        self.assertEqual(interval_to_seconds("1min"), 60)
        self.assertEqual(interval_to_seconds("1minutes"), 60)
        self.assertEqual(interval_to_seconds("60min"), 3600)
        self.assertEqual(interval_to_seconds("60minutes"), 3600)
        self.assertEqual(interval_to_seconds("1234567min"), 1234567 * 60)
        self.assertEqual(interval_to_seconds("1234567minutes"), 1234567 * 60)
        self.assertEqual(interval_to_seconds("012min"), 720)
        self.assertEqual(interval_to_seconds("012minutes"), 720)

    def test_interval_to_seconds_with_hours(self):
        """
        With a suffix of "h" or "hours", the interval is parsed in hours.
        """
        self.assertEqual(interval_to_seconds("0h"), 0)
        self.assertEqual(interval_to_seconds("0hours"), 0)
        self.assertEqual(interval_to_seconds("1h"), 3600)
        self.assertEqual(interval_to_seconds("1hours"), 3600)
        self.assertEqual(interval_to_seconds("24h"), 24 * 3600)
        self.assertEqual(interval_to_seconds("24hours"), 24 * 3600)
        self.assertEqual(interval_to_seconds("1234h"), 1234 * 3600)
        self.assertEqual(interval_to_seconds("1234hours"), 1234 * 3600)
        self.assertEqual(interval_to_seconds("012h"), 12 * 3600)
        self.assertEqual(interval_to_seconds("012hours"), 12 * 3600)

    def test_interval_to_seconds_with_days(self):
        """
        With a suffix of "d" or "days", the interval is parsed in days.
        """
        self.assertEqual(interval_to_seconds("0d"), 0)
        self.assertEqual(interval_to_seconds("0days"), 0)
        self.assertEqual(interval_to_seconds("1d"), 86400)
        self.assertEqual(interval_to_seconds("1days"), 86400)
        self.assertEqual(interval_to_seconds("60d"), 60 * 86400)
        self.assertEqual(interval_to_seconds("60days"), 60 * 86400)
        self.assertEqual(interval_to_seconds("1234d"), 1234 * 86400)
        self.assertEqual(interval_to_seconds("1234d"), 1234 * 86400)
        self.assertEqual(interval_to_seconds("014d"), 14 * 86400)
        self.assertEqual(interval_to_seconds("014days"), 14 * 86400)

    def test_interval_to_seconds_with_weeks(self):
        """
        With a suffix of "w" or "weeks", the interval is parsed in weeks.
        """
        self.assertEqual(interval_to_seconds("0w"), 0)
        self.assertEqual(interval_to_seconds("0weeks"), 0)
        self.assertEqual(interval_to_seconds("1w"), 604800)
        self.assertEqual(interval_to_seconds("1weeks"), 604800)
        self.assertEqual(interval_to_seconds("4w"), 2419200)
        self.assertEqual(interval_to_seconds("4weeks"), 2419200)
        self.assertEqual(interval_to_seconds("123w"), 123 * 604800)
        self.assertEqual(interval_to_seconds("123weeks"), 123 * 604800)
        self.assertEqual(interval_to_seconds("012w"), 12 * 604800)
        self.assertEqual(interval_to_seconds("012weeks"), 12 * 604800)

    def test_interval_to_seconds_with_months(self):
        """
        With a suffix of "mon" or "months", the interval is parsed in months.
        """
        self.assertEqual(interval_to_seconds("0mon"), 0)
        self.assertEqual(interval_to_seconds("0months"), 0)
        self.assertEqual(interval_to_seconds("1mon"), 2592000)
        self.assertEqual(interval_to_seconds("1months"), 2592000)
        self.assertEqual(interval_to_seconds("12mon"), 12 * 2592000)
        self.assertEqual(interval_to_seconds("12months"), 12 * 2592000)
        self.assertEqual(interval_to_seconds("123mon"), 123 * 2592000)
        self.assertEqual(interval_to_seconds("123months"), 123 * 2592000)
        self.assertEqual(interval_to_seconds("012mon"), 12 * 2592000)
        self.assertEqual(interval_to_seconds("012months"), 12 * 2592000)

    def test_interval_to_seconds_with_years(self):
        """
        With a suffix of "y" or "years", the interval is parsed in years.
        """
        self.assertEqual(interval_to_seconds("0y"), 0)
        self.assertEqual(interval_to_seconds("0years"), 0)
        self.assertEqual(interval_to_seconds("1y"), 31536000)
        self.assertEqual(interval_to_seconds("1years"), 31536000)
        self.assertEqual(interval_to_seconds("5y"), 5 * 31536000)
        self.assertEqual(interval_to_seconds("5years"), 5 * 31536000)
        self.assertEqual(interval_to_seconds("123y"), 123 * 31536000)
        self.assertEqual(interval_to_seconds("123years"), 123 * 31536000)
        self.assertEqual(interval_to_seconds("02y"), 2 * 31536000)
        self.assertEqual(interval_to_seconds("02years"), 2 * 31536000)

    def test_parse_time_with_invalid_interval(self):
        """
        If given a time_str starting with "-" and containing an invalid
        interval, a TimeParserValueError is raised.
        """
        now = datetime(2015, 2, 1, 0, 0, 0)
        self.assert_TPVE(parse_time, "-0", now)
        self.assert_TPVE(parse_time, "-12", now)
        self.assert_TPVE(parse_time, "-20150101", now)

    def test_parse_time_with_interval(self):
        """
        If given a time_str starting with "-", the time is parsed as an
        interval prior to "now".
        """
        now = datetime(2015, 2, 1, 0, 0, 0)
        self.assertEqual(parse_time("-0s", now), now)
        self.assertEqual(
            parse_time("-1s", now), datetime(2015, 1, 31, 23, 59, 59))
        self.assertEqual(
            parse_time("-1s", now), datetime(2015, 1, 31, 23, 59, 59))
        self.assertEqual(
            parse_time("-2w", now), datetime(2015, 1, 18, 0, 0, 0))
