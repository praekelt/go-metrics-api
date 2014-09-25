"""
Tests for the metrics API's server.
"""
import yaml

from twisted.internet.defer import succeed, inlineCallbacks
from twisted.trial.unittest import TestCase

from confmodel.fields import ConfigText

from go_api.cyclone.helpers import AppHelper

from go_metrics.server import MetricsApi
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
