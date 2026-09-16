import pytest

from httpx import Response

from app.client import ClusterClient
from app.config import ClientConfig


@pytest.mark.asyncio
async def test_create_group_rollback_on_failure():

    config = ClientConfig(
        hosts=[
            "http://node1",
            "http://node2"
        ]
    )

    client = ClusterClient(config)

    deleted_nodes = []


    async def fake_post(url, json):

        if "node2" in url:
            raise Exception(
                "node2 failed"
            )

        return Response(
            status_code=201
        )


    async def fake_delete(url, json):

        deleted_nodes.append(url)

        return Response(
            status_code=200
        )


    client.http.post = fake_post
    client.http.delete = fake_delete


    with pytest.raises(Exception):

        await client.create_group(
            "test-group"
        )


    assert deleted_nodes == [
        "http://node1/v1/group/"
    ]