import json
from base64 import b64encode

from twisted.trial.unittest import TestCase
from twisted.internet.defer import inlineCallbacks, returnValue

from confmodel.errors import ConfigError

from go_api.cyclone.helpers import MockHttpServer

from go_metrics.metrics.base import MetricsBackendError, BadMetricsQueryError
from go_metrics.metrics.graphite import (
    GraphiteMetrics, GraphiteBackend, GraphiteBackendConfig)


class TestGraphiteMetrics(TestCase):
    @inlineCallbacks
    def mk_graphite(self, handler=None):
        graphite = MockHttpServer(handler)
        yield graphite.start()

        self.addCleanup(graphite.stop)
        returnValue(graphite)

    def mk_backend(self, **kw):
        kw.setdefault('persistent', False)
        return GraphiteBackend(kw)

    @inlineCallbacks
    def test_get_request(self):
        reqs = []

        def handler(req):
            reqs.append(req)
            return '{}'

        graphite = yield self.mk_graphite(handler)
        backend = self.mk_backend(graphite_url=graphite.url)
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
        backend = self.mk_backend(graphite_url=graphite.url)
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
        backend = self.mk_backend(graphite_url=graphite.url)
        metrics = GraphiteMetrics(backend, 'owner-1')

        data = yield metrics.get(m=['stores.a.b.last', 'stores.b.a.max'])

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
        backend = self.mk_backend(graphite_url=graphite.url)
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
        backend = self.mk_backend(graphite_url=graphite.url)
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
        backend = self.mk_backend(graphite_url=graphite.url)
        metrics = GraphiteMetrics(backend, 'owner-1')

        try:
            yield metrics.get()
        except MetricsBackendError, e:
            self.assertEqual(str(e),
                "Got error response interacting with metrics backend")
        else:
            self.fail("Expected an error")

    @inlineCallbacks
    def test_get_null_handling_default(self):
        def handler(req):
            return json.dumps([{
                'target': 'stores.a.b.last',
                'datapoints': [
                    [None, 2695],
                    [5.0, 3695],
                    [None, 4695],
                    [None, 5695],
                    [10.0, 6695],
                    [None, 7695]]
            }, {
                'target': 'stores.b.a.max',
                'datapoints': [
                    [None, 2695],
                    [12.0, 3695],
                    [None, 4695],
                    [14.0, 5695]]
            }])

        graphite = yield self.mk_graphite(handler)
        backend = self.mk_backend(graphite_url=graphite.url)
        metrics = GraphiteMetrics(backend, 'owner-1')

        self.assertEqual(
            (yield metrics.get(
                m=['stores.a.b.last', 'stores.b.a.max'])),
            (yield metrics.get(
                m=['stores.a.b.last', 'stores.b.a.max'],
                nulls='zeroize')))

    @inlineCallbacks
    def test_get_null_handling_zeroize(self):
        def handler(req):
            return json.dumps([{
                'target': 'stores.a.b.last',
                'datapoints': [
                    [None, 2695],
                    [5.0, 3695],
                    [None, 4695],
                    [None, 5695],
                    [10.0, 6695],
                    [None, 7695]]
            }, {
                'target': 'stores.b.a.max',
                'datapoints': [
                    [None, 2695],
                    [12.0, 3695],
                    [None, 4695],
                    [14.0, 5695]]
            }])

        graphite = yield self.mk_graphite(handler)
        backend = self.mk_backend(graphite_url=graphite.url)
        metrics = GraphiteMetrics(backend, 'owner-1')

        data = yield metrics.get(
            m=['stores.a.b.last', 'stores.b.a.max'],
            nulls='zeroize')

        self.assertEqual(data, {
            'stores.a.b.last': [{
                'x': 2695000,
                'y': 0.0
            }, {
                'x': 3695000,
                'y': 5.0
            }, {
                'x': 4695000,
                'y': 0.0
            }, {
                'x': 5695000,
                'y': 0.0
            }, {
                'x': 6695000,
                'y': 10.0
            }, {
                'x': 7695000,
                'y': 0.0
            }],
            'stores.b.a.max': [{
                'x': 2695000,
                'y': 0.0
            }, {
                'x': 3695000,
                'y': 12.0
            }, {
                'x': 4695000,
                'y': 0.0
            }, {
                'x': 5695000,
                'y': 14.0
            }]
        })

    @inlineCallbacks
    def test_get_null_handling_omit(self):
        def handler(req):
            return json.dumps([{
                'target': 'stores.a.b.last',
                'datapoints': [
                    [None, 2695],
                    [5.0, 3695],
                    [None, 4695],
                    [None, 5695],
                    [10.0, 6695],
                    [None, 7695]]
            }, {
                'target': 'stores.b.a.max',
                'datapoints': [
                    [None, 2695],
                    [12.0, 3695],
                    [None, 4695],
                    [14.0, 5695]]
            }])

        graphite = yield self.mk_graphite(handler)
        backend = self.mk_backend(graphite_url=graphite.url)
        metrics = GraphiteMetrics(backend, 'owner-1')

        data = yield metrics.get(
            m=['stores.a.b.last', 'stores.b.a.max'],
            nulls='omit')

        self.assertEqual(data, {
            'stores.a.b.last': [{
                'x': 3695000,
                'y': 5.0
            }, {
                'x': 6695000,
                'y': 10.0
            }],
            'stores.b.a.max': [{
                'x': 3695000,
                'y': 12.0
            }, {
                'x': 5695000,
                'y': 14.0
            }]
        })

    @inlineCallbacks
    def test_get_null_handling_keep(self):
        def handler(req):
            return json.dumps([{
                'target': 'stores.a.b.last',
                'datapoints': [
                    [None, 2695],
                    [5.0, 3695],
                    [None, 4695],
                    [None, 5695],
                    [10.0, 6695],
                    [None, 7695]]
            }, {
                'target': 'stores.b.a.max',
                'datapoints': [
                    [None, 2695],
                    [12.0, 3695],
                    [None, 4695],
                    [14.0, 5695]]
            }])

        graphite = yield self.mk_graphite(handler)
        backend = self.mk_backend(graphite_url=graphite.url)
        metrics = GraphiteMetrics(backend, 'owner-1')

        data = yield metrics.get(
            m=['stores.a.b.last', 'stores.b.a.max'],
            nulls='keep')

        self.assertEqual(data, {
            'stores.a.b.last': [{
                'x': 2695000,
                'y': None
            }, {
                'x': 3695000,
                'y': 5.0
            }, {
                'x': 4695000,
                'y': None
            }, {
                'x': 5695000,
                'y': None
            }, {
                'x': 6695000,
                'y': 10.0
            }, {
                'x': 7695000,
                'y': None
            }],
            'stores.b.a.max': [{
                'x': 2695000,
                'y': None
            }, {
                'x': 3695000,
                'y': 12.0
            }, {
                'x': 4695000,
                'y': None
            }, {
                'x': 5695000,
                'y': 14.0
            }]
        })

    @inlineCallbacks
    def test_get_null_handling_unrecognised(self):
        graphite = yield self.mk_graphite()
        backend = self.mk_backend(graphite_url=graphite.url)
        metrics = GraphiteMetrics(backend, 'owner-1')

        try:
            yield metrics.get(
                m=['stores.a.b.last', 'stores.b.a.max'],
                nulls='bad')
        except BadMetricsQueryError, e:
            self.assertEqual(str(e), "Unrecognised null parser 'bad'")
        else:
            self.fail("Expected an error")

    @inlineCallbacks
    def test_get_auth(self):
        reqs = []

        def handler(req):
            reqs.append(req)
            return '{}'

        graphite = yield self.mk_graphite(handler)
        backend = self.mk_backend(
            graphite_url=graphite.url,
            username="root",
            password="toor")

        metrics = GraphiteMetrics(backend, 'owner-1')

        yield metrics.get(**{
            'm': ['stores.a.b.last', 'stores.b.a.max'],
            'from': '-48h',
            'until': '-24h',
            'interval': '1day'
        })

        [req] = reqs
        self.assertEqual(
            req.getHeader('Authorization'),
            'Basic %s' % (b64encode('root:toor')))

    @inlineCallbacks
    def test_get_no_auth(self):
        reqs = []

        def handler(req):
            reqs.append(req)
            return '{}'

        graphite = yield self.mk_graphite(handler)
        backend = self.mk_backend(graphite_url=graphite.url)

        metrics = GraphiteMetrics(backend, 'owner-1')

        yield metrics.get(**{
            'm': ['stores.a.b.last', 'stores.b.a.max'],
            'from': '-48h',
            'until': '-24h',
            'interval': '1day'
        })

        [req] = reqs
        self.assertEqual(req.getHeader('Authorization'), None)


class TestGraphiteBackendConfig(TestCase):
    def test_auth_fields(self):
        GraphiteBackendConfig({})
        GraphiteBackendConfig({
            'username': 'foo',
            'password': 'bar',
        })
        self.assertRaises(
            ConfigError, GraphiteBackendConfig, {'username': 'foo'})
        self.assertRaises(
            ConfigError, GraphiteBackendConfig, {'password': 'bar'})
