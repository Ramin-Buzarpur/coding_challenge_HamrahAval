import asyncio

from app.http_client import HttpClient
from app.config import ClientConfig
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

        return results


    async def _create_on_node(
        self,
        host: str,
        group_id: str
    ):

        url = f"{host}/v1/group/"

        response = await self.http.post(
            url,
            {
                "groupId": group_id
            }
        )

        return NodeResult(
            host=host,
            status=OperationStatus.SUCCESS
        )