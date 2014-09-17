"""
Tests for the metrics API's server.

These tests are run against both the real implementation of the API and the
verified fake implementation in order to verify that both behave correctly.
"""


from twisted.trial.unittest import TestCase


class MetricsApiTestMixin(object):
    pass


class TestMetricsApi(TestCase, MetricsApiTestMixin):
    pass


class TestFakeMetricsApi(TestCase, MetricsApiTestMixin):
    pass
