import httpx
import pytest

from app.exceptions import ClusterOperationError
from tests.conftest import FakeCluster

HOSTS = ["http://node1", "http://node2", "http://node3"]


async def test_create_is_rolled_back_when_the_first_node_fails(make_client):
    """Requests run in parallel, so a failure on node1 does not stop node2
    and node3 from creating the group. Both of them must be cleaned up."""

    cluster = FakeCluster(HOSTS, fail_on=["http://node1"])
    client = make_client(cluster)

    with pytest.raises(ClusterOperationError) as error:
        await client.create_group("team-a")

    assert sorted(error.value.rolled_back) == ["http://node2", "http://node3"]

    for host in HOSTS:
        assert "team-a" not in cluster.groups[host]


async def test_create_is_rolled_back_when_the_last_node_fails(make_client):
    cluster = FakeCluster(HOSTS, fail_on=["http://node3"])
    client = make_client(cluster)

    with pytest.raises(ClusterOperationError):
        await client.create_group("team-a")

    assert cluster.groups["http://node1"] == set()
    assert cluster.groups["http://node2"] == set()


async def test_pre_existing_group_is_left_alone(make_client):
    """node2 answered 400 because the group was already there. We did not
    create it, so the rollback must not delete it either."""

    cluster = FakeCluster(HOSTS, fail_on=["http://node3"])
    cluster.groups["http://node2"].add("team-a")

    client = make_client(cluster)

    with pytest.raises(ClusterOperationError) as error:
        await client.create_group("team-a")

    assert error.value.rolled_back == ["http://node1"]
    assert "team-a" in cluster.groups["http://node2"]


async def test_delete_is_rolled_back_by_recreating_the_group(make_client):
    cluster = FakeCluster(HOSTS)
    client = make_client(cluster)

    await client.create_group("team-a")

    cluster.fail_on = {"http://node3"}

    with pytest.raises(ClusterOperationError):
        await client.delete_group("team-a")

    # node1 and node2 were deleted and then put back.
    assert "team-a" in cluster.groups["http://node1"]
    assert "team-a" in cluster.groups["http://node2"]


async def test_failed_rollback_is_reported(make_client):
    cluster = FakeCluster(HOSTS, fail_on=["http://node3"])

    def handler(request: httpx.Request) -> httpx.Response:
        # Deleting on node1 (the rollback) always breaks.
        if request.method == "DELETE" and request.url.host == "node1":
            raise httpx.ConnectError("node1 unreachable")

        return cluster.handler(request)

    client = make_client(cluster)
    client.http.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

    with pytest.raises(ClusterOperationError) as error:
        await client.create_group("team-a")

    assert error.value.rollback_failures == ["http://node1"]
