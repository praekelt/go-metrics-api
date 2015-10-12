from confmodel import Config


class MetricsBackendError(Exception):
    """
    Raised when an error occurs whilst interacting with a metrics backend.
    """


class BadMetricsQueryError(Exception):
    """
    Raised when an error occurs because a bad query was given.
    """


class Metrics(object):
    """
    A model encapsulating how metric values are queried for a particular
    backend and owner id. Intended to be subclassed with backend-specific
    logic.
    """

    def __init__(self, backend, owner_id):
        self.backend = backend
        self.owner_id = owner_id
        self.initialize()

    def initialize(self):
        """
        Optionally override for backend-specific setup
        """

    def get(self, **kw):
        """
        Override with backend-specific logic for retrieving values
        """
        raise NotImplementedError()

    def fire(self, **kw):
        """
        Override with backend-specific logic for firing metric values
        """
        raise NotImplementedError()


class MetricsBackendConfig(Config):
    """"
    Config for a metrics backend typed. Intended to be subclassed for
    backend-specific configuration
    """


class MetricsBackend(object):
    """
    Ensapsulates machinery specific to a metrics backend.
    """
    model_class = Metrics
    config_class = MetricsBackendConfig

    def __init__(self, config=None):
        if config is None:
            config = {}
        self.config = self.config_class(config)
        self.initialize()

    def initialize(self):
        """
        Optionally override for backend-specific setup
        """

    def teardown(self):
        """
        Optionally override for backend-specific tearing down
        """

    def get_model(self, owner_id):
        """
        Creates a new instance of the backend's metric model from the given
        owner id.
        """
        return self.model_class(self, owner_id)
