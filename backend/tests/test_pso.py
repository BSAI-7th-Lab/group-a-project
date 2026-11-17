import numpy as np
from swarm import DispatchProblem, PSOConfig, run_pso
from swarm.dummy import make_rush_hour


def make(seed=0, n=15, m=5):
    fp, st = make_rush_hour(n, m, seed)
    return DispatchProblem(st.tasks, st.waiters, fp)


def test_pso_improves_on_initial_swarm():
    r = run_pso(make(), PSOConfig(seed=1))
    assert r.history[-1] < r.history[0]
    assert all(b <= a + 1e-9 for a, b in zip(r.history, r.history[1:]))  # gBest monotone


def test_pso_beats_random_search_same_budget():
    p = make(seed=3)
    r = run_pso(p, PSOConfig(seed=3))
    rng = np.random.default_rng(3)
    lo, hi = (np.array(b) for b in p.bounds())
    best_rand = min(p.evaluate(rng.uniform(lo, hi)) for _ in range(r.evaluations))
    assert r.best_fitness <= best_rand * 1.02


def test_budget_30x20_under_500ms():
    r = run_pso(make(), PSOConfig(particles=30, iters=20, seed=0))
    assert r.evaluations == 30 * 21
    assert r.elapsed_ms < 500


def test_deterministic_with_seed():
    a = run_pso(make(), PSOConfig(seed=42))
    b = run_pso(make(), PSOConfig(seed=42))
    assert a.best_fitness == b.best_fitness


def test_positions_stay_in_bounds():
    p = make()
    r = run_pso(p, PSOConfig(seed=5))
    lo, hi = (np.array(b) for b in p.bounds())
    assert np.all(r.best_x >= lo) and np.all(r.best_x <= hi)


def test_no_waiters_or_tasks_does_not_crash():
    fp, st = make_rush_hour(0, 3, 0)
    assert run_pso(DispatchProblem([], st.waiters, fp)).best_fitness == 0.0
    fp, st = make_rush_hour(4, 0, 0)
    assert run_pso(DispatchProblem(st.tasks, [], fp)).evaluations == 0
