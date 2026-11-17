"""Particle encoding + fitness for waiter dispatch.

Particle x has length 2N:
  x[:N]   assignment values  -> waiter index = round(x) mod M
  x[N:]   order keys         -> within a waiter, tasks sorted ascending by key
Lower fitness is better.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Sequence

from .floorplan import Floorplan
from .models import Task, Waiter, Weights


@dataclass
class Plan:
    assignments: dict[str, list[dict]]      # waiter_id -> ordered stops
    metrics: dict
    fitness: float


class DispatchProblem:
    def __init__(self, tasks: Sequence[Task], waiters: Sequence[Waiter],
                 floorplan: Floorplan, weights: Weights = Weights(),
                 prev_assignment: Optional[dict[str, str]] = None):
        self.tasks = list(tasks)
        self.waiters = list(waiters)
        self.fp = floorplan
        self.w = weights
        self.n = len(self.tasks)
        self.m = len(self.waiters)
        self.dim = 2 * self.n
        self.prev = prev_assignment or {}
        ix = floorplan.index
        self._dest = [ix[t.table_id] for t in self.tasks]
        self._pick = [ix[t.pickup_node] if t.pickup_node else -1 for t in self.tasks]
        self._wpos = [ix[w.node] for w in self.waiters]
        self._prev_w = [
            next((j for j, w in enumerate(self.waiters) if w.id == self.prev.get(t.id)), -1)
            for t in self.tasks
        ]

    # ---- search-space bounds (used by PSO) ----
    def bounds(self):
        lo = [-0.5] * self.n + [0.0] * self.n
        hi = [self.m - 0.5 - 1e-9] * self.n + [1.0] * self.n
        return lo, hi

    # ---- decode + repair ----
    def decode(self, x: Sequence[float]) -> tuple[list[int], int]:
        """Return (waiter index per task, #unrepairable capacity violations)."""
        m, n = self.m, self.n
        assign = [int(math.floor(x[i] + 0.5)) % m for i in range(n)]
        room = [w.capacity - w.carrying for w in self.waiters]
        used = [0] * m
        for i, a in enumerate(assign):
            used[a] += self.tasks[i].load
        for i in range(n):                                  # repair operator
            a = assign[i]
            ld = self.tasks[i].load
            if used[a] > room[a]:
                best = min(range(m), key=lambda j: used[j] - room[j])
                if best != a and used[best] + ld <= room[best]:
                    used[a] -= ld
                    used[best] += ld
                    assign[i] = best
        # whatever is still over capacity cannot be repaired -> hard penalty
        violations = sum(max(0, used[j] - room[j]) for j in range(m))
        return assign, violations

    # ---- simulation ----
    def _simulate(self, x: Sequence[float]):
        n, m = self.n, self.m
        assign, violations = self.decode(x)
        per: list[list[int]] = [[] for _ in range(m)]
        for i, a in enumerate(assign):
            per[a].append(i)
        mat = self.fp.matrix
        completion = hot = bill = walk = 0.0
        ends = []
        stops: list[list[tuple[int, float]]] = [[] for _ in range(m)]
        for j in range(m):
            wt = self.waiters[j]
            t, pos = wt.busy_s, self._wpos[j]
            for i in sorted(per[j], key=lambda k: x[n + k]):
                task = self.tasks[i]
                travel = 0.0
                if self._pick[i] >= 0:
                    travel += mat[pos][self._pick[i]]
                    pos = self._pick[i]
                travel += mat[pos][self._dest[i]]
                pos = self._dest[i]
                t += travel
                arrive = t
                t += task.service_s
                walk += travel
                completion = max(completion, t)
                if task.is_hot:
                    hot += task.age_s + arrive
                elif task.is_bill:
                    bill += task.age_s + arrive
                stops[j].append((i, arrive))
            ends.append(t)
        mean = sum(ends) / m
        imbalance = math.sqrt(sum((e - mean) ** 2 for e in ends) / m)
        kept = sum(1 for i in range(n) if self._prev_w[i] == assign[i])
        return dict(assign=assign, stops=stops, completion=completion, hot=hot,
                    bill=bill, walk=walk, imbalance=imbalance,
                    violations=violations, kept=kept)

    def _score(self, s: dict) -> float:
        w = self.w
        return (w.completion * s["completion"] + w.hot_wait * s["hot"]
                + w.bill_wait * s["bill"] + w.walk * s["walk"]
                + w.imbalance * s["imbalance"]
                + w.capacity_violation * s["violations"]
                - w.hysteresis * s["kept"])

    def evaluate(self, x: Sequence[float]) -> float:
        if self.n == 0 or self.m == 0:
            return 0.0
        return self._score(self._simulate(x))

    def build_plan(self, x: Sequence[float]) -> Plan:
        if self.n == 0 or self.m == 0:
            return Plan({w.id: [] for w in self.waiters},
                        dict(completion_s=0, hot_wait_s=0, bill_wait_s=0,
                             walk_s=0, imbalance=0, capacity_violations=0), 0.0)
        s = self._simulate(x)
        out = {w.id: [] for w in self.waiters}
        for j, lst in enumerate(s["stops"]):
            for i, arrive in lst:
                t = self.tasks[i]
                out[self.waiters[j].id].append(dict(
                    task_id=t.id, table_id=t.table_id, type=t.type,
                    eta_s=round(arrive, 1)))
        metrics = dict(completion_s=round(s["completion"], 1),
                       hot_wait_s=round(s["hot"], 1),
                       bill_wait_s=round(s["bill"], 1),
                       walk_s=round(s["walk"], 1),
                       imbalance=round(s["imbalance"], 2),
                       capacity_violations=s["violations"])
        return Plan(out, metrics, self._score(s))
