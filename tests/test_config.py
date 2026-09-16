import pytest

from app.config import ClientConfig


def test_hosts_are_stored_as_a_tuple():
    config = ClientConfig(hosts=["http://node1", "http://node2"])

    assert config.hosts == ("http://node1", "http://node2")


def test_empty_host_list_is_rejected():
    with pytest.raises(ValueError):
        ClientConfig(hosts=[])
