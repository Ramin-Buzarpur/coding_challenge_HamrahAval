import pytest

from app.client import ClusterClient
from app.config import ClientConfig


@pytest.mark.asyncio
async def test_delete_group_rollback_on_failure():

    config = ClientConfig(
        hosts=[
            "http://node1",
            "http://node2"
        ]
    )

    client = ClusterClient(config)

    recreated_nodes = []


    async def fake_delete(url, json):

        if "node2" in url:
            raise Exception("node2 delete failed")

        return True


    async def fake_post(url, json):

        recreated_nodes.append(url)


    client.http.delete = fake_delete
    client.http.post = fake_post


    with pytest.raises(Exception):

        await client.delete_group(
            "test-group"
        )


    assert recreated_nodes == [
        "http://node1/v1/group/"
    ]