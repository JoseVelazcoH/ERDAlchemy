from __future__ import annotations

import math
import random
from dataclasses import dataclass

from sqlalchemy_erd.introspect import TableInfo, RelationshipInfo

NODE_W = 218
HEADER_H = 36
FIELD_H = 21
PAD = 6


def node_h(table: TableInfo) -> int:
    return HEADER_H + PAD + len(table.columns) * FIELD_H + PAD


@dataclass
class Vec:
    x: float
    y: float

    def __add__(self, other: Vec) -> Vec:
        return Vec(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vec) -> Vec:
        return Vec(self.x - other.x, self.y - other.y)

    def __mul__(self, s: float) -> Vec:
        return Vec(self.x * s, self.y * s)

    def length(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y)


def force_directed_layout(
    tables: list[TableInfo],
    relationships: list[RelationshipInfo],
    iterations: int = 300,
    seed: int | None = 42,
) -> dict[str, tuple[float, float]]:
    if not tables:
        return {}

    rng = random.Random(seed)

    table_names = [t.name for t in tables]
    table_map = {t.name: t for t in tables}
    n = len(table_names)

    edges: list[tuple[int, int]] = []
    name_to_idx = {name: i for i, name in enumerate(table_names)}
    for rel in relationships:
        if rel.from_table in name_to_idx and rel.to_table in name_to_idx:
            edges.append((name_to_idx[rel.from_table], name_to_idx[rel.to_table]))

    spread = max(300, n * 150)
    pos = [Vec(rng.uniform(50, spread), rng.uniform(50, spread)) for _ in range(n)]

    k_repulse = 50000.0
    k_attract = 0.005
    ideal_len = 300.0
    temp = spread / 2.0
    cooling = temp / (iterations + 1)

    for step in range(iterations):
        forces = [Vec(0, 0) for _ in range(n)]

        for i in range(n):
            for j in range(i + 1, n):
                delta = pos[i] - pos[j]
                dist = max(delta.length(), 1.0)
                repulse = k_repulse / (dist * dist)
                f = Vec(delta.x / dist * repulse, delta.y / dist * repulse)
                forces[i] = forces[i] + f
                forces[j] = forces[j] - f

        for i_idx, j_idx in edges:
            delta = pos[j_idx] - pos[i_idx]
            dist = max(delta.length(), 1.0)
            attract = k_attract * (dist - ideal_len)
            f = Vec(delta.x / dist * attract, delta.y / dist * attract)
            forces[i_idx] = forces[i_idx] + f
            forces[j_idx] = forces[j_idx] - f

        for i in range(n):
            f = forces[i]
            fl = max(f.length(), 0.01)
            capped = min(fl, temp)
            pos[i] = pos[i] + Vec(f.x / fl * capped, f.y / fl * capped)

        temp -= cooling

    min_x = min(p.x for p in pos)
    min_y = min(p.y for p in pos)
    margin = 60.0
    for i in range(n):
        pos[i] = Vec(pos[i].x - min_x + margin, pos[i].y - min_y + margin)

    result: dict[str, tuple[float, float]] = {}
    for i, name in enumerate(table_names):
        result[name] = (round(pos[i].x, 1), round(pos[i].y, 1))

    return result
