import asyncio

from app.config import ClientConfig
from app.http_client import HttpClient
from app.models import NodeResult, OperationStatus


class ClusterClient:

    def __init__(self, config: ClientConfig):
        self.config = config
        self.http = HttpClient(config)


    async def create_group(self, group_id: str):

        tasks = [
            self._create_on_node(host, group_id)
            for host in self.config.hosts
        ]

        results = await asyncio.gather(
            *tasks,
            return_exceptions=True
        )

        successful_nodes = []

        for host, result in zip(
            self.config.hosts,
            results
        ):

            if isinstance(result, Exception):

                await self._rollback_create(
                    successful_nodes,
                    group_id
                )

                raise result

            successful_nodes.append(host)

        return results


    async def delete_group(self, group_id: str):

        tasks = [
            self._delete_on_node(host, group_id)
            for host in self.config.hosts
        ]

        results = await asyncio.gather(
            *tasks,
            return_exceptions=True
        )

        deleted_nodes = []

        for host, result in zip(
            self.config.hosts,
            results
        ):

            if isinstance(result, Exception):

                await self._rollback_delete(
                    deleted_nodes,
                    group_id
                )

                raise result

            deleted_nodes.append(host)

        return results


    async def _create_on_node(
        self,
        host: str,
        group_id: str
    ):

        url = f"{host}/v1/group/"

        await self.http.post(
            url,
            {
                "groupId": group_id
            }
        )

        return NodeResult(
            host=host,
            status=OperationStatus.SUCCESS
        )


    async def _delete_on_node(
        self,
        host: str,
        group_id: str
    ):

        url = f"{host}/v1/group/"

        await self.http.delete(
            url,
            {
                "groupId": group_id
            }
        )

        return NodeResult(
            host=host,
            status=OperationStatus.SUCCESS
        )


    async def _rollback_create(
        self,
        successful_nodes: list[str],
        group_id: str
    ):

        tasks = [
            self._delete_on_node(
                host,
                group_id
            )
            for host in successful_nodes
        ]

        await asyncio.gather(
            *tasks,
            return_exceptions=True
        )


    async def _rollback_delete(
        self,
        deleted_nodes: list[str],
        group_id: str
    ):

        tasks = [
            self._create_on_node(
                host,
                group_id
            )
            for host in deleted_nodes
        ]

        await asyncio.gather(
            *tasks,
            return_exceptions=True
        )