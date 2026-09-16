import json

import httpx
import pytest

from app.config import ClientConfig
from app.exceptions import TransientAPIError
from app.http_client import HttpClient


def build_client(handler, **kwargs):
    config = ClientConfig(
        hosts=["http://node1"],
        backoff_multiplier=0,
        backoff_max=0,
        **kwargs,
    )

    return HttpClient(config, client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))


async def test_delete_sends_the_group_id_in_the_body():
    """httpx.AsyncClient.delete() cannot carry a body, so this checks that
    the request is built with client.request() instead."""

    seen = {}

    def handler(request):
        seen["method"] = request.method
        seen["body"] = json.loads(request.content)
        return httpx.Response(200)

    client = build_client(handler)
    await client.delete("http://node1/v1/group/", {"groupId": "team-a"})

    assert seen == {"method": "DELETE", "body": {"groupId": "team-a"}}

    await client.close()


async def test_timeout_is_retried():
    attempts = 0

    def handler(request):
        nonlocal attempts
        attempts += 1
        raise httpx.ConnectTimeout("too slow")

    client = build_client(handler, max_attempts=3)

    with pytest.raises(httpx.ConnectTimeout):
        await client.post("http://node1/v1/group/", {"groupId": "team-a"})

    assert attempts == 3

    await client.close()


async def test_server_error_is_retried_and_then_gives_up():
    attempts = 0

    def handler(request):
        nonlocal attempts
        attempts += 1
        return httpx.Response(500)

    client = build_client(handler, max_attempts=3)

    with pytest.raises(TransientAPIError):
        await client.post("http://node1/v1/group/", {"groupId": "team-a"})

    assert attempts == 3

    await client.close()


async def test_retry_stops_as_soon_as_the_node_recovers():
    attempts = 0

    def handler(request):
        nonlocal attempts
        attempts += 1

        if attempts == 1:
            return httpx.Response(503)

        return httpx.Response(201)

    client = build_client(handler, max_attempts=3)

    response = await client.post("http://node1/v1/group/", {"groupId": "team-a"})

    assert response.status_code == 201
    assert attempts == 2

    await client.close()


async def test_client_errors_are_not_retried():
    attempts = 0

    def handler(request):
        nonlocal attempts
        attempts += 1
        return httpx.Response(400)

    client = build_client(handler, max_attempts=3)

    response = await client.post("http://node1/v1/group/", {"groupId": "team-a"})

    assert response.status_code == 400
    assert attempts == 1

    await client.close()
