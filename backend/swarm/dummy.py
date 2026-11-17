"""Dummy rush-hour data for tests, demos and (later) the simulation mode."""
from __future__ import annotations

import random

from .floorplan import Floorplan
from .models import BoardState, Task, Waiter


def make_floorplan(cols: int = 4, rows: int = 3, spacing: float = 4.0) -> Floorplan:
    nodes = {"kitchen_pass": (0.0, 0.0), "bar": (0.0, 12.0), "entrance": (20.0, 0.0)}
    k = 1
    for r in range(rows):
        for c in range(cols):
            nodes[f"T{k}"] = (4.0 + c * spacing, 3.0 + r * spacing)
            k += 1
    return Floorplan(nodes)


def make_rush_hour(n_tasks: int = 15, n_waiters: int = 5, seed: int = 0,
                   fp: Floorplan | None = None) -> tuple[Floorplan, BoardState]:
    rng = random.Random(seed)
    fp = fp or make_floorplan()
    tables = [n for n in fp.ids if n.startswith("T")]
    types = ["deliver_food"] * 5 + ["deliver_drink"] * 3 + ["bill"] * 3 + ["confirm", "clear"]
    svc = {"deliver_food": 20, "deliver_drink": 15, "bill": 40, "confirm": 15, "clear": 25}
    tasks = []
    for i in range(n_tasks):
        ty = rng.choice(types)
        tasks.append(Task(
            id=f"task_{i+1}", table_id=rng.choice(tables), type=ty,
            age_s=rng.uniform(0, 90), service_s=svc[ty],
            load=0 if ty == "clear" else 1,
            pickup_node="kitchen_pass" if ty == "deliver_food" else
                        ("bar" if ty == "deliver_drink" else None)))
    stations = ["kitchen_pass", "bar", "entrance"] + tables
    waiters = [Waiter(id=f"W{j+1}", node=rng.choice(stations),
                      busy_s=rng.choice([0, 0, 10, 25]),
                      carrying=rng.choice([0, 0, 1]), capacity=4)
               for j in range(n_waiters)]
    return fp, BoardState(tasks=tasks, waiters=waiters, now=1_700_000_000.0)
