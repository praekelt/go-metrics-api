import json
from base64 import b64encode

from twisted.trial.unittest import TestCase
from twisted.internet.defer import inlineCallbacks, returnValue

from confmodel.errors import ConfigError

from go_api.cyclone.helpers import MockHttpServer

import go_metrics.metrics.graphite
from go_metrics.metrics.base import MetricsBackendError, BadMetricsQueryError
from go_metrics.metrics.graphite import (
    GraphiteMetrics, GraphiteBackend, GraphiteBackendConfig, MetricWorker)

# from vumi.tests.utils import VumiWorkerTestCase
from vumi.tests.helpers import VumiTestCase, WorkerHelper


class DummyWorkerCreatorClass(object):
    def __init__(self, test_case, expected_config, worker):
        self._test_case = test_case
        self._expected_config = expected_config
        self._worker = worker

    def __call__(self, config):
        return DummyWorkerCreator(
            self._test_case, self._expected_config, self._worker)


class DummyWorkerCreator(object):
    def __init__(self, test_case, expected_config, worker):
        self._test_case = test_case
        self._expected_config = expected_config
        self._worker = worker

    def create_worker_by_class(self, cls, cfg):
        self._test_case.assertEqual(cls, MetricWorker)
        self._test_case.assertEqual(cfg, self._expected_config)
        return self._worker


class TestGraphiteMetrics(VumiTestCase):

    def setUp(self):
        self.worker_helper = self.add_helper(WorkerHelper())

    def get_worker(self, config, worker_class):
        return self.worker_helper.get_worker(worker_class, config)

    @inlineCallbacks
    def mk_graphite(self, handler=None):
        graphite = MockHttpServer(handler)
        yield graphite.start()

        self.addCleanup(graphite.stop)
        returnValue(graphite)

    @inlineCallbacks
    def mk_backend(self, **kw):
        kw.setdefault('persistent', False)
        prefix = kw.setdefault('prefix', 'go.campaigns')
        worker = yield self.get_worker({'prefix': prefix}, MetricWorker)

        worker_creator_cls = DummyWorkerCreatorClass(
            self, {'prefix': prefix}, worker)
        self.patch(
            go_metrics.metrics.graphite, 'WorkerCreator', worker_creator_cls)

        backend = GraphiteBackend(kw)
        self.addCleanup(backend.teardown)
        returnValue(backend)

    @inlineCallbacks
    def test_get_request(self):
        reqs = []

        def handler(req):
            reqs.append(req)
            return '{}'

        graphite = yield self.mk_graphite(handler)
        backend = yield self.mk_backend(graphite_url=graphite.url)
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
        backend = yield self.mk_backend(graphite_url=graphite.url)
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
    def test_get_one_request_no_list(self):
        reqs = []

        def handler(req):
            reqs.append(req)
            return '{}'

        graphite = yield self.mk_graphite(handler)
        backend = yield self.mk_backend(graphite_url=graphite.url)
        metrics = GraphiteMetrics(backend, 'owner-1')

        yield metrics.get(**{
            'm': 'stores.a.b.last',
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
        backend = yield self.mk_backend(graphite_url=graphite.url)
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
        backend = yield self.mk_backend(graphite_url=graphite.url)
        metrics = GraphiteMetrics(backend, 'owner-1')

        yield metrics.get(**{
            'from': '-48h',
            'until': '-24h',
            'interval': '1day'
        })

        [req] = reqs
        self.assertTrue('target' not in req.args)

    @inlineCallbacks
    def test_reject_large_request(self):
        """
        Requests for excessive amounts of data are rejected.
        """
        backend = yield self.mk_backend()
        metrics = GraphiteMetrics(backend, 'owner-1')

        err = yield self.assertFailure(
            metrics.get(**{'from': '-1d', 'interval': '1s'}),
            BadMetricsQueryError)
        self.assertEqual(
            str(err),
            "86400 data points requested, maximum allowed is 10000")

        # "from" can be later than "until".
        err = yield self.assertFailure(
            metrics.get(**{'from': 'now', 'until': '-1d', 'interval': '1s'}),
            BadMetricsQueryError)
        self.assertEqual(
            str(err),
            "86400 data points requested, maximum allowed is 10000")

    @inlineCallbacks
    def test_reject_large_request_multiple_metrics(self):
        """
        Requests for excessive amounts of data are rejected, even if the
        results for individual metrics are within the limits.
        """
        reqs = []

        def handler(req):
            reqs.append(req)
            return '{}'

        graphite = yield self.mk_graphite(handler)
        backend = yield self.mk_backend(graphite_url=graphite.url)
        metrics = GraphiteMetrics(backend, 'owner-1')

        # Two metrics, 8640 points each.
        err = yield self.assertFailure(
            metrics.get(**{
                'm': ['a', 'b'],
                'from': '-1d',
                'interval': '10s',
            }),
            BadMetricsQueryError)
        self.assertEqual(
            str(err),
            "17280 data points requested, maximum allowed is 10000")

        # Only one metric.
        resp = yield metrics.get(**{'from': '-1d', 'interval': '10s'})
        self.assertEqual(resp, {})

    @inlineCallbacks
    def test_reject_large_request_with_config(self):
        """
        The excessive data rejection threshold is configurable.
        """
        reqs = []

        def handler(req):
            reqs.append(req)
            return '{}'

        graphite = yield self.mk_graphite(handler)
        backend = yield self.mk_backend(
            graphite_url=graphite.url, max_response_size=100000)
        metrics = GraphiteMetrics(backend, 'owner-1')

        # Too much data.
        err = yield self.assertFailure(
            metrics.get(**{'from': '-2d', 'interval': '1s'}),
            BadMetricsQueryError)
        self.assertEqual(
            str(err),
            "172800 data points requested, maximum allowed is 100000")

        # Not too much data.
        resp = yield metrics.get(**{'from': '-1d', 'interval': '1s'})
        self.assertEqual(resp, {})

    @inlineCallbacks
    def test_get_defaults(self):
        reqs = []

        def handler(req):
            reqs.append(req)
            return '{}'

        graphite = yield self.mk_graphite(handler)
        backend = yield self.mk_backend(graphite_url=graphite.url)
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
        backend = yield self.mk_backend(graphite_url=graphite.url)
        metrics = GraphiteMetrics(backend, 'owner-1')

        err = yield self.assertFailure(metrics.get(), MetricsBackendError)
        self.assertEqual(
            str(err), "Got error response interacting with metrics backend")

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
        backend = yield self.mk_backend(graphite_url=graphite.url)
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
        backend = yield self.mk_backend(graphite_url=graphite.url)
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
        backend = yield self.mk_backend(graphite_url=graphite.url)
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
        backend = yield self.mk_backend(graphite_url=graphite.url)
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
        backend = yield self.mk_backend(graphite_url=graphite.url)
        metrics = GraphiteMetrics(backend, 'owner-1')

        err = yield self.assertFailure(
            metrics.get(m=['stores.a.b.last', 'stores.b.a.max'], nulls='bad'),
            BadMetricsQueryError)
        self.assertEqual(str(err), "Unrecognised null parser 'bad'")

    @inlineCallbacks
    def test_get_auth(self):
        reqs = []

        def handler(req):
            reqs.append(req)
            return '{}'

        graphite = yield self.mk_graphite(handler)
        backend = yield self.mk_backend(
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
        backend = yield self.mk_backend(graphite_url=graphite.url)

        metrics = GraphiteMetrics(backend, 'owner-1')

        yield metrics.get(**{
            'm': ['stores.a.b.last', 'stores.b.a.max'],
            'from': '-48h',
            'until': '-24h',
            'interval': '1day'
        })

        [req] = reqs
        self.assertEqual(req.getHeader('Authorization'), None)

    @inlineCallbacks
    def test_post_request_single(self):
        backend = yield self.mk_backend()
        metrics = GraphiteMetrics(backend, 'owner-1')

        res = yield metrics.fire(**{'foo.avg': 1.7})
        [metric] = res

        self.assertEqual(metric, {
            'name': 'foo.avg',
            'value': 1.7,
            'aggregator': 'avg',
        })

    @inlineCallbacks
    def test_post_request_multiple(self):
        backend = yield self.mk_backend()
        metrics = GraphiteMetrics(backend, 'owner-1')

        res = yield metrics.fire(**{'foo.avg': 1.2, 'oof.avg': 2.7})

        self.assertEqual(sorted(res), sorted([{
            'name': 'foo.avg',
            'value': 1.2,
            'aggregator': 'avg',
        }, {
            'name': 'oof.avg',
            'value': 2.7,
            'aggregator': 'avg',
        }]))

    @inlineCallbacks
    def test_post_request_bad_value(self):
        backend = yield self.mk_backend()
        metrics = GraphiteMetrics(backend, 'owner-1')

        try:
            yield metrics.fire(**{'foo.avg': 'bar'})
        except BadMetricsQueryError as e:
            self.assertEqual(
                str(e), "'bar' is not a valid metric value,should be a "
                "floating point number")
        else:
            self.fail("BadMetricQueryError not raised")

    @inlineCallbacks
    def test_post_request_bad_aggregator(self):
        backend = yield self.mk_backend()
        metrics = GraphiteMetrics(backend, 'owner-1')

        try:
            yield metrics.fire(**{'foo': 1.2})
        except BadMetricsQueryError as e:
            self.assertEqual(
                str(e), "Aggregator 'foo' is not a valid aggregator")
        else:
            self.fail("BadMetricQueryError not raised")

    @inlineCallbacks
    def test_post_aggregators(self):
        backend = yield self.mk_backend()
        metrics = GraphiteMetrics(backend, 'owner-1')

        for agg in GraphiteMetrics.aggregators:
            res = yield metrics.fire(**{'foo.%s' % agg: 1.3})
            [metric] = res
            self.assertEqual(metric['aggregator'], agg)


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
