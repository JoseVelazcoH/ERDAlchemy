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


GAP_X = 60
GAP_Y = 40


def _grid_layout(
    tables: list[TableInfo],
    margin: float,
) -> dict[str, tuple[float, float]]:
    n = len(tables)
    cols = max(1, math.ceil(math.sqrt(n)))
    rows: list[list[TableInfo]] = []
    for i in range(0, n, cols):
        rows.append(tables[i:i + cols])

    positions: dict[str, tuple[float, float]] = {}
    y = margin
    for row_tables in rows:
        max_h = max(node_h(t) for t in row_tables)
        x = margin
        for t in row_tables:
            positions[t.name] = (round(x, 1), round(y, 1))
            x += NODE_W + GAP_X
        y += max_h + GAP_Y

    return positions


def star_layout(
    tables: list[TableInfo],
    relationships: list[RelationshipInfo],
) -> dict[str, tuple[float, float]]:
    """Deterministic column-based layout for star schemas and disconnected graphs.

    Args:
        tables: Table metadata extracted by ``introspect_models``.
        relationships: FK / M:N edges between tables.

    Returns:
        Mapping of table name → ``(x, y)`` position.
    """
    if not tables:
        return {}

    table_map = {t.name: t for t in tables}
    margin = 60.0

    outgoing_count: dict[str, int] = {}
    connected: set[str] = set()

    for rel in relationships:
        outgoing_count[rel.to_table] = outgoing_count.get(rel.to_table, 0) + 1
        connected.add(rel.from_table)
        connected.add(rel.to_table)

    disconnected = [t for t in tables if t.name not in connected]

    if not connected:
        return _grid_layout(tables, margin)

    max_out = max(outgoing_count.values())
    fact_tables = [
        t for t in tables
        if outgoing_count.get(t.name, 0) == max_out and t.name in connected
    ]
    fact_names = {t.name for t in fact_tables}
    catalog_tables = [
        t for t in tables
        if t.name in connected and t.name not in fact_names
    ]

    positions: dict[str, tuple[float, float]] = {}

    if len(fact_tables) == 1:
        positions = _single_fact_layout(
            fact_tables[0], catalog_tables, disconnected,
            relationships, table_map, margin,
        )
    else:
        positions = _multi_fact_layout(
            fact_tables, catalog_tables, disconnected,
            table_map, margin,
        )

    return positions


def _single_fact_layout(
    fact: TableInfo,
    catalogs: list[TableInfo],
    disconnected: list[TableInfo],
    relationships: list[RelationshipInfo],
    table_map: dict[str, TableInfo],
    margin: float,
) -> dict[str, tuple[float, float]]:
    fk_order: dict[str, int] = {}
    for rel in relationships:
        if rel.to_table == fact.name and not rel.fk_column.startswith("via "):
            for idx, col in enumerate(fact.columns):
                if col.name == rel.fk_column:
                    fk_order[rel.from_table] = idx
                    break

    catalogs = sorted(catalogs, key=lambda t: fk_order.get(t.name, 999))

    mid = len(catalogs) // 2
    left = catalogs[:mid]
    right = catalogs[mid:]

    left_heights = [node_h(t) for t in left]
    right_heights = [node_h(t) for t in right]
    fact_height = node_h(fact)

    left_total = (sum(left_heights) + GAP_Y * (len(left) - 1)) if left else 0
    right_total = (sum(right_heights) + GAP_Y * (len(right) - 1)) if right else 0
    max_height = max(left_total, right_total, fact_height)

    left_x = margin
    center_x = (margin + NODE_W + GAP_X) if left else margin
    right_x = center_x + NODE_W + GAP_X

    positions: dict[str, tuple[float, float]] = {}

    cy = margin + (max_height - fact_height) / 2
    positions[fact.name] = (round(center_x, 1), round(cy, 1))

    ly = margin + (max_height - left_total) / 2
    for i, t in enumerate(left):
        positions[t.name] = (round(left_x, 1), round(ly, 1))
        ly += left_heights[i] + GAP_Y

    ry = margin + (max_height - right_total) / 2
    for i, t in enumerate(right):
        positions[t.name] = (round(right_x, 1), round(ry, 1))
        ry += right_heights[i] + GAP_Y

    if disconnected:
        max_bottom = max(
            y + node_h(table_map[name])
            for name, (_, y) in positions.items()
        )
        disc_y = max_bottom + GAP_Y * 2
        dx = margin
        for t in disconnected:
            positions[t.name] = (round(dx, 1), round(disc_y, 1))
            dx += NODE_W + GAP_X

    return positions


def _multi_fact_layout(
    fact_tables: list[TableInfo],
    catalogs: list[TableInfo],
    disconnected: list[TableInfo],
    table_map: dict[str, TableInfo],
    margin: float,
) -> dict[str, tuple[float, float]]:
    positions: dict[str, tuple[float, float]] = {}

    x = margin
    catalog_max_h = 0
    for t in catalogs:
        h = node_h(t)
        positions[t.name] = (round(x, 1), round(margin, 1))
        x += NODE_W + GAP_X
        catalog_max_h = max(catalog_max_h, h)

    fact_y = margin + (catalog_max_h + GAP_Y * 2 if catalogs else 0)
    catalog_row_width = (len(catalogs) * (NODE_W + GAP_X) - GAP_X) if catalogs else 0
    fact_row_width = len(fact_tables) * (NODE_W + GAP_X) - GAP_X
    fx = margin + max(0, (catalog_row_width - fact_row_width) / 2)
    fact_max_h = 0
    for t in fact_tables:
        h = node_h(t)
        positions[t.name] = (round(fx, 1), round(fact_y, 1))
        fx += NODE_W + GAP_X
        fact_max_h = max(fact_max_h, h)

    if disconnected:
        max_bottom = max(
            y + node_h(table_map[name])
            for name, (_, y) in positions.items()
        )
        disc_y = max_bottom + GAP_Y * 2
        dx = margin
        for t in disconnected:
            positions[t.name] = (round(dx, 1), round(disc_y, 1))
            dx += NODE_W + GAP_X

    return positions
