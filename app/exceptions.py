class ClusterClientError(Exception):
    """Base class for every error raised by this package."""


class TransientAPIError(ClusterClientError):
    """A failure that is probably temporary, so the request is worth retrying.

    Used for 5xx responses. Timeouts and connection errors are raised by httpx
    itself and are handled separately.
    """


class NodeOperationError(ClusterClientError):
    """A node answered with something we cannot recover from (e.g. 403)."""


class ClusterOperationError(ClusterClientError):
    """The operation failed on at least one node, so it was rolled back.

    `failures` maps a host to the error it produced, `rolled_back` lists the
    hosts we had to undo, and `rollback_failures` lists the hosts where the
    undo itself did not work - those need manual attention.
    """

    def __init__(self, action, group_id, failures, rolled_back, rollback_failures):
        self.action = action
        self.group_id = group_id
        self.failures = failures
        self.rolled_back = rolled_back
        self.rollback_failures = rollback_failures

        message = f"{action} of '{group_id}' failed on {list(failures)}"

        if rollback_failures:
            message += f"; rollback also failed on {list(rollback_failures)}"

        super().__init__(message)
