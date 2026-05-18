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
    *,
    k_repulse: float = 35000.0,
    k_attract: float = 0.1,
    k_align: float = 0.02,
    ideal_len: float = 280.0,
) -> dict[str, tuple[float, float]]:
    """Compute table positions using a force-directed graph layout.

    Args:
        tables: Table metadata extracted by ``introspect_models``.
        relationships: FK / M:N edges between tables.
        iterations: Number of simulation steps (higher = more stable).
        seed: Random seed for reproducible layouts (``None`` for random).
        k_repulse: Repulsion strength between all nodes.
        k_attract: Attraction strength between connected nodes.
        k_align: Horizontal-alignment force for connected nodes.
        ideal_len: Target edge length in pixels between connected nodes.

    Returns:
        Mapping of table name → ``(x, y)`` position.
    """
    if not tables:
        return {}

    rng = random.Random(seed)

    table_names = [t.name for t in tables]
    table_map = {t.name: t for t in tables}
    n = len(table_names)

    schema_of = [t.schema for t in tables]
    multi_schema = len(set(schema_of)) > 1

    edges: list[tuple[int, int]] = []
    name_to_idx = {name: i for i, name in enumerate(table_names)}
    for rel in relationships:
        if rel.from_table in name_to_idx and rel.to_table in name_to_idx:
            edges.append((name_to_idx[rel.from_table], name_to_idx[rel.to_table]))

    spread = max(300, n * 150)
    pos = [Vec(rng.uniform(50, spread), rng.uniform(50, spread)) for _ in range(n)]

    temp = spread / 2.0
    cooling = temp / (iterations + 1)

    for step in range(iterations):
        forces = [Vec(0, 0) for _ in range(n)]

        for i in range(n):
            for j in range(i + 1, n):
                delta = pos[i] - pos[j]
                dist = max(delta.length(), 1.0)
                strength = k_repulse * 1.4 if multi_schema and schema_of[i] != schema_of[j] else k_repulse
                repulse = strength / (dist * dist)
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

        for i_idx, j_idx in edges:
            dy = pos[j_idx].y - pos[i_idx].y
            align_f = Vec(0, dy * k_align)
            forces[i_idx] = forces[i_idx] + align_f
            forces[j_idx] = forces[j_idx] - align_f

        for i in range(n):
            f = forces[i]
            fl = max(f.length(), 0.01)
            capped = min(fl, temp)
            pos[i] = pos[i] + Vec(f.x / fl * capped, f.y / fl * capped)

        temp -= cooling

    heights = [node_h(table_map[name]) for name in table_names]
    gap = 15.0
    for _ in range(50):
        resolved = True
        for i in range(n):
            for j in range(i + 1, n):
                dx = pos[i].x - pos[j].x
                dy = pos[i].y - pos[j].y
                min_dx = NODE_W + gap
                min_dy = (heights[i] + heights[j]) / 2 + gap
                if abs(dx) < min_dx and abs(dy) < min_dy:
                    ox = (min_dx - abs(dx)) / 2 + 1
                    oy = (min_dy - abs(dy)) / 2 + 1
                    if ox < oy:
                        sx = ox if dx >= 0 else -ox
                        pos[i] = Vec(pos[i].x + sx, pos[i].y)
                        pos[j] = Vec(pos[j].x - sx, pos[j].y)
                    else:
                        sy = oy if dy >= 0 else -oy
                        pos[i] = Vec(pos[i].x, pos[i].y + sy)
                        pos[j] = Vec(pos[j].x, pos[j].y - sy)
                    resolved = False
        if resolved:
            break

    min_x = min(p.x for p in pos)
    min_y = min(p.y for p in pos)
    margin = 60.0
    for i in range(n):
        pos[i] = Vec(pos[i].x - min_x + margin, pos[i].y - min_y + margin)

    result: dict[str, tuple[float, float]] = {}
    for i, name in enumerate(table_names):
        result[name] = (round(pos[i].x, 1), round(pos[i].y, 1))

    return result
