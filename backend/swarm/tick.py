"""Tick loop: warm start from the previous gBest + hysteresis, emits a SwarmTick dict."""
from __future__ import annotations

import time
from typing import Optional

import numpy as np

from .floorplan import Floorplan
from .fitness import DispatchProblem
from .models import BoardState, Weights
from .pso import PSOConfig, run_pso


class DispatchEngine:
    def __init__(self, floorplan: Floorplan, cfg: PSOConfig = PSOConfig(),
                 warm_iters: int = 10, weights: Weights = Weights(),
                 warm_seeds: int = 6, switch_margin: float = 0.03):
        self.fp = floorplan
        self.cfg = cfg
        self.warm_iters = warm_iters
        self.weights = weights
        self.warm_seeds = warm_seeds
        self.switch_margin = switch_margin   # new plan must beat old by this fraction
        self.tick_id = 0
        self._prev_assign: dict[str, str] = {}   # task_id -> waiter_id
        self._prev_key: dict[str, float] = {}    # task_id -> order key

    def reset(self):
        self._prev_assign, self._prev_key = {}, {}

    def _seeds(self, problem: DispatchProblem) -> Optional[np.ndarray]:
        if not self._prev_assign or problem.n == 0 or problem.m == 0:
            return None
        rng = np.random.default_rng(self.cfg.seed)
        widx = {w.id: j for j, w in enumerate(problem.waiters)}
        base = np.empty(problem.dim)
        for i, t in enumerate(problem.tasks):
            base[i] = widx.get(self._prev_assign.get(t.id),
                               rng.uniform(-0.5, problem.m - 0.5))
            base[problem.n + i] = self._prev_key.get(t.id, rng.random())
        seeds = [base]
        for _ in range(self.warm_seeds - 1):
            noisy = base.copy()
            noisy[:problem.n] += rng.normal(0, 0.3, problem.n)
            noisy[problem.n:] += rng.normal(0, 0.05, problem.n)
            seeds.append(noisy)
        return np.array(seeds)

    def tick(self, state: BoardState) -> dict:
        t0 = time.perf_counter()
        self.tick_id += 1
        problem = DispatchProblem(state.tasks, state.waiters, self.fp,
                                  self.weights, self._prev_assign)
        seeds = self._seeds(problem)
        warm = seeds is not None
        cfg = self.cfg
        if warm:
            cfg = PSOConfig(**{**cfg.__dict__, "iters": self.warm_iters})
        res = run_pso(problem, cfg, seeds)
        best_x = res.best_x
        if warm and problem.n:
            f_prev = problem.evaluate(seeds[0])          # yesterday's plan, today's state
            if res.best_fitness > f_prev - self.switch_margin * abs(f_prev):
                best_x = seeds[0]                        # not worth changing: no flicker
        plan = problem.build_plan(best_x)

        self._prev_assign, self._prev_key = {}, {}
        if problem.n and problem.m:
            assign, _ = problem.decode(best_x)
            for i, t in enumerate(problem.tasks):
                self._prev_assign[t.id] = problem.waiters[assign[i]].id
                self._prev_key[t.id] = float(best_x[problem.n + i])

        return {
            "tick_id": self.tick_id,
            "ts": state.now,
            "warm_start": warm,
            "assignments": plan.assignments,
            "unassigned": [] if problem.m else [t.id for t in problem.tasks],
            "metrics": plan.metrics,
            "fitness": round(plan.fitness, 2),
            "iterations": cfg.iters,
            "evaluations": res.evaluations,
            "elapsed_ms": round((time.perf_counter() - t0) * 1000, 1),
        }
