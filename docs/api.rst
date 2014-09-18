Go Metrics HTTP API
===================

Contents
--------

* :ref:`response-format-overview`
* :ref:`api-authentication`
* :ref:`api-methods`

.. _response-format-overview:

Response Format Overview
------------------------

Successful responses to GET requests will contain the requested data in json
format.

**Example response (success response)**:

.. sourcecode:: http

    HTTP/1.1 200 OK
    {...}

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

TODO
