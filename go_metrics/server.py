import functools
import base64

from urlparse import parse_qs as _parse_qs

from twisted.internet.defer import maybeDeferred, inlineCallbacks

from confmodel import Config
from confmodel.fields import ConfigDict

from go_api.cyclone.handlers import ApiApplication, BaseHandler
from cyclone.web import HTTPAuthenticationRequired

from go_metrics.metrics.base import MetricsBackendError, BadMetricsQueryError
from go_metrics.metrics.graphite import GraphiteBackend


def parse_qs(qs):
    return dict(
        (k, v[0] if len(v) == 1 else v)
        for (k, v) in _parse_qs(qs).iteritems())


def HTTPBasic(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        backend = self.model.backend
        config = backend.config
        if not (getattr(config, 'basicauth_username', None) and
                getattr(config, 'basicauth_password', None)):
            return method(self, *args, **kwargs)

        msg = "Authentication Required"
        if "Authorization" in self.request.headers:
            try:
                auth_type, data = self.request.headers["Authorization"].split()
                if auth_type == "Basic":
                    usr, pwd = base64.b64decode(data).split(":", 1)
                    if (usr == config.basicauth_username and
                            pwd == config.basicauth_password):
                            self._current_user = usr
                            return method(self, *args, **kwargs)
                    msg = "Authentication Failed"
            except (ValueError, TypeError):
                # NOTE: ValueError for when the split() doesn't work
                #       TypeError for when the data isn't base64 decodeable
                msg = "Invalid Authorization header"

        raise HTTPAuthenticationRequired(
            log_message=msg, auth_type="Basic", realm="Metrics API")

    return wrapper


class MetricsHandler(BaseHandler):

    @HTTPBasic
    def get(self):
        query = parse_qs(self.request.query)
        d = maybeDeferred(self.model.get, **query)
        d.addCallback(self.write_object)
        d.addErrback(self.catch_err, 400, BadMetricsQueryError)
        d.addErrback(self.catch_err, 500, MetricsBackendError)
        d.addErrback(self.raise_err, 500, "Failed to retrieve metrics.")
        return d

    def _assert_dict(self, d):
        if not isinstance(d, dict):
            raise BadMetricsQueryError(
                "Invalid query %r, should be dict, not %s" % (d, type(d)))

    @HTTPBasic
    def post(self):
        data = self.parse_json(self.request.body)
        d = maybeDeferred(self._assert_dict, data)
        d.addCallback(lambda _: self.model.fire(**data))
        d.addCallback(self.write_object)
        d.addErrback(self.catch_err, 400, BadMetricsQueryError)
        d.addErrback(self.raise_err, 500, "Failed to fire metrics.")
        return d


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

    @inlineCallbacks
    def teardown(self):
        yield self.backend.teardown()

    def get_metrics_model(self, owner_id):
        return self.backend.get_model(owner_id)
