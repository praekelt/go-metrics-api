import json

from twisted.trial.unittest import TestCase
from twisted.internet.defer import inlineCallbacks, returnValue

from go_api.cyclone.helpers import MockHttpServer

from go_metrics.metrics.base import MetricsBackendError
from go_metrics.metrics.graphite import GraphiteMetrics, GraphiteBackend


class TestGraphiteMetrics(TestCase):
    @inlineCallbacks
    def mk_graphite(self, handler=None):
        graphite = MockHttpServer(handler)
        yield graphite.start()

        self.addCleanup(graphite.stop)
        returnValue(graphite)

    @inlineCallbacks
    def test_get_request(self):
        reqs = []

        def handler(req):
            reqs.append(req)
            return '{}'

        graphite = yield self.mk_graphite(handler)
        backend = GraphiteBackend({'graphite_url': graphite.url})
        metrics = GraphiteMetrics(backend, 'owner-1')

        yield metrics.get(**{
            'm': ['stores.a.b.last', 'stores.b.a.max'],
            'from': '-48h',
            'until': '-24h',
            'interval': '1day'
        })

        [req] = reqs

        self.assertTrue(req.uri.startswith('/render/?'))

        self.assertEqual(req.args, {
            'format': ['json'],
            'from': ['-48h'],
            'until': ['-24h'],
            'target': [
                "alias(summarize(go.campaigns.owner-1.stores.a.b.last,"
                " '1day', 'last', false), 'stores.a.b.last')",

                "alias(summarize(go.campaigns.owner-1.stores.b.a.max, "
                "'1day', 'max', false), 'stores.b.a.max')"],
        })

    @inlineCallbacks
    def test_get_one_request(self):
        reqs = []

        def handler(req):
            reqs.append(req)
            return '{}'

        graphite = yield self.mk_graphite(handler)
        backend = GraphiteBackend({'graphite_url': graphite.url})
        metrics = GraphiteMetrics(backend, 'owner-1')

        yield metrics.get(**{
            'm': ['stores.a.b.last'],
            'from': '-48h',
            'until': '-24h',
            'interval': '1day'
        })

        [req] = reqs

        self.assertTrue(req.uri.startswith('/render/?'))

        self.assertEqual(req.args, {
            'format': ['json'],
            'from': ['-48h'],
            'until': ['-24h'],
            'target': [
                "alias(summarize(go.campaigns.owner-1.stores.a.b.last,"
                " '1day', 'last', false), 'stores.a.b.last')"],
        })

    @inlineCallbacks
    def test_get_response(self):
        def handler(req):
            return json.dumps([{
                'target': 'stores.a.b.last',
                'datapoints': [
                    [5.0, 5695],
                    [10.0, 5700]]
            }, {
                'target': 'stores.b.a.max',
                'datapoints': [
                    [12.0, 3724],
                    [14.0, 3741]]
            }])

        graphite = yield self.mk_graphite(handler)
        backend = GraphiteBackend({'graphite_url': graphite.url})
        metrics = GraphiteMetrics(backend, 'owner-1')

        data = yield metrics.get(**{
            'm': ['stores.a.b.last', 'stores.b.a.max'],
            'from': '-48h',
            'until': '-24h',
            'interval': '1day'
        })

        self.assertEqual(data, {
            'stores.a.b.last': [{
                'x': 5695000,
                'y': 5.0
            }, {
                'x': 5700000,
                'y': 10.0
            }],
            'stores.b.a.max': [{
                'x': 3724000,
                'y': 12.0
            }, {
                'x': 3741000,
                'y': 14.0
            }]
        })

    @inlineCallbacks
    def test_get_default_metrics(self):
        reqs = []

        def handler(req):
            reqs.append(req)
            return '{}'

        graphite = yield self.mk_graphite(handler)
        backend = GraphiteBackend({'graphite_url': graphite.url})
        metrics = GraphiteMetrics(backend, 'owner-1')

        yield metrics.get(**{
            'from': '-48h',
            'until': '-24h',
            'interval': '1day'
        })

        [req] = reqs
        self.assertTrue('target' not in req.args)

    @inlineCallbacks
    def test_get_defaults(self):
        reqs = []

        def handler(req):
            reqs.append(req)
            return '{}'

        graphite = yield self.mk_graphite(handler)
        backend = GraphiteBackend({'graphite_url': graphite.url})
        metrics = GraphiteMetrics(backend, 'owner-1')

        yield metrics.get(m=['stores.a.b.last'])

        [req] = reqs
        self.assertEqual(req.args, {
            'format': ['json'],
            'from': ['-24h'],
            'until': ['-0s'],
            'target': [
                "alias(summarize(go.campaigns.owner-1.stores.a.b.last,"
                " '1hour', 'last', false), 'stores.a.b.last')"],
        })

    @inlineCallbacks
    def test_get_backend_error(self):
        def handler(req):
            req.setResponseCode(400)
            return ':('

        graphite = yield self.mk_graphite(handler)
        backend = GraphiteBackend({'graphite_url': graphite.url})
        metrics = GraphiteMetrics(backend, 'owner-1')

        try:
            yield metrics.get()
        except MetricsBackendError, e:
            self.assertEqual(str(e),
                "Got error response for request to graphite: (400) :(")
        else:
            self.fail("Expected an error")


class TestGraphiteBackend(TestCase):
    pass
