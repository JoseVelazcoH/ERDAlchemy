"""Star/snowflake column layout: a fact table flanked by catalog columns."""

import math

from sqlalchemy_erd.constants.geometry import GAP_X, GAP_Y, MARGIN, NODE_W
from sqlalchemy_erd.introspect import RelationshipInfo, TableInfo
from sqlalchemy_erd.layout import node_h


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
    margin = MARGIN

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
