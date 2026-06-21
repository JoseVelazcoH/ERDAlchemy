from __future__ import annotations

import math
import random
from dataclasses import dataclass

from sqlalchemy_erd.introspect import TableInfo, RelationshipInfo
from sqlalchemy_erd.theme import DEFAULT_KIND_LABELS

NODE_W = 218
HEADER_H = 36
FIELD_H = 21
PAD = 6


def node_h(table: TableInfo) -> int:
    return HEADER_H + PAD + len(table.columns) * FIELD_H + PAD


def auto_node_width(tables: list[TableInfo]) -> int:
    char_w = 6.2
    max_w = NODE_W
    for t in tables:
        header_w = 24 + len(t.class_name) * 7.8
        max_w = max(max_w, int(header_w))
        for col in t.columns:
            kind_label = DEFAULT_KIND_LABELS.get(col.kind, col.kind)
            if not col.is_pk and not col.is_fk and col.nullable:
                kind_label += "?"
            col_w = 10 + len(col.name) * char_w + 12 + len(kind_label) * char_w + 8
            max_w = max(max_w, int(col_w))
    return max_w


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
    node_w: int = NODE_W,
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
                min_dx = node_w + gap
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
    node_w: int = NODE_W,
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
            x += node_w + GAP_X
        y += max_h + GAP_Y

    return positions


def star_layout(
    tables: list[TableInfo],
    relationships: list[RelationshipInfo],
    star_cols: int | None = None,
    node_w: int = NODE_W,
) -> dict[str, tuple[float, float]]:
    """Deterministic column-based layout for star schemas and disconnected graphs.

    Args:
        tables: Table metadata extracted by ``introspect_models``.
        relationships: FK / M:N edges between tables.
        star_cols: Number of catalog columns per side of the fact table.
            ``None`` selects automatically (2 per side when >12 catalogs,
            1 otherwise).

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
        return _grid_layout(tables, margin, node_w)

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
            relationships, table_map, margin, star_cols, node_w,
        )
    else:
        positions = _multi_fact_layout(
            fact_tables, catalog_tables, disconnected,
            table_map, margin, node_w,
        )

    return positions


def _single_fact_layout(
    fact: TableInfo,
    catalogs: list[TableInfo],
    disconnected: list[TableInfo],
    relationships: list[RelationshipInfo],
    table_map: dict[str, TableInfo],
    margin: float,
    star_cols: int | None = None,
    node_w: int = NODE_W,
) -> dict[str, tuple[float, float]]:
    fk_order: dict[str, int] = {}
    for rel in relationships:
        if rel.to_table == fact.name and not rel.fk_column.startswith("via "):
            for idx, col in enumerate(fact.columns):
                if col.name == rel.fk_column:
                    fk_order[rel.from_table] = idx
                    break

    catalogs = sorted(catalogs, key=lambda t: fk_order.get(t.name, math.inf))

    if star_cols is None:
        star_cols = 2 if len(catalogs) > 12 else 1

    total_slots = 2 * star_cols
    chunk_size = math.ceil(len(catalogs) / total_slots) if catalogs else 0
    groups: list[list[TableInfo]] = []
    for i in range(total_slots):
        start = i * chunk_size
        groups.append(catalogs[start:start + chunk_size])

    left_groups = groups[:star_cols]
    right_groups = groups[star_cols:]

    def _col_total_h(col_tables: list[TableInfo]) -> float:
        if not col_tables:
            return 0
        heights = [node_h(t) for t in col_tables]
        return sum(heights) + GAP_Y * (len(heights) - 1)

    fact_height = node_h(fact)
    all_totals = (
        [_col_total_h(g) for g in left_groups]
        + [fact_height]
        + [_col_total_h(g) for g in right_groups]
    )
    max_height = max(all_totals)

    has_left = any(left_groups)
    n_left_cols = star_cols if has_left else 0

    positions: dict[str, tuple[float, float]] = {}

    for ci, group in enumerate(left_groups):
        x = margin + ci * (node_w + GAP_X)
        total_h = _col_total_h(group)
        y = margin + (max_height - total_h) / 2
        for t in group:
            positions[t.name] = (round(x, 1), round(y, 1))
            y += node_h(t) + GAP_Y

    center_x = margin + n_left_cols * (node_w + GAP_X)
    cy = margin + (max_height - fact_height) / 2
    positions[fact.name] = (round(center_x, 1), round(cy, 1))

    for ci, group in enumerate(right_groups):
        x = center_x + (ci + 1) * (node_w + GAP_X)
        total_h = _col_total_h(group)
        y = margin + (max_height - total_h) / 2
        for t in group:
            positions[t.name] = (round(x, 1), round(y, 1))
            y += node_h(t) + GAP_Y

    if disconnected:
        max_bottom = max(
            y + node_h(table_map[name])
            for name, (_, y) in positions.items()
        )
        disc_y = max_bottom + GAP_Y * 2
        dx = margin
        for t in disconnected:
            positions[t.name] = (round(dx, 1), round(disc_y, 1))
            dx += node_w + GAP_X

    return positions


def _multi_fact_layout(
    fact_tables: list[TableInfo],
    catalogs: list[TableInfo],
    disconnected: list[TableInfo],
    table_map: dict[str, TableInfo],
    margin: float,
    node_w: int = NODE_W,
) -> dict[str, tuple[float, float]]:
    positions: dict[str, tuple[float, float]] = {}

    x = margin
    catalog_max_h = 0
    for t in catalogs:
        h = node_h(t)
        positions[t.name] = (round(x, 1), round(margin, 1))
        x += node_w + GAP_X
        catalog_max_h = max(catalog_max_h, h)

    fact_y = margin + (catalog_max_h + GAP_Y * 2 if catalogs else 0)
    catalog_row_width = (len(catalogs) * (node_w + GAP_X) - GAP_X) if catalogs else 0
    fact_row_width = len(fact_tables) * (node_w + GAP_X) - GAP_X
    fx = margin + max(0, (catalog_row_width - fact_row_width) / 2)
    fact_max_h = 0
    for t in fact_tables:
        h = node_h(t)
        positions[t.name] = (round(fx, 1), round(fact_y, 1))
        fx += node_w + GAP_X
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
            dx += node_w + GAP_X

    return positions
