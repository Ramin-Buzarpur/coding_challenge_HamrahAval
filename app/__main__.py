import asyncio

from app.client import ClusterClient
from app.config import ClientConfig


async def main():

    config = ClientConfig(
        hosts=[
            "http://node1.example.com",
            "http://node2.example.com",
            "http://node3.example.com"
        ]
    )

    client = ClusterClient(config)

    await client.create_group(
        "example-group"
    )


if __name__ == "__main__":
    asyncio.run(main())