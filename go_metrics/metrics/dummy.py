"""
Dummy backend for the metrics api for use in tests.
"""

from go_metrics.metrics.base import Metrics, MetricsBackend


class DummyMetrics(Metrics):
    pass


class DummyBackend(MetricsBackend):
    model_class = DummyMetrics
