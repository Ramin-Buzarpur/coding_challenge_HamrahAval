import argparse
import asyncio
import os
import sys

from app.client import ClusterClient
from app.config import ClientConfig
from app.exceptions import ClusterOperationError
from app.logger import get_logger, setup_logging

logger = get_logger("app")

DEFAULT_HOSTS = "http://node1.example.com,http://node2.example.com,http://node3.example.com"


def read_hosts() -> list[str]:
    raw = os.getenv("NODE_HOSTS", DEFAULT_HOSTS)
    return [host.strip().rstrip("/") for host in raw.split(",") if host.strip()]


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="python -m app",
        description="Create or delete a group on every node of the cluster.",
    )

    parser.add_argument("action", choices=["create", "delete"])
    parser.add_argument("group_id")
    parser.add_argument(
        "--timeout",
        type=float,
        default=float(os.getenv("REQUEST_TIMEOUT", "5")),
        help="per request timeout in seconds (default: 5)",
    )
    parser.add_argument(
        "--attempts",
        type=int,
        default=int(os.getenv("MAX_ATTEMPTS", "3")),
        help="how many times one request is attempted (default: 3)",
    )

    return parser.parse_args(argv)


async def run(args) -> int:
    config = ClientConfig(
        hosts=read_hosts(),
        timeout=args.timeout,
        max_attempts=args.attempts,
    )

    async with ClusterClient(config) as client:
        try:
            if args.action == "create":
                await client.create_group(args.group_id)
            else:
                await client.delete_group(args.group_id)

        except ClusterOperationError as error:
            logger.error("%s", error)

            # Exit code 2 means the cluster still needs manual cleanup, so a
            # Kubernetes Job retry would not help.
            return 2 if error.rollback_failures else 1

    logger.info("done")
    return 0


def main() -> int:
    setup_logging()
    return asyncio.run(run(parse_args()))


if __name__ == "__main__":
    sys.exit(main())
