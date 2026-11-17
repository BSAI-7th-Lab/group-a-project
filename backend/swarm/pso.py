"""Vectorized PSO loop (NumPy for the swarm math, problem.evaluate for fitness)."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from .fitness import DispatchProblem


@dataclass
class PSOConfig:
    particles: int = 30
    iters: int = 20
    w_start: float = 0.7
    w_end: float = 0.4
    c1: float = 1.5
    c2: float = 2.0
    seed: Optional[int] = None


@dataclass
class PSOResult:
    best_x: np.ndarray
    best_fitness: float
    history: list[float] = field(default_factory=list)   # gBest per iteration
    evaluations: int = 0
    elapsed_ms: float = 0.0


def run_pso(problem: DispatchProblem, cfg: PSOConfig = PSOConfig(),
            seeds: Optional[np.ndarray] = None) -> PSOResult:
    t0 = time.perf_counter()
    rng = np.random.default_rng(cfg.seed)
    D = problem.dim
    if D == 0 or problem.m == 0:
        return PSOResult(np.zeros(0), 0.0, [0.0], 0, 0.0)

    lo, hi = (np.array(b) for b in problem.bounds())
    span = hi - lo
    X = rng.uniform(lo, hi, size=(cfg.particles, D))
    if seeds is not None and len(seeds):
        k = min(len(seeds), cfg.particles)
        X[:k] = np.clip(seeds[:k], lo, hi)
    V = rng.uniform(-0.1, 0.1, size=(cfg.particles, D)) * span
    vmax = 0.5 * span

    fit = np.array([problem.evaluate(x) for x in X])
    evals = cfg.particles
    pbest, pbest_f = X.copy(), fit.copy()
    g = int(np.argmin(pbest_f))
    gbest, gbest_f = pbest[g].copy(), float(pbest_f[g])
    history = [gbest_f]

    for it in range(cfg.iters):
        w = cfg.w_start + (cfg.w_end - cfg.w_start) * it / max(1, cfg.iters - 1)
        r1 = rng.random((cfg.particles, D))
        r2 = rng.random((cfg.particles, D))
        V = w * V + cfg.c1 * r1 * (pbest - X) + cfg.c2 * r2 * (gbest - X)
        V = np.clip(V, -vmax, vmax)
        X = np.clip(X + V, lo, hi)
        fit = np.array([problem.evaluate(x) for x in X])
        evals += cfg.particles
        better = fit < pbest_f
        pbest[better], pbest_f[better] = X[better], fit[better]
        g = int(np.argmin(pbest_f))
        if pbest_f[g] < gbest_f:
            gbest, gbest_f = pbest[g].copy(), float(pbest_f[g])
        history.append(gbest_f)

    return PSOResult(gbest, gbest_f, history, evals,
                     (time.perf_counter() - t0) * 1000)
