"""Hierarchical (Sugiyama-style) layered layout for ERDs.

ERDs are hierarchical graphs: a foreign key implies a parent → child direction.
This layout ranks tables into columns by that direction (left → right), orders
nodes within each column to reduce edge crossings, and stacks them so no two
cards overlap by construction — the same strategy Graphviz ``dot`` uses, without
taking a Graphviz dependency.
"""

from collections import defaultdict

from sqlalchemy_erd.constants.geometry import GAP_X, GAP_Y, MARGIN, NODE_W
from sqlalchemy_erd.constants.layered import BARYCENTER_SWEEPS, DISCONNECTED_ROW_GAP
from sqlalchemy_erd.introspect import RelationshipInfo, TableInfo
from sqlalchemy_erd.layout import node_h

_VISITING = "visiting"
_DONE = "done"


def _build_edges(
    names: list[str],
    relationships: list[RelationshipInfo],
) -> list[tuple[str, str]]:
    """Directed parent → child edges, filtered to known tables and de-duplicated."""
    known = set(names)
    edges: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for rel in relationships:
        edge = (rel.from_table, rel.to_table)
        if edge[0] not in known or edge[1] not in known:
            continue
        if edge[0] == edge[1] or edge in seen:
            continue
        seen.add(edge)
        edges.append(edge)
    return edges


def _break_cycles(
    ordered_nodes: list[str],
    edges: list[tuple[str, str]],
) -> list[tuple[str, str]]:
    """Return an acyclic subset of ``edges`` by dropping back edges via DFS.

    Circular foreign keys (e.g. ``departments`` ↔ ``employees``) would otherwise
    make layering diverge. Nodes are visited in a fixed order for determinism.
    """
    successors: dict[str, list[str]] = defaultdict(list)
    for u, v in edges:
        successors[u].append(v)

    state: dict[str, str] = {}
    acyclic: list[tuple[str, str]] = []

    def visit(node: str) -> None:
        state[node] = _VISITING
        for child in successors[node]:
            if state.get(child) == _VISITING:
                continue  # back edge → drop to break the cycle
            acyclic.append((node, child))
            if child not in state:
                visit(child)
        state[node] = _DONE

    for node in ordered_nodes:
        if node not in state:
            visit(node)
    return acyclic


def _assign_layers(
    nodes: set[str],
    acyclic_edges: list[tuple[str, str]],
) -> dict[str, int]:
    """Longest-path layering: each node sits one column right of its deepest parent."""
    layer = {node: 0 for node in nodes}
    for _ in range(len(nodes)):
        changed = False
        for parent, child in acyclic_edges:
            if layer[child] < layer[parent] + 1:
                layer[child] = layer[parent] + 1
                changed = True
        if not changed:
            break
    return layer


def _sort_by_barycenter(
    nodes: list[str],
    reference_order: list[str],
    neighbors: dict[str, list[str]],
) -> list[str]:
    """Order ``nodes`` by the mean position of their neighbors in an adjacent column.

    Nodes with no neighbor in the reference column keep their current position.
    """
    reference_index = {name: i for i, name in enumerate(reference_order)}
    keyed = []
    for current_pos, name in enumerate(nodes):
        neighbor_indices = [
            reference_index[n] for n in neighbors[name] if n in reference_index
        ]
        barycenter = (
            sum(neighbor_indices) / len(neighbor_indices)
            if neighbor_indices
            else current_pos
        )
        keyed.append((barycenter, current_pos, name))
    keyed.sort()
    return [name for _, _, name in keyed]


def _order_within_layers(
    layers: dict[str, int],
    acyclic_edges: list[tuple[str, str]],
) -> dict[int, list[str]]:
    """Crossing reduction: barycenter sweeps down and up the columns."""
    by_layer: dict[int, list[str]] = defaultdict(list)
    for node in sorted(layers):  # deterministic initial order
        by_layer[layers[node]].append(node)
    if not by_layer:
        return by_layer

    max_layer = max(by_layer)
    predecessors: dict[str, list[str]] = defaultdict(list)
    successors: dict[str, list[str]] = defaultdict(list)
    for parent, child in acyclic_edges:
        successors[parent].append(child)
        predecessors[child].append(parent)

    for _ in range(BARYCENTER_SWEEPS):
        for layer_index in range(1, max_layer + 1):
            by_layer[layer_index] = _sort_by_barycenter(
                by_layer[layer_index], by_layer[layer_index - 1], predecessors,
            )
        for layer_index in range(max_layer - 1, -1, -1):
            by_layer[layer_index] = _sort_by_barycenter(
                by_layer[layer_index], by_layer[layer_index + 1], successors,
            )
    return by_layer


def _column_height(names: list[str], table_map: dict[str, TableInfo]) -> float:
    if not names:
        return 0.0
    heights = [node_h(table_map[name]) for name in names]
    return sum(heights) + GAP_Y * (len(heights) - 1)


def _assign_coordinates(
    by_layer: dict[int, list[str]],
    table_map: dict[str, TableInfo],
    node_w: int,
) -> dict[str, tuple[float, float]]:
    """Place each column at a fixed x, vertically centered against the tallest column."""
    positions: dict[str, tuple[float, float]] = {}
    column_heights = {
        layer_index: _column_height(names, table_map)
        for layer_index, names in by_layer.items()
    }
    max_height = max(column_heights.values(), default=0.0)

    for layer_index in sorted(by_layer):
        x = MARGIN + layer_index * (node_w + GAP_X)
        y = MARGIN + (max_height - column_heights[layer_index]) / 2
        for name in by_layer[layer_index]:
            positions[name] = (round(x, 1), round(y, 1))
            y += node_h(table_map[name]) + GAP_Y
    return positions


def _place_disconnected(
    disconnected: list[TableInfo],
    positions: dict[str, tuple[float, float]],
    table_map: dict[str, TableInfo],
    node_w: int,
) -> None:
    """Lay out tables with no relationships in a row below the connected graph."""
    if not disconnected:
        return

    if positions:
        max_bottom = max(
            y + node_h(table_map[name]) for name, (_, y) in positions.items()
        )
        y = max_bottom + DISCONNECTED_ROW_GAP
    else:
        y = MARGIN

    x = MARGIN
    for table in disconnected:
        positions[table.name] = (round(x, 1), round(y, 1))
        x += node_w + GAP_X


def layered_layout(
    tables: list[TableInfo],
    relationships: list[RelationshipInfo],
    node_w: int = NODE_W,
) -> dict[str, tuple[float, float]]:
    """Compute table positions with a hierarchical layered (Sugiyama) layout.

    Args:
        tables: Table metadata extracted by ``introspect_models``.
        relationships: FK / M:N edges between tables.
        node_w: Card width in pixels, used for column spacing.

    Returns:
        Mapping of table name → ``(x, y)`` position.
    """
    if not tables:
        return {}

    table_map = {t.name: t for t in tables}
    names = [t.name for t in tables]

    edges = _build_edges(names, relationships)
    connected = {node for edge in edges for node in edge}
    disconnected = [t for t in tables if t.name not in connected]

    positions: dict[str, tuple[float, float]] = {}
    if connected:
        acyclic_edges = _break_cycles(sorted(connected), edges)
        layers = _assign_layers(connected, acyclic_edges)
        by_layer = _order_within_layers(layers, acyclic_edges)
        positions = _assign_coordinates(by_layer, table_map, node_w)

    _place_disconnected(disconnected, positions, table_map, node_w)
    return positions
