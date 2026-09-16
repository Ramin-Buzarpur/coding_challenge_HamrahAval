class ClusterClientException(Exception):
    """Base exception for cluster client."""


class APIRequestException(ClusterClientException):
    """Raised when API request fails."""


class RetryExhaustedException(ClusterClientException):
    """Raised when retry attempts are exhausted."""