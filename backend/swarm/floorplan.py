"""Floorplan as node coordinates; walk time = Manhattan distance * sec_per_m."""
from __future__ import annotations


class Floorplan:
    def __init__(self, nodes: dict[str, tuple[float, float]],
                 sec_per_m: float = 1.3,
                 congestion: dict[str, float] | None = None):
        """nodes: id -> (x_m, y_m). congestion: id -> multiplier on walking INTO that node
        (e.g. 10.0 for a blocked aisle / birthday party)."""
        self.nodes = dict(nodes)
        self.sec_per_m = sec_per_m
        self.congestion = congestion or {}
        self.ids = list(self.nodes)
        self.index = {n: i for i, n in enumerate(self.ids)}
        self.matrix = self._build()

    @classmethod
    def from_json(cls, data: dict) -> "Floorplan":
        nodes = {n["id"]: (float(n["x"]), float(n["y"])) for n in data["nodes"]}
        return cls(nodes, float(data.get("sec_per_m", 1.3)), data.get("congestion"))

    def _build(self) -> list[list[float]]:
        m = []
        for a in self.ids:
            ax, ay = self.nodes[a]
            row = []
            for b in self.ids:
                bx, by = self.nodes[b]
                t = (abs(ax - bx) + abs(ay - by)) * self.sec_per_m
                row.append(t * self.congestion.get(b, 1.0) if a != b else 0.0)
            m.append(row)
        return m

    def walk_time(self, a: str, b: str) -> float:
        return self.matrix[self.index[a]][self.index[b]]
