from dataclasses import dataclass


@dataclass(frozen=True)
class ClientConfig:
    """Runtime settings for the cluster client."""

    hosts: tuple[str, ...]

    # Per-request timeout in seconds.
    timeout: float = 5.0

    # How many times a single request is attempted in total (1 = no retry).
    max_attempts: int = 3

    # Backoff between attempts.
    backoff_multiplier: float = 0.5
    backoff_max: float = 5.0

    def __post_init__(self):
        if not self.hosts:
            raise ValueError("at least one host is required")

        # A list is fine as input, but keep it immutable inside the config.
        object.__setattr__(self, "hosts", tuple(self.hosts))
