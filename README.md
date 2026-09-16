# Cluster API client

A small Python client that creates and deletes groups on every node of a
cluster, and undoes its own work when one of the nodes fails.

This is my solution for the coding challenge. The cluster API itself is not
implemented here, only the client that talks to it.

## The problem

Every node exposes the same REST API, and a group only makes sense if it
exists on all of them. The catch is that the API is unstable: a node can time
out or answer 500 for no particular reason. So "create a group on three nodes"
can easily end up as "created on two nodes, failed on one", which leaves the
cluster in a state nobody asked for.

The client deals with that in two steps: retry the requests that look
temporary, and if a node still refuses, remove whatever the other nodes
already did before raising the error.

## How to use it

```bash
pip install -r requirements.txt

export NODE_HOSTS="http://node1.example.com,http://node2.example.com,http://node3.example.com"

python -m app create my-group
python -m app delete my-group
```

As a module:

```python
import asyncio
from app.client import ClusterClient
from app.config import ClientConfig
from app.exceptions import ClusterOperationError


async def main():
    config = ClientConfig(
        hosts=["http://node1.example.com", "http://node2.example.com"],
        timeout=5.0,
        max_attempts=3,
    )

    async with ClusterClient(config) as client:
        try:
            await client.create_group("my-group")
        except ClusterOperationError as error:
            print("failed on:", list(error.failures))
            print("rolled back:", error.rolled_back)
            print("needs manual cleanup:", error.rollback_failures)


asyncio.run(main())
```

`create_group` and `delete_group` either succeed on every node or raise
`ClusterOperationError`. There is no partial success.

### Settings

| Variable | Flag | Default | What it does |
| --- | --- | --- | --- |
| `NODE_HOSTS` | - | three example hosts | Comma separated base URLs |
| `REQUEST_TIMEOUT` | `--timeout` | `5` | Per request timeout in seconds |
| `MAX_ATTEMPTS` | `--attempts` | `3` | Total attempts per request, so 3 means 1 try + 2 retries |
| `LOG_LEVEL` | - | `INFO` | Standard logging levels |

Exit codes: `0` all good, `1` the operation failed but the rollback cleaned
up, `2` the rollback failed too and somebody has to look at the cluster.

## How it works

```
app/
├── __main__.py     CLI entry point
├── client.py       cluster logic: fan out, decide, roll back
├── http_client.py  one request with timeout and retries
├── config.py       settings
├── models.py       result of a single node
├── exceptions.py   error types
└── logger.py       logging setup
```

`HttpClient` knows nothing about groups, it only sends a request and retries
it when the failure looks temporary. `ClusterClient` knows nothing about
httpx, it only decides what to do with the results. Keeping them apart made
the tests much easier to write.

The flow for create looks like this:

```
POST /v1/group/ to all nodes in parallel
         │
         ├── all nodes accepted        -> done
         │
         └── at least one failed
                   │
                   ├── DELETE on the nodes we actually created it on
                   └── raise ClusterOperationError
```

Delete is the mirror image: if one node fails, the groups that were already
deleted get recreated.

### Retries

A request is retried when it times out, when the connection breaks, or when
the node answers 5xx. Backoff is exponential with a bit of jitter, so three
nodes that failed at the same moment do not come back at the exact same
moment either.

A 4xx is never retried, because trying the same bad request again will not
produce a different answer.

## Assumptions

The API docs left a few things open, so these are my calls.

**400 on create means the group is already there.** The docs say "perhaps the
object exists", so I treat it as an acceptable outcome rather than a failure.
It is not perfect, a real bad request also returns 400, and with this API
there is no way to tell the two apart from the status code alone. The GET
endpoint could be used to check, but that is one extra round trip per node on
every call, so I decided against it and exposed `group_exists()` as a helper
instead.

**A node that answered 400 is not rolled back.** This one matters more than it
looks. If the group already existed on node2 before I started, and node3 then
fails, deleting it from node2 would destroy something I never created. Only
the nodes that answered 201 get cleaned up. Same logic for delete: a node that
answered 404 had nothing to restore.

**404 on delete is fine.** The group is gone, which is what was asked for.

**Rollback is best effort.** If the rollback itself fails there is nothing
sensible left to do automatically, so it is logged at CRITICAL and reported
through `ClusterOperationError.rollback_failures`. In a real system this is
where you would page someone or let a reconciliation loop fix the drift.

**Requests go to all nodes in parallel.** With three nodes it does not matter
much, but doing it sequentially would mean the total timeout grows with the
number of nodes for no reason.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

The tests use `httpx.MockTransport`, so they go through the real `HttpClient`
(URL building, request body, retry logic) without any network. `FakeCluster`
in `tests/conftest.py` is a small in-memory cluster that remembers which
groups exist on which node, which makes it possible to assert on the final
state instead of on the calls.

What is covered: create and delete on every node, 400 and 404 handling, retry
on timeout and on 500, no retry on 400, rollback when the first node fails and
when the last one does, not rolling back a group that already existed, and
rollback that fails.

The first one is the interesting case. Because the requests run in parallel, a
failure on node1 says nothing about node2 and node3, and it is easy to write
a rollback that only cleans up the nodes before the failing one. That is
exactly what `test_create_is_rolled_back_when_the_first_node_fails` checks.

## Docker

```bash
docker build -t cluster-api-client .

docker run --rm -e NODE_HOSTS="http://node1:8000,http://node2:8000" \
  cluster-api-client create my-group
```

The image runs as a non root user and only contains `app/`, the tests and dev
files stay out.

### Trying it against fake nodes

There is a throwaway server in `dev/fake_node.py` that implements the three
endpoints in memory and returns 500 about 30% of the time. It is not part of
the solution, it just makes the retry and rollback behaviour visible:

```bash
docker compose up --build
```

You should see retry warnings in the log, and either a successful create or a
rollback, depending on how unlucky the run was.

## Kubernetes

`manifests/` has a ConfigMap and a Job. A Job rather than a Deployment,
because the client does one thing and exits, it does not serve traffic.

```bash
kubectl apply -f manifests/
kubectl logs -l app.kubernetes.io/name=cluster-api-client
```

The node list lives in the ConfigMap so the image does not have to be rebuilt
to point at a different cluster. The Job has resource requests and limits, a
deadline, and runs as non root with a read only root filesystem.

`backoffLimit: 3` is safe here because a failed run has already rolled itself
back, so a retry starts from a clean state. Change `args` in the Job to run
`delete` instead of `create`.

## What I would do next

- The rollback is not atomic. If the process is killed between the failed
  create and the rollback, the cluster stays inconsistent. A real fix is a
  reconciliation job that periodically compares the nodes, or writing the
  intent somewhere durable before touching any node.
- No limit on concurrency. Three nodes is fine, three hundred would want a
  semaphore.
- No circuit breaker. A node that is down still eats the full retry budget on
  every single call.
- Only `groupId` is supported, because that is all the API has. If groups grow
  more fields, `NodeResult` and the payload building should move into a proper
  serializer.
