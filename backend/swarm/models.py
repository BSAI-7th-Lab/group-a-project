"""Plain data models used by the swarm. Times are seconds relative to 'now'."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

TASK_TYPES = ("deliver_food", "deliver_drink", "bill", "confirm", "clear")
DISPATCHABLE_STATUS = ("pending", "delayed")


@dataclass(frozen=True)
class Task:
    id: str
    table_id: str                      # floorplan node id of the destination
    type: str                          # one of TASK_TYPES
    age_s: float = 0.0                 # seconds the guest has already been waiting
    service_s: float = 30.0            # time spent at the table
    load: int = 1                      # carrying slots used (plates, trays)
    pickup_node: Optional[str] = None  # e.g. "kitchen_pass" for hot food

    @property
    def is_hot(self) -> bool:
        return self.type == "deliver_food"

    @property
    def is_bill(self) -> bool:
        return self.type == "bill"


@dataclass(frozen=True)
class Waiter:
    id: str
    node: str                          # inferred position (node id)
    busy_s: float = 0.0                # seconds until the current task is finished
    carrying: int = 0                  # slots already in hand
    capacity: int = 4                  # max slots


@dataclass
class BoardState:
    """Snapshot of the Restaurant State Board that one tick plans against."""
    tasks: list[Task] = field(default_factory=list)
    waiters: list[Waiter] = field(default_factory=list)
    now: float = 0.0

    @classmethod
    def from_board(cls, board: dict) -> "BoardState":
        """Parse the JSON shape defined in docs/contracts.md (WaiterTask + Waiter)."""
        now = float(board["now"])
        tasks = []
        for t in board.get("tasks", []):
            if t.get("status", "pending") not in DISPATCHABLE_STATUS:
                continue
            since = t.get("ready_at") or t["created_at"]
            tasks.append(Task(
                id=t["task_id"],
                table_id=t["table_id"],
                type=t["type"],
                age_s=max(0.0, now - float(since)),
                service_s=float(t.get("service_s", 30.0)),
                load=int(t.get("load", 1)),
                pickup_node=t.get("pickup_node")
                or ("kitchen_pass" if t["type"] == "deliver_food" else None),
            ))
        waiters = []
        for w in board.get("waiters", []):
            if not w.get("on_shift", True):
                continue
            busy_until = w.get("busy_until")
            waiters.append(Waiter(
                id=w["waiter_id"],
                node=w["node"],
                busy_s=max(0.0, float(busy_until) - now) if busy_until else 0.0,
                carrying=int(w.get("carrying", 0)),
                capacity=int(w.get("capacity", 4)),
            ))
        return cls(tasks=tasks, waiters=waiters, now=now)


@dataclass(frozen=True)
class Weights:
    completion: float = 2.0
    hot_wait: float = 5.0
    bill_wait: float = 1.5
    walk: float = 1.0
    imbalance: float = 3.0
    capacity_violation: float = 1000.0
    hysteresis: float = 10.0           # bonus per task kept with the same waiter
