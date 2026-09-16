from dataclasses import dataclass
from enum import Enum


class OperationStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class NodeResult:
    host: str
    status: OperationStatus
    message: str | None = None