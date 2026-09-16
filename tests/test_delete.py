import pytest

from httpx import Response

from app.client import ClusterClient
from app.config import ClientConfig


@pytest.mark.asyncio
async def test_delete_group_success():

    config = ClientConfig(
        hosts=[
            "http://node1",
            "http://node2"
        ]
    )

    client = ClusterClient(config)


    async def fake_delete(url, json):

        return Response(
            status_code=200
        )


    client.http.delete = fake_delete


    results = await client.delete_group(
        "test-group"
    )


    assert len(results) == 2