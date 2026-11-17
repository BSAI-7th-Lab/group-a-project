# SwarmDining — JSON State & API Contracts (v0.1 DRAFT)

Owner: MD (Swarm) · Reviewers: AM (Backend), MA (Frontend)
Status: **proposed — all three sign off before Week 2 starts.** Change a field name only via PR to this file.

## Conventions
- All field names `snake_case`. All times are **epoch seconds (float, UTC)**; durations end in `_s`.
- IDs are strings. **Table ids double as floorplan node ids** (`"T4"`). Fixed nodes: `"kitchen_pass"`, `"bar"`, `"entrance"`.
- Enums are lowercase strings.
- The swarm only *reads* Orders/Tables/Waiters/Tasks from the blackboard and only *writes* `SwarmTick`.

## 1. Order
```json
{
  "order_id": "ord_0192",
  "table_id": "T4",
  "status": "received",
  "created_at": 1700000000.0,
  "items": [
    {"item_id": "steak", "name": "Ribeye", "qty": 1, "station": "grill", "hot": true, "status": "queued"},
    {"item_id": "cola",  "name": "Cola",   "qty": 2, "station": "bar",   "hot": false, "status": "queued"}
  ],
  "total": 34.5
}
```
`order.status`: `received | cooking | plated | served | paid | cancelled`
`item.status`: `queued | cooking | plated | served`
`item.station`: `grill | fryer | oven | stove | bar | cold`

## 2. Table
```json
{
  "table_id": "T4",
  "seats": 4,
  "status": "occupied",
  "x": 8.0, "y": 7.0,
  "party_size": 3,
  "seated_at": 1699999000.0,
  "predicted_free_at": null
}
```
`table.status`: `free | reserved | occupied | needs_cleaning`
(`predicted_free_at` stays `null` until the future dwell-time model exists.)

## 3. Waiter
```json
{
  "waiter_id": "W2",
  "node": "kitchen_pass",
  "busy_until": 1700000012.0,
  "carrying": 1,
  "capacity": 4,
  "on_shift": true
}
```
- `node` = **inferred** position (set to the table/node of the last completed task; never GPS).
- `busy_until` = epoch when current task ends, `null` if idle. `carrying` / `capacity` are tray slots.

## 4. WaiterTask
```json
{
  "task_id": "task_77",
  "table_id": "T4",
  "type": "deliver_food",
  "status": "pending",
  "created_at": 1700000000.0,
  "ready_at": 1700000040.0,
  "service_s": 20,
  "load": 1,
  "pickup_node": "kitchen_pass",
  "assigned_to": null,
  "order_id": "ord_0192"
}
```
`type`: `deliver_food | deliver_drink | bill | confirm | clear`
`status`: `pending | assigned | in_progress | done | delayed`
- `ready_at`: when the dish was plated (food) — hot-food wait counts from here. `null` for non-food → wait counts from `created_at`.
- `pickup_node`: optional; defaults to `kitchen_pass` for `deliver_food`.
- The swarm plans only tasks with status `pending` or `delayed`. **Delayed** tasks are re-planned automatically next tick.
- Auto-generation (AM): plated tap → `deliver_food`; bill request → `bill`; new order → `confirm`; guests leave → `clear`.

## 5. Floorplan
```json
{
  "sec_per_m": 1.3,
  "nodes": [
    {"id": "kitchen_pass", "x": 0, "y": 0, "kind": "kitchen"},
    {"id": "T1", "x": 4, "y": 3, "kind": "table"}
  ],
  "congestion": {"T3": 10.0}
}
```
`congestion` is optional: multiplier on walk time into that node (blocked aisle / big party).

## 6. Board snapshot (input to the swarm)
What AM's Redis helper returns from `get_board()`:
```json
{ "now": 1700000050.0, "tasks": [ /*WaiterTask*/ ], "waiters": [ /*Waiter*/ ] }
```
Swarm entry point: `BoardState.from_board(board)` → `DispatchEngine.tick(state)`.

## 7. SwarmTick (output of the swarm)
```json
{
  "tick_id": 41,
  "ts": 1700000050.0,
  "warm_start": true,
  "assignments": {
    "W2": [
      {"task_id": "task_77", "table_id": "T4", "type": "deliver_food", "eta_s": 18.2},
      {"task_id": "task_80", "table_id": "T7", "type": "bill",         "eta_s": 61.0}
    ],
    "W3": []
  },
  "unassigned": [],
  "metrics": {"completion_s": 184.2, "hot_wait_s": 517.0, "bill_wait_s": 726.7,
              "walk_s": 335.4, "imbalance": 16.75, "capacity_violations": 0},
  "fitness": 4405.17,
  "iterations": 10,
  "evaluations": 330,
  "elapsed_ms": 13.4
}
```
- `assignments[waiter_id]` is **ordered**; index 0 is what the waiter app shows first (`"T4 steak → T7 bill"`).
- Backend writes each assigned task's `assigned_to` + `status="assigned"`, stores the tick under `swarm:last_tick`, and pushes it on the WebSocket.

## 8. Redis key proposal (AM to confirm)
| Key | Type | Content |
|---|---|---|
| `board:tables` | hash `table_id → Table JSON` | |
| `board:orders` | hash `order_id → Order JSON` | |
| `board:tasks` | hash `task_id → WaiterTask JSON` | |
| `board:waiters` | hash `waiter_id → Waiter JSON` | |
| `board:floorplan` | string | Floorplan JSON |
| `swarm:last_tick` | string | SwarmTick JSON |
| `swarm:ticks` | list (capped) | recent SwarmTicks for logging/replay |

## 9. API endpoints (AM / MA)
| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | liveness |
| POST | `/orders` | customer submits order (`table_id`, items) |
| GET | `/board` | full board snapshot (debug) |
| POST | `/tasks/{task_id}/done` | waiter one-tap Done → updates `Waiter.node` |
| POST | `/tasks/{task_id}/delayed` | waiter one-tap Delayed |
| POST | `/orders/{order_id}/items/{item_id}/plated` | KDS tap → creates `deliver_food` task |
| WS | `/ws/waiter/{waiter_id}` | pushes that waiter's slice of SwarmTick |
| WS | `/ws/kitchen` | pushes ticket updates |
| POST | `/swarm/tick` | trigger a tick manually (dev) |

## Sign-off
- [ ] MD  - [ ] AM  - [ ] MA   (date: ____)
