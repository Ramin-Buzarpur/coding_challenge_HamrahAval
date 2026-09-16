class ClusterClientException(Exception):
    pass


class APIRequestException(ClusterClientException):
    pass


class RetryExhaustedException(ClusterClientException):
    pass