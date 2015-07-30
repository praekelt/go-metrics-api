"""
Tests for the metrics API's server.
"""
import json
import yaml

from twisted.internet.defer import succeed, inlineCallbacks, maybeDeferred
from twisted.trial.unittest import TestCase

from confmodel.fields import ConfigText

from go_api.cyclone.helpers import AppHelper

from go_metrics.server import MetricsApi
from go_metrics.metrics.base import MetricsBackendError, BadMetricsQueryError
from go_metrics.metrics.dummy import DummyBackend


class DummyMetricsApi(MetricsApi):
    config_required = False
    backend_class = DummyBackend
    factory_preprocessor = staticmethod(lambda x: x)


class TestMetricsApi(TestCase):
    def mk_config(self, **kw):
        tempfile = self.mktemp()
        with open(tempfile, 'wb') as fp:
            yaml.safe_dump(kw, fp)

        return tempfile

    def test_initialize_backend(self):
        class ToyBackendConfig(DummyBackend.config_class):
            foo = ConfigText("A foo")

        class ToyBackend(DummyBackend):
            config_class = ToyBackendConfig

        class ToyApi(DummyMetricsApi):
            backend_class = ToyBackend

        app = ToyApi(self.mk_config(backend={'foo': 'bar'}))
        self.assertTrue(isinstance(app.backend, ToyBackend))
        self.assertTrue(isinstance(app.backend.config, ToyBackendConfig))
        self.assertEqual(app.backend.config.foo, 'bar')

    def test_get_metrics_model(self):
        app = DummyMetricsApi(self.mk_config())
        model = app.get_metrics_model('owner-1')
        self.assertEqual(model.owner_id, 'owner-1')

    @inlineCallbacks
    def test_metrics_get(self):
        app = DummyMetricsApi(self.mk_config())
        app.backend.fixtures.add(
            foo='bar',
            baz=['quux', 'corge'],
            result={'grault': 'garply'})

        get = AppHelper(app).get
        resp = yield get('/metrics/', params={
            'foo': 'bar',
            'baz': ['quux', 'corge']
        })
        self.assertEqual((yield resp.json()), {'grault': 'garply'})

    @inlineCallbacks
    def test_metrics_get_async(self):
        app = DummyMetricsApi(self.mk_config())
        app.backend.fixtures.add(foo='bar', result=succeed({'baz': 'quux'}))
        get = AppHelper(app).get
        resp = yield get('/metrics/', params={'foo': 'bar'})
        self.assertEqual((yield resp.json()), {'baz': 'quux'})

    @inlineCallbacks
    def test_metrics_get_query_error(self):
        app = DummyMetricsApi(self.mk_config())

        def fail():
            raise BadMetricsQueryError(":(")

        app.backend.fixtures.add(foo='bar', result=maybeDeferred(fail))

        get = AppHelper(app).get
        resp = yield get('/metrics/', params={'foo': 'bar'})

        self.assertEqual((yield resp.json()), {
            'status_code': 400,
            'reason': ':(',
        })

    @inlineCallbacks
    def test_metrics_get_backend_error(self):
        app = DummyMetricsApi(self.mk_config())

        def fail():
            raise MetricsBackendError(":(")

        app.backend.fixtures.add(foo='bar', result=maybeDeferred(fail))

        get = AppHelper(app).get
        resp = yield get('/metrics/', params={'foo': 'bar'})

        self.assertEqual((yield resp.json()), {
            'status_code': 500,
            'reason': ':(',
        })

    @inlineCallbacks
    def test_metrics_get_uncaught_error(self):
        app = DummyMetricsApi(self.mk_config())

        class DummyError(Exception):
            pass

        def fail():
            raise DummyError(":(")

        app.backend.fixtures.add(foo='bar', result=maybeDeferred(fail))

        get = AppHelper(app).get
        resp = yield get('/metrics/', params={'foo': 'bar'})

        self.assertEqual((yield resp.json()), {
            'status_code': 500,
            'reason': 'Failed to retrieve metrics.',
        })

        [f] = self.flushLoggedErrors(DummyError)
        self.assertEqual(str(f.value), ":(")

    @inlineCallbacks
    def test_metrics_post(self):
        app = DummyMetricsApi(self.mk_config())
        app.backend.fixtures.add(
            foo='bar',
            baz=['quux', 'corge'],
            method='fire',
            result={'grault': 'garply'})

        post = AppHelper(app).post
        resp = yield post('/metrics/', data=json.dumps({
            'foo': 'bar',
            'baz': ['quux', 'corge']
        }))
        self.assertEqual((yield resp.json()), {'grault': 'garply'})

    @inlineCallbacks
    def test_metrics_post_async(self):
        app = DummyMetricsApi(self.mk_config())
        app.backend.fixtures.add(
            foo='bar', result=succeed({'baz': 'quux'}), method='fire')
        post = AppHelper(app).post
        resp = yield post('/metrics/', data=json.dumps({'foo': 'bar'}))
        self.assertEqual((yield resp.json()), {'baz': 'quux'})

    @inlineCallbacks
    def test_metrics_post_query_error(self):
        app = DummyMetricsApi(self.mk_config())

        def fail():
            raise BadMetricsQueryError(":(")

        app.backend.fixtures.add(
            foo='bar', result=maybeDeferred(fail), method='fire')

        post = AppHelper(app).post
        resp = yield post('/metrics/', data=json.dumps({'foo': 'bar'}))

        self.assertEqual((yield resp.json()), {
            'status_code': 400,
            'reason': ':(',
        })

    @inlineCallbacks
    def test_metrics_post_uncaught_error(self):
        app = DummyMetricsApi(self.mk_config())

        class DummyError(Exception):
            pass

        def fail():
            raise DummyError(":(")

        app.backend.fixtures.add(
            foo='bar', result=maybeDeferred(fail), method='fire')

        post = AppHelper(app).post
        resp = yield post('/metrics/', data=json.dumps({'foo': 'bar'}))

        self.assertEqual((yield resp.json()), {
            'status_code': 500,
            'reason': 'Failed to fire metrics.',
        })

        [f] = self.flushLoggedErrors(DummyError)
        self.assertEqual(str(f.value), ":(")
