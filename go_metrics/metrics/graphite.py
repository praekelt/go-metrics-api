"""
Graphite backend for the metrics api.
"""

from go_metrics.metrics.base import Metrics, MetricsBackend


class GraphiteMetrics(Metrics):
    pass


class GraphiteBackendConfig(MetricsBackend.config_class):
    pass


class GraphiteBackend(MetricsBackend):
    model_class = GraphiteMetrics
