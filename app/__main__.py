import asyncio
import os

from app.client import ClusterClient
from app.config import ClientConfig


def get_hosts() -> list[str]:
    hosts = os.getenv(
        "NODE_HOSTS",
        "http://node1.example.com,http://node2.example.com,http://node3.example.com"
    )

    return [
        host.strip()
        for host in hosts.split(",")
        if host.strip()
    ]


async def main():

    config = ClientConfig(
        hosts=get_hosts()
    )

    client = ClusterClient(config)

    await client.create_group(
        "example-group"
    )


if __name__ == "__main__":
    asyncio.run(main())