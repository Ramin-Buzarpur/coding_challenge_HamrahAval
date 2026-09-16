import pytest

from httpx import Response

from app.client import ClusterClient
from app.config import ClientConfig
from app.models import OperationStatus


@pytest.mark.asyncio
async def test_create_group_success():

    config = ClientConfig(
        hosts=[
            "http://node1",
            "http://node2"
        ]
    )

    client = ClusterClient(config)


    async def fake_post(url, json):

        return Response(
            status_code=201
        )


    client.http.post = fake_post


    results = await client.create_group(
        "test-group"
    )


    assert len(results) == 2

    assert results[0].status == OperationStatus.SUCCESS
    assert results[1].status == OperationStatus.SUCCESS