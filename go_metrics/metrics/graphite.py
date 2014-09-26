"""
Graphite backend for the metrics api.
"""

from urllib import urlencode
from urlparse import urljoin

from twisted.internet.defer import inlineCallbacks, returnValue

import treq

from confmodel.fields import ConfigText

from go_metrics.metrics.base import (
    Metrics, MetricsBackend, MetricsBackendError, BadMetricsQueryError)


def agg_from_name(name):
    return name.split('.')[-1]


def is_error(resp):
    return 400 <= resp.code <= 599


def omit_nulls(datapoints):
    return [d for d in datapoints if d['y'] is not None]


def zeroize_nulls(datapoints):
    return [{
        'x': d['x'],
        'y': 0.0 if d['y'] is None else d['y']
    } for d in datapoints]


null_parsers = {
    'keep': lambda x: x,
    'omit': omit_nulls,
    'zeroize': zeroize_nulls,
}


class GraphiteMetrics(Metrics):
    def _build_metric_name(self, name, interval, align_to_from):
        agg = agg_from_name(name)
        full_name = "go.campaigns.%s.%s" % (self.owner_id, name)

        return (
            "alias(summarize(%s, '%s', '%s', %s), '%s')" %
            (full_name, interval, agg, align_to_from, name))

    def _build_render_url(self, params):
        metrics = params['m']

        if (isinstance(metrics, basestring)):
            metrics = [metrics]

        targets = [
            self._build_metric_name(
                name, params['interval'], params['align_to_from'])
            for name in metrics]

        url = urljoin(self.backend.config.graphite_url, 'render/')
        return "%s?%s" % (url, urlencode({
            'format': 'json',
            'target': targets,
            'from': params['from'],
            'until': params['until'],
        }, True))

    def _parse_datapoints(self, datapoints):
        return [{
            'x': x * 1000,
            'y': y,
        } for (y, x) in datapoints]

    def _parse_response(self, data, null_parser):
        return dict(
            (d['target'], null_parser(self._parse_datapoints(d['datapoints'])))
            for d in data)

    @inlineCallbacks
    def get(self, **kw):
        params = {
            'm': [],
            'from': '-24h',
            'until': '-0s',
            'nulls': 'zeroize',
            'interval': '1hour',
            'align_to_from': 'false',
        }
        params.update(kw)

        if params['nulls'] not in null_parsers:
            raise BadMetricsQueryError(
                "Unrecognised null parser '%s'" % (params['nulls'],))

        url = self._build_render_url(params)
        resp = yield treq.get(url, persistent=False)

        if is_error(resp):
            raise MetricsBackendError(
                "Got error response for request to graphite: "
                "(%s) %s" % (resp.code, (yield resp.content())))

        null_parser = null_parsers[params['nulls']]
        returnValue(self._parse_response((yield resp.json()), null_parser))


class GraphiteBackendConfig(MetricsBackend.config_class):
    graphite_url = ConfigText(
        "Url for graphite web app to query",
        default='http://127.0.0.1:8080')


class GraphiteBackend(MetricsBackend):
    model_class = GraphiteMetrics
    config_class = GraphiteBackendConfig
