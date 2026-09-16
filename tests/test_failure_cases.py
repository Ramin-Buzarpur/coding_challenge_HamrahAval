import pytest
import httpx

from httpx import Response

from app.client import ClusterClient
from app.config import ClientConfig
from app.http_client import HttpClient


@pytest.mark.asyncio
async def test_create_accepts_existing_group_400():

    config = ClientConfig(
        hosts=[
            "http://node1"
        ]
    )

    client = ClusterClient(config)


    async def fake_post(url, json):

        return Response(
            status_code=400
        )


    client.http.post = fake_post


    result = await client.create_group(
        "existing-group"
    )


    assert len(result) == 1



@pytest.mark.asyncio
async def test_retry_on_timeout():

    config = ClientConfig(
        hosts=[
            "http://node1"
        ]
    )

    client = HttpClient(config)

    attempts = 0


    async def fake_request(*args, **kwargs):

        nonlocal attempts

        attempts += 1

        raise httpx.TimeoutException(
            "timeout"
        )


    client.client.post = fake_request


    with pytest.raises(httpx.TimeoutException):

        await client.post(
            "http://node1",
            {}
        )


    assert attempts == 3


    await client.close()