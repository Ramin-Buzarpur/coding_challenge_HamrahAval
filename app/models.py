from dataclasses import dataclass
from enum import Enum


class NodeOutcome(str, Enum):
    # The node changed state because of us, so a rollback has to undo it.
    CHANGED = "changed"

    # The node was already in the state we wanted. Nothing to undo.
    ALREADY_DONE = "already_done"


@dataclass(frozen=True)
class NodeResult:
    host: str
    outcome: NodeOutcome
    status_code: int

    @property
    def needs_rollback(self) -> bool:
        return self.outcome is NodeOutcome.CHANGED
