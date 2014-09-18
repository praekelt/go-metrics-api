Go Metrics HTTP API
===================

Contents
--------

- :ref:`response-format-overview`
- :ref:`metric-types`
- :ref:`api-authentication`
- :ref:`api-methods`

    - :http:get:`/`

.. _response-format-overview:

Response Format Overview
------------------------

Successful responses to GET requests will contain the requested data in json
format.

**Example response (success response)**:

.. sourcecode:: http

    HTTP/1.1 200 OK
    {
        ...
    }

Errors are returned with the relevant HTTP error code and a json object
containing ``status_code``, the HTTP status code, and ``reason``, the reason
for the error.

**Example response (error response)**:

.. sourcecode:: http

    HTTP/1.1 400 Bad Request
    {
        "status_code": 400,
        "reason": "Bad Request"
    }


.. _metric-types

Metric Types
------------

Account Metrics
~~~~~~~~~~~~~~~

Account metrics are metrics relevant to a particular account, but not
necessarily relevant to a particular conversation in the account. All metrics
published via Vumi Go javascript sandbox applications are account metrics. Account metric names take the form ``stores.<store_name>.<metric_name>.<agg_method>``:

    - ``store_name``: the namespace used for publishing the metrics (e.g.
      ``default``). For javascript sandbox applications, the store name matches
      the configured name for the app in the conversation config unless
      configured otherwise.
    - ``metric_name``: the name of the metric (e.g. ``questions_completed``).
    - ``agg_method``: the aggregation method used to publish metric values (e.g.
      ``last``).


Conversation Metrics
~~~~~~~~~~~~~~~~~~~~

Conversation metrics are metrics relevant only to a particular conversation,
for example, the total messages sent in the conversation. Conversation metric
names take the form ``conversations.<conv_id>.<metric_name>.<agg_method>``:

    - ``conv_id``: the UUID for the conversation.
    - ``metric_name``: the name of the metric (e.g. ``messages_sent``).
    - ``agg_method``: the aggregation method used to publish metric values (e.g.
      ``last``).

*Note*: At the time of writing, conversation metrics are not yet ready for use.


.. _api-authentication:

API Authentication
------------------

Authentication is done using an OAuth bearer token.

**Example request**:

.. sourcecode:: http

    GET /api/contacts/ HTTP/1.1
    Host: example.com
    Authorization: Bearer auth-token

**Example response (success)**:

.. sourcecode:: http

    HTTP/1.1 200 OK

**Example response (failure)**:

.. sourcecode:: http

    HTTP/1.1 403 Forbidden

**Example response (no authorization header)**:

.. sourcecode:: http

    HTTP/1.1 401 Unauthorized


.. _api-methods:

API Methods
-----------

.. http:get:: /

    Retrieves the timestamp-value pairs of the metrics specified as query
    parameters.

    :query m: Name of a metric to be retrieved. Multiple may be specified. See
    :ref:`metric-types` for an overview of the metric name formats.

    :query from: The beginning time period to retrieve values from. Can be in
    any form accepted by graphite. See graphite's `from and until`_
    documentation. Defaults to 24 hours ago.

    :query until: The ending time period to retrieve values until. Can be in any
    form accepted by graphite. See graphite's `from and until`_ documentation.
    Defaults to the current time.

    :query interval: The size of the time buckets into which metric values
    should be summarized. Can be in any form accepted by graphite. See
    graphite's `functions` documentation. Defaults to ``1hour``.

    :query align_to_from: align the time buckets into which metric values are
    summarized against the given ``from`` time. Defaults to false.

    **Example request**:

    .. sourcecode:: http

        GET /?m=stores.a.a.last&m=stores.b.c.avg&from=-30d&until=-1d&interval=1day&align_to_from=true HTTP/1.1
        Host: example.com
        Authorization: Bearer auth-token

    **Example response (success)**:

    .. sourcecode:: http

        HTTP/1.1 200 OK

        {
            "stores.a.a.last": [{
              "x": 1405018164786,
              "y": 39598.0
            }, {
              "x": 1405104564786,
              "y": 36752.0
            }],
            "stores.b.c.avg": [{
              "x": 1405018164786,
              "y": 62431.0
            }, {
              "x": 1405104564786,
              "y": 72432.0
            }]
        }


   **Description of the JSON response attributes**:

   The response contains mappings between the metric names and their
   timestamp-value pairs.
   
   Each pair contains the timestamp under the ``x`` field, and is formatted as
   the number of milliseconds elapsed since 1 January 1970 00:00:00 UTC.

   Each pair contains the value under the ``y`` field, and is formatted as a
   json number.


.. _from and until: http://graphite.readthedocs.org/en/latest/render_api.html#from-until
.. _functions: http://graphite.readthedocs.org/en/latest/functions.html#graphite.render.functions.summarize
