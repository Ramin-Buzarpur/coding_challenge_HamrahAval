import logging
import os
import sys

_configured = False


def setup_logging(level: str | None = None) -> None:
    """Configure logging once, at process start."""
    global _configured

    if _configured:
        return

    logging.basicConfig(
        level=level or os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
        stream=sys.stdout,
    )

    # httpx logs every request at INFO, which drowns out our own lines.
    logging.getLogger("httpx").setLevel(logging.WARNING)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
