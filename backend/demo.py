"""Run:  python demo.py   -> two ticks on dummy rush-hour data."""
import json
from swarm import DispatchEngine, PSOConfig
from swarm.dummy import make_rush_hour

fp, state = make_rush_hour(n_tasks=15, n_waiters=5, seed=7)
engine = DispatchEngine(fp, PSOConfig(seed=7))
for i in (1, 2):
    tick = engine.tick(state)
    print(f"--- tick {i}  warm={tick['warm_start']}  {tick['elapsed_ms']} ms  fitness={tick['fitness']}")
    for w, stops in tick["assignments"].items():
        print(f"  {w}: " + " -> ".join(f"{s['table_id']}:{s['type']}" for s in stops))
    print("  metrics:", json.dumps(tick["metrics"]))
