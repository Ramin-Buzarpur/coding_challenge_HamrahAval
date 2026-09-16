import asyncio

from app.config import ClientConfig
from app.exceptions import ClusterOperationError, NodeOperationError
from app.http_client import HttpClient
from app.logger import get_logger
from app.models import NodeOutcome, NodeResult

logger = get_logger(__name__)


class ClusterClient:
    """Creates and deletes groups on every node of the cluster.

    An operation is only considered successful when every node accepted it.
    If any node fails, the nodes that were already changed are put back to
    their previous state and the error is raised to the caller.
    """

    def __init__(self, config: ClientConfig, http: HttpClient | None = None):
        self.config = config
        self.http = http or HttpClient(config)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        await self.close()

    async def close(self) -> None:
        await self.http.close()

    # ------------------------------------------------------------------ public

    async def create_group(self, group_id: str) -> list[NodeResult]:
        return await self._run(
            action="create",
            group_id=group_id,
            apply=self._create_on_node,
            undo=self._delete_on_node,
        )

    async def delete_group(self, group_id: str) -> list[NodeResult]:
        return await self._run(
            action="delete",
            group_id=group_id,
            apply=self._delete_on_node,
            undo=self._create_on_node,
        )

    async def group_exists(self, host: str, group_id: str) -> bool:
        """Small helper on top of the GET endpoint, handy for verification."""
        response = await self.http.get(f"{host}/v1/group/{group_id}/")
        return response.status_code == 200

    # ----------------------------------------------------------------- internal

    async def _run(self, action, group_id, apply, undo) -> list[NodeResult]:
        hosts = self.config.hosts

        logger.info("%s group '%s' on %s node(s)", action, group_id, len(hosts))

        results = await asyncio.gather(
            *(apply(host, group_id) for host in hosts),
            return_exceptions=True,
        )

        succeeded = []
        failures = {}

        # All requests were sent in parallel, so a failure on the first host
        # says nothing about the others. Every result has to be inspected
        # before deciding what to roll back.
        for host, result in zip(hosts, results):
            if isinstance(result, BaseException):
                failures[host] = result
            else:
                succeeded.append(result)

        if not failures:
            logger.info("%s of '%s' succeeded on all nodes", action, group_id)
            return list(results)

        for host, error in failures.items():
            logger.error("%s failed on %s: %s", action, host, error)

        # Only the nodes we actually changed are rolled back. A node that was
        # already in the target state (400 on create, 404 on delete) is left
        # alone, otherwise we would delete a group somebody else created.
        to_undo = [result.host for result in succeeded if result.needs_rollback]

        rollback_failures = await self._rollback(action, group_id, undo, to_undo)

        raise ClusterOperationError(
            action=action,
            group_id=group_id,
            failures=failures,
            rolled_back=to_undo,
            rollback_failures=rollback_failures,
        )

    async def _rollback(self, action, group_id, undo, hosts) -> list[str]:
        if not hosts:
            logger.info("nothing to roll back for '%s'", group_id)
            return []

        logger.warning("rolling back %s of '%s' on %s", action, group_id, hosts)

        results = await asyncio.gather(
            *(undo(host, group_id) for host in hosts),
            return_exceptions=True,
        )

        failed = []

        # Rollback is best effort. If it fails there is nothing left to try
        # automatically, so the only useful thing is a loud log line.
        for host, result in zip(hosts, results):
            if isinstance(result, BaseException):
                failed.append(host)
                logger.critical(
                    "rollback failed on %s for '%s': %s - manual cleanup needed",
                    host,
                    group_id,
                    result,
                )

        if not failed:
            logger.info("rollback of '%s' finished successfully", group_id)

        return failed

    async def _create_on_node(self, host: str, group_id: str) -> NodeResult:
        response = await self.http.post(
            f"{host}/v1/group/",
            {"groupId": group_id},
        )

        if response.status_code == 201:
            return NodeResult(host, NodeOutcome.CHANGED, 201)

        # The API docs say 400 probably means the group already exists.
        # See the assumptions section of the README.
        if response.status_code == 400:
            logger.info("group '%s' already exists on %s", group_id, host)
            return NodeResult(host, NodeOutcome.ALREADY_DONE, 400)

        raise NodeOperationError(
            f"create of '{group_id}' on {host} returned {response.status_code}"
        )

    async def _delete_on_node(self, host: str, group_id: str) -> NodeResult:
        response = await self.http.delete(
            f"{host}/v1/group/",
            {"groupId": group_id},
        )

        if response.status_code == 200:
            return NodeResult(host, NodeOutcome.CHANGED, 200)

        if response.status_code == 404:
            logger.info("group '%s' does not exist on %s", group_id, host)
            return NodeResult(host, NodeOutcome.ALREADY_DONE, 404)

        raise NodeOperationError(
            f"delete of '{group_id}' on {host} returned {response.status_code}"
        )
