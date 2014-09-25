import urlparse

from twisted.internet.defer import inlineCallbacks

from confmodel import Config
from confmodel.fields import ConfigDict

from go_api.cyclone.handlers import ApiApplication, BaseHandler

from go_metrics.metrics.graphite import GraphiteBackend


def parse_qs(qs):
    return dict(
        (k, v[0] if len(v) == 1 else v)
        for (k, v) in urlparse.parse_qs(qs).iteritems())


class MetricsHandler(BaseHandler):
    @inlineCallbacks
    def get(self):
        query = parse_qs(self.request.query)
        result = yield self.model.get(**query)
        self.write_object(result)


class MetricsApiConfig(Config):
    backend = ConfigDict("Config for metrics backend", default={})


class MetricsApi(ApiApplication):
    config_required = True
    backend_class = GraphiteBackend

    @property
    def models(self):
        return (('/metrics/', MetricsHandler, self.get_metrics_model),)

    def initialize(self, settings, config):
        config = MetricsApiConfig(config)
        self.backend = self.backend_class(config.backend)

    def get_metrics_model(self, owner_id):
        return self.backend.get_model(owner_id)
