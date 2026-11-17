import copy
from swarm import BoardState, DispatchEngine, PSOConfig
from swarm.dummy import make_rush_hour


def assignment_map(tick):
    return {s["task_id"]: w for w, stops in tick["assignments"].items() for s in stops}


def test_every_task_is_assigned_once():
    fp, st = make_rush_hour()
    t = DispatchEngine(fp, PSOConfig(seed=1)).tick(st)
    assert sorted(assignment_map(t)) == sorted(x.id for x in st.tasks)


def test_second_tick_is_warm_and_cheaper():
    fp, st = make_rush_hour()
    e = DispatchEngine(fp, PSOConfig(seed=1))
    t1, t2 = e.tick(st), e.tick(st)
    assert not t1["warm_start"] and t2["warm_start"]
    assert t2["iterations"] < t1["iterations"]


def test_consecutive_ticks_do_not_flicker():
    fp, st = make_rush_hour()
    e = DispatchEngine(fp, PSOConfig(seed=1))
    prev = assignment_map(e.tick(st))
    for _ in range(4):
        cur = assignment_map(e.tick(st))
        same = sum(prev[k] == cur[k] for k in prev) / len(prev)
        assert same >= 0.9
        prev = cur


def test_new_task_mostly_preserves_existing_plan():
    fp, st = make_rush_hour(12, 4, seed=2)
    e = DispatchEngine(fp, PSOConfig(seed=2))
    before = assignment_map(e.tick(st))
    st2 = copy.deepcopy(st)
    st2.tasks.append(type(st.tasks[0])("task_new", "T5", "deliver_food", age_s=5,
                                       pickup_node="kitchen_pass"))
    after = assignment_map(e.tick(st2))
    kept = sum(before[k] == after[k] for k in before) / len(before)
    assert kept >= 0.7 and "task_new" in after


def test_waiter_leaving_shift_replans():
    fp, st = make_rush_hour(10, 4, seed=4)
    e = DispatchEngine(fp, PSOConfig(seed=4))
    e.tick(st)
    st.waiters = st.waiters[:-1]
    t = e.tick(st)
    assert set(t["assignments"]) == {w.id for w in st.waiters}
    assert len(assignment_map(t)) == 10


def test_tick_under_budget():
    fp, st = make_rush_hour()
    t = DispatchEngine(fp, PSOConfig(seed=0)).tick(st)
    assert t["elapsed_ms"] < 500


def test_no_waiters_returns_unassigned():
    fp, st = make_rush_hour(3, 1, 0)
    st.waiters = []
    t = DispatchEngine(fp).tick(st)
    assert len(t["unassigned"]) == 3


def test_from_board_parses_contract_json():
    now = 1000.0
    board = {
        "now": now,
        "tasks": [
            {"task_id": "t1", "table_id": "T1", "type": "deliver_food", "status": "pending",
             "created_at": 900, "ready_at": 960, "service_s": 20, "load": 1},
            {"task_id": "t2", "table_id": "T2", "type": "bill", "status": "pending",
             "created_at": 940},
            {"task_id": "t3", "table_id": "T2", "type": "bill", "status": "done",
             "created_at": 900},
        ],
        "waiters": [
            {"waiter_id": "W1", "node": "kitchen_pass", "busy_until": 1010, "carrying": 1,
             "capacity": 3, "on_shift": True},
            {"waiter_id": "W2", "node": "bar", "on_shift": False},
        ],
    }
    st = BoardState.from_board(board)
    assert [t.id for t in st.tasks] == ["t1", "t2"]            # done task skipped
    assert st.tasks[0].age_s == 40 and st.tasks[0].pickup_node == "kitchen_pass"
    assert st.tasks[1].age_s == 60
    assert [w.id for w in st.waiters] == ["W1"]                # off-shift skipped
    assert st.waiters[0].busy_s == 10 and st.waiters[0].capacity == 3
