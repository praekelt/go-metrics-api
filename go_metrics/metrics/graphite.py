"""
Graphite backend for the metrics api.
"""

from urllib import urlencode
from urlparse import urljoin

from twisted.internet.defer import inlineCallbacks, returnValue

import treq

from confmodel.fields import ConfigText

from go_metrics.metrics.base import Metrics, MetricsBackend


def agg_from_name(name):
    return name.split('.')[-1]


class GraphiteMetrics(Metrics):
    def _build_metric_name(self, name, interval, align_to_from):
        agg = agg_from_name(name)
        full_name = "go.campaigns.%s.%s" % (self.owner_id, name)

        return (
            "alias(summarize(%s, '%s', '%s', %s), %s)" %
            (full_name, interval, agg, align_to_from, name))

    def _build_render_url(self, params):
        targets = [
            self._build_metric_name(
                name, params['interval'], params['align_to_from'])
            for name in params['m']]

        url = urljoin(self.backend.config.graphite_url, 'render/')
        return "%s?%s" % (url, urlencode({
            'target': targets,
            'from': params['from'],
            'until': params['until'],
        }, True))

    def _parse_datapoints(self, datapoints):
        # TODO filter nulls
        return [{
            'x': x * 1000,
            'y': y,
        } for (y, x) in datapoints]

    def _parse_response(self, data):
        return dict(
            (d['target'], self._parse_datapoints(d['datapoints']))
            for d in data)

    @inlineCallbacks
    def get(self, **kw):
        params = {
            'm': [],
            'from': '-24h',
            'until': '-0s',
            'interval': '1hour',
            'align_to_from': 'false',
        }
        params.update(kw)
        url = self._build_render_url(params)
        resp = yield treq.get(url, persistent=False)
        # TODO handle error responses
        returnValue(self._parse_response((yield resp.json())))


class GraphiteBackendConfig(MetricsBackend.config_class):
    graphite_url = ConfigText(
        "Url for graphite web app to query",
        default='http://127.0.0.1:8080')


class GraphiteBackend(MetricsBackend):
    model_class = GraphiteMetrics
    config_class = GraphiteBackendConfig
