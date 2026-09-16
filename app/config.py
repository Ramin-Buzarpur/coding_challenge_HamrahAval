from dataclasses import dataclass


@dataclass(frozen=True)
class ClientConfig:
    hosts: list[str]
    timeout: float = 5.0
    max_retries: int = 3