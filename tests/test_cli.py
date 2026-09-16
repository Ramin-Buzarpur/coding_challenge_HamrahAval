from app.__main__ import parse_args, read_hosts


def test_hosts_are_read_from_the_environment(monkeypatch):
    monkeypatch.setenv("NODE_HOSTS", " http://node1/ ,http://node2, ")

    assert read_hosts() == ["http://node1", "http://node2"]


def test_arguments_are_parsed():
    args = parse_args(["create", "team-a", "--timeout", "2"])

    assert args.action == "create"
    assert args.group_id == "team-a"
    assert args.timeout == 2
