"""
Dummy backend for the metrics api for use in tests.
"""

from go_metrics.metrics.base import Metrics, MetricsBackend


def matches(target, items):
    for k, v in items.iteritems():
        if k not in target:
            return False

        if target[k] != items[k]:
            return False

    return True


class Fixtures(object):
    def __init__(self):
        self.items = []

    def match(self, **kw):
        for f in self.items:
            if matches(f, kw):
                return f['result']
        return {}

    def add(self, **kw):
        kw.setdefault('method', 'get')
        kw.setdefault('result', {})
        self.items.append(kw)


class DummyMetrics(Metrics):
    def get(self, **kw):
        return self.backend.fixtures.match(method='get', **kw)

    def fire(self, **kw):
        return self.backend.fixtures.match(method='fire', **kw)


class DummyBackend(MetricsBackend):
    model_class = DummyMetrics

    def initialize(self):
        self.fixtures = Fixtures()
