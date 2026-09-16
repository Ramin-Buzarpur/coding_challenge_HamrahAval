import asyncio

from app.config import ClientConfig
from app.http_client import HttpClient
from app.models import NodeResult, OperationStatus
from app.logger import get_logger


class ClusterClient:

    def __init__(self, config: ClientConfig):

        self.config = config
        self.http = HttpClient(config)
        self.logger = get_logger(__name__)


    async def create_group(
        self,
        group_id: str
    ):

        tasks = [
            self._create_on_node(
                host,
                group_id
            )
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



    async def delete_group(
        self,
        group_id: str
    ):

        tasks = [
            self._delete_on_node(
                host,
                group_id
            )
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
        host,
        group_id
    ):

        response = await self.http.post(
            f"{host}/v1/group/",
            {
                "groupId": group_id
            }
        )


        # already exists is acceptable
        if response.status_code not in (
            201,
            400
        ):
            raise Exception(
                f"Create failed on {host}: {response.status_code}"
            )


        return NodeResult(
            host,
            OperationStatus.SUCCESS
        )



    async def _delete_on_node(
        self,
        host,
        group_id
    ):

        response = await self.http.delete(
            f"{host}/v1/group/",
            {
                "groupId": group_id
            }
        )


        # not existing is acceptable
        if response.status_code not in (
            200,
            404
        ):
            raise Exception(
                f"Delete failed on {host}: {response.status_code}"
            )


        return NodeResult(
            host,
            OperationStatus.SUCCESS
        )



    async def _rollback_create(
        self,
        nodes,
        group_id
    ):

        tasks = [
            self._delete_on_node(
                node,
                group_id
            )
            for node in nodes
        ]


        await asyncio.gather(
            *tasks,
            return_exceptions=True
        )



    async def _rollback_delete(
        self,
        nodes,
        group_id
    ):

        tasks = [
            self._create_on_node(
                node,
                group_id
            )
            for node in nodes
        ]


        await asyncio.gather(
            *tasks,
            return_exceptions=True
        )