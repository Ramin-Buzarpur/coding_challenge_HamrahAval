import pytest

from app.exceptions import ClusterOperationError
from app.models import NodeOutcome
from tests.conftest import FakeCluster

HOSTS = ["http://node1", "http://node2", "http://node3"]


async def test_group_is_created_on_every_node(make_client):
    cluster = FakeCluster(HOSTS)
    client = make_client(cluster)

    results = await client.create_group("team-a")

    assert len(results) == 3
    assert all(result.outcome is NodeOutcome.CHANGED for result in results)

    for host in HOSTS:
        assert "team-a" in cluster.groups[host]


async def test_existing_group_is_not_an_error(make_client):
    cluster = FakeCluster(HOSTS)
    client = make_client(cluster)

    # The group already exists on node2, so that node answers with 400.
    cluster.groups["http://node2"].add("team-a")

    results = await client.create_group("team-a")

    by_host = {result.host: result for result in results}

    assert by_host["http://node2"].outcome is NodeOutcome.ALREADY_DONE
    assert by_host["http://node1"].outcome is NodeOutcome.CHANGED


async def test_unexpected_status_code_fails_the_operation(make_client):
    cluster = FakeCluster(HOSTS, fail_on=["http://node2"], status=403)
    client = make_client(cluster)

    with pytest.raises(ClusterOperationError) as error:
        await client.create_group("team-a")

    assert list(error.value.failures) == ["http://node2"]


async def test_group_exists_uses_the_get_endpoint(make_client):
    cluster = FakeCluster(HOSTS)
    client = make_client(cluster)

    assert await client.group_exists("http://node1", "team-a") is False

    await client.create_group("team-a")

    assert await client.group_exists("http://node1", "team-a") is True