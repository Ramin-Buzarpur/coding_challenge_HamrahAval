import pytest

from app.exceptions import ClusterOperationError
from app.models import NodeOutcome
from tests.conftest import FakeCluster

HOSTS = ["http://node1", "http://node2"]


async def test_group_is_deleted_from_every_node(make_client):
    cluster = FakeCluster(HOSTS)
    client = make_client(cluster)

    await client.create_group("team-a")
    await client.delete_group("team-a")

    for host in HOSTS:
        assert cluster.groups[host] == set()


async def test_missing_group_is_not_an_error(make_client):
    cluster = FakeCluster(HOSTS)
    client = make_client(cluster)

    results = await client.delete_group("never-created")

    assert all(result.outcome is NodeOutcome.ALREADY_DONE for result in results)


async def test_delete_failure_is_reported(make_client):
    cluster = FakeCluster(HOSTS, fail_on=["http://node2"], status=403)
    client = make_client(cluster)

    with pytest.raises(ClusterOperationError):
        await client.delete_group("team-a")
