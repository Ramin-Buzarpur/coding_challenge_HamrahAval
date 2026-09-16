import pytest

from app.config import ClientConfig
from app.http_client import HttpClient


@pytest.mark.asyncio
async def test_http_client_creation():

    config = ClientConfig(
        hosts=[
            "http://node1"
        ]
    )

    client = HttpClient(config)

    assert client.client is not None

    await client.close()