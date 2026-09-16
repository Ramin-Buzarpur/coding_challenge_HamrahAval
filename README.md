# Cluster API Client

A small client module for managing group objects across multiple cluster nodes.

## About this project

This project was created as part of a coding challenge.

The goal was to build a client that can create and delete groups on multiple nodes while keeping the cluster state consistent when some requests fail.

Each node exposes the same REST API, but the API is not guaranteed to be stable. Because of that, the client needs to handle cases like timeouts, connection errors, and partial failures.

The main focus of the implementation is:
- sending requests to multiple nodes
- handling failures
- rolling back successful changes when needed
- keeping the code simple and easy to maintain

---

## Project structure


cluster-api-client/

├── app/
│ ├── client.py
│ ├── http_client.py
│ ├── config.py
│ ├── models.py
│ ├── exceptions.py
│ ├── logger.py
│ └── main.py
│
├── tests/
│
├── manifests/
│ └── job.yaml
│
├── Dockerfile
├── requirements.txt
└── README.md


---

## Design overview

The project is divided into a few simple layers.

`ClusterClient`  
Handles the main workflow. It knows how to create and delete groups across nodes and when rollback is required.

`HttpClient`  
Responsible only for HTTP communication with nodes.

`Config`  
Keeps runtime configuration such as node addresses and request settings.

The idea was to keep the business logic separate from the HTTP layer so that each part can be tested independently.

---

## Handling failures

The most important part of this task is dealing with partial failures.

For example, during a create operation:


Node 1 -> success
Node 2 -> success
Node 3 -> failed


The client will remove the created objects from Node 1 and Node 2 to avoid leaving the cluster in an inconsistent state.

The same approach is used for delete operations. If deleting from one of the nodes fails after some nodes have already been updated, the client tries to restore the previous state.

---

## Assumptions

Some behaviors were not completely defined by the API documentation, so the following assumptions were made.

### Create

The API documentation mentions that HTTP 400 can happen when the object already exists.

For this reason, an existing object is considered an acceptable state for create operations.

### Delete

If a delete request returns 404, the desired state is already achieved because the object does not exist.

### Rollback failure

Rollback operations are best-effort.

If rollback itself fails, the error is logged. In a production environment, this situation would usually require a reconciliation process or alerting mechanism.

---

## Running the project

Install dependencies:

```bash
pip install -r requirements.txt

Run tests:

pytest

Run the application:

python -m app

Node addresses can be configured using the NODE_HOSTS environment variable.

Example:

export NODE_HOSTS=http://node1.example.com,http://node2.example.com
Docker

Build the image:

docker build -t cluster-api-client .

Run:

docker run cluster-api-client

The container executes the client entry point defined in app/__main__.py.

Kubernetes

A simple Kubernetes Job manifest is included.

The client is deployed as a Job because it performs an operation and finishes. It is not a long-running service that receives incoming traffic.

Apply the manifest:

kubectl apply -f manifests/job.yaml