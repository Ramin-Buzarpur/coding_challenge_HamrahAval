import json

import httpx
import pytest

from app.client import ClusterClient
from app.config import ClientConfig
from app.http_client import HttpClient


class FakeCluster:
    """A tiny in-memory stand-in for the real nodes.

    It is wired into httpx through MockTransport, so the tests go through the
    real HttpClient (URL building, request body, retries) without any network.
    """

    def __init__(self, hosts, fail_on=None, status=500):
        self.hosts = list(hosts)

        # host -> set of group ids that exist on it
        self.groups = {host: set() for host in self.hosts}

        # hosts that should answer with an error instead of doing the work
        self.fail_on = set(fail_on or ())
        self.fail_status = status

        # every request we received, as (method, host, group_id)
        self.calls = []

    def host_of(self, request):
        return f"{request.url.scheme}://{request.url.host}"

    def handler(self, request: httpx.Request) -> httpx.Response:
        host = self.host_of(request)

        if request.method == "GET":
            group_id = request.url.path.strip("/").split("/")[-1]
        else:
            group_id = json.loads(request.content)["groupId"]

        self.calls.append((request.method, host, group_id))

        if host in self.fail_on:
            return httpx.Response(self.fail_status)

        if request.method == "POST":
            if group_id in self.groups[host]:
                return httpx.Response(400)

            self.groups[host].add(group_id)
            return httpx.Response(201)

        if request.method == "DELETE":
            if group_id not in self.groups[host]:
                return httpx.Response(404)

            self.groups[host].discard(group_id)
            return httpx.Response(200)

        if request.method == "GET":
            if group_id in self.groups[host]:
                return httpx.Response(200, json={"groupId": group_id})

            return httpx.Response(404)

        return httpx.Response(405)

    def methods_for(self, host):
        return [method for method, called_host, _ in self.calls if called_host == host]


@pytest.fixture
def make_client():
    """Builds a ClusterClient backed by a FakeCluster."""

    def factory(cluster: FakeCluster, **config_kwargs):
        config = ClientConfig(
            hosts=cluster.hosts,
            max_attempts=config_kwargs.pop("max_attempts", 1),
            backoff_multiplier=0,
            backoff_max=0,
            **config_kwargs,
        )

        transport = httpx.MockTransport(cluster.handler)
        http = HttpClient(config, client=httpx.AsyncClient(transport=transport))

        return ClusterClient(config, http=http)

    return factory
