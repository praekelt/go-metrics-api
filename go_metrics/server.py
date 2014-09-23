from go_api.cyclone.handlers import ApiApplication, BaseHandler

from confmodel import Config, ConfigDict

from go_metrics.metrics.graphite import GraphiteBackend


class MetricsHandler(BaseHandler)
    model_alias = 'backend'


class MetricsApiConfig(Config):
    backend = ConfigDict("Config for metrics backend", required=True)


class MetricssApi(ApiApplication):
    config_required = True
    backend_class = GraphiteBackend

    @property
    def models(self):
        return (('/metrics', MetricsHandler, self.get_metrics_model))

    def initialize(self, config):
        config = MetricssApi(config)
        self.metrics_backend = self.backend_class(config.backend)

    def get_metrics_model(self, owner_id):
        return self.metrics_backend.get_model(owner_id)
