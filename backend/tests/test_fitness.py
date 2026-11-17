import pytest
from swarm import DispatchProblem, Floorplan, Task, Waiter, Weights


@pytest.fixture
def fp():
    return Floorplan({"pass": (0, 0), "T1": (10, 0), "T2": (0, 10), "T3": (10, 10)})


def prob(tasks, waiters, fp, **kw):
    return DispatchProblem(tasks, waiters, fp, **kw)


def test_decode_round_and_modulo(fp):
    tasks = [Task(f"t{i}", "T1", "confirm") for i in range(5)]
    ws = [Waiter(f"W{i}", "pass") for i in range(3)]
    p = prob(tasks, ws, fp)
    x = [2.34, 0.71, 1.55, 2.89, 0.12] + [0.5] * 5
    assign, viol = p.decode(x)
    assert assign == [2, 1, 2, 0, 0] and viol == 0      # matches the proposal example


def test_manhattan_walk_time(fp):
    assert fp.walk_time("pass", "T1") == pytest.approx(10 * 1.3)
    assert fp.walk_time("T1", "T2") == pytest.approx(20 * 1.3)


def test_nearer_waiter_scores_better(fp):
    tasks = [Task("t1", "T1", "deliver_drink")]
    ws = [Waiter("near", "T1"), Waiter("far", "T2")]
    p = prob(tasks, ws, fp)
    assert p.evaluate([0.0, 0.5]) < p.evaluate([1.0, 0.5])


def test_hot_food_penalised_more_than_drink(fp):
    ws = [Waiter("W", "pass")]
    hot = prob([Task("t", "T1", "deliver_food", age_s=60)], ws, fp)
    cold = prob([Task("t", "T1", "deliver_drink", age_s=60)], ws, fp)
    assert hot.evaluate([0, 0.5]) > cold.evaluate([0, 0.5])


def test_hot_dish_goes_first(fp):
    tasks = [Task("drink", "T2", "deliver_drink"), Task("steak", "T1", "deliver_food", age_s=30)]
    p = prob(tasks, [Waiter("W", "pass")], fp)
    steak_first = p.evaluate([0, 0, 0.9, 0.1])
    drink_first = p.evaluate([0, 0, 0.1, 0.9])
    assert steak_first < drink_first


def test_ordering_key_controls_sequence(fp):
    tasks = [Task("a", "T1", "confirm"), Task("b", "T2", "confirm")]
    p = prob(tasks, [Waiter("W", "pass")], fp)
    plan = p.build_plan([0, 0, 0.9, 0.1])
    assert [s["task_id"] for s in plan.assignments["W"]] == ["b", "a"]


def test_capacity_repair_moves_overflow(fp):
    tasks = [Task(f"t{i}", "T1", "deliver_food") for i in range(4)]
    ws = [Waiter("W1", "pass", capacity=2), Waiter("W2", "pass", capacity=2)]
    p = prob(tasks, ws, fp)
    assign, viol = p.decode([0.0] * 4 + [0.5] * 4)       # everyone wants W1
    assert viol == 0 and assign.count(0) == 2 and assign.count(1) == 2


def test_unrepairable_capacity_is_penalised(fp):
    tasks = [Task(f"t{i}", "T1", "deliver_food") for i in range(3)]
    p = prob(tasks, [Waiter("W1", "pass", capacity=2)], fp)
    _, viol = p.decode([0.0] * 3 + [0.5] * 3)
    assert viol == 1
    assert p.evaluate([0.0] * 6) > 1000


def test_imbalance_term(fp):
    tasks = [Task(f"t{i}", "T1", "confirm") for i in range(4)]
    ws = [Waiter("W1", "T1"), Waiter("W2", "T1")]
    w = Weights(completion=0, hot_wait=0, bill_wait=0, walk=0, hysteresis=0)
    p = prob(tasks, ws, fp, weights=w)
    even = p.evaluate([0, 0, 1, 1] + [0.5] * 4)
    lopsided = p.evaluate([0, 0, 0, 0] + [0.5] * 4)
    assert even < lopsided


def test_hysteresis_rewards_keeping_assignment(fp):
    tasks = [Task("t1", "T1", "confirm")]
    ws = [Waiter("W1", "T1"), Waiter("W2", "T1")]
    p = prob(tasks, ws, fp, prev_assignment={"t1": "W2"})
    assert p.evaluate([1.0, 0.5]) < p.evaluate([0.0, 0.5])


def test_busy_waiter_delays_arrival(fp):
    tasks = [Task("t1", "T1", "bill")]
    free = prob(tasks, [Waiter("W", "T1", busy_s=0)], fp)
    busy = prob(tasks, [Waiter("W", "T1", busy_s=60)], fp)
    assert busy.evaluate([0, 0.5]) > free.evaluate([0, 0.5])


def test_empty_problem_is_safe(fp):
    p = prob([], [Waiter("W", "pass")], fp)
    assert p.evaluate([]) == 0.0
    assert p.build_plan([]).assignments == {"W": []}
