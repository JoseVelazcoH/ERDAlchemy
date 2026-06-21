"""Tests for sqlalchemy_erd.layered — hierarchical (Sugiyama-style) layered layout."""

from sqlalchemy_erd.constants.geometry import NODE_W
from sqlalchemy_erd.introspect import introspect_models, TableInfo, ColumnInfo
from sqlalchemy_erd.layered import layered_layout
from sqlalchemy_erd.layout import node_h


def _make_table(name: str, n_cols: int = 2) -> TableInfo:
    columns = [
        ColumnInfo(name=f"c{i}", kind="int", nullable=False, is_pk=(i == 0), is_fk=False)
        for i in range(n_cols)
    ]
    return TableInfo(name=name, class_name=name, schema=None, columns=columns)


def _overlaps(pos, tables, node_w=NODE_W):
    table_map = {t.name: t for t in tables}
    names = list(pos)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            x1, y1 = pos[names[i]]
            x2, y2 = pos[names[j]]
            h1 = node_h(table_map[names[i]])
            h2 = node_h(table_map[names[j]])
            overlap_x = x1 < x2 + node_w and x2 < x1 + node_w
            overlap_y = y1 < y2 + h1 and y2 < y1 + h2
            if overlap_x and overlap_y:
                return (names[i], names[j])
    return None


class TestLayeredLayout:
    def test_empty_tables_returns_empty(self):
        assert layered_layout([], []) == {}

    def test_positions_all_tables(self, blog_base):
        tables, rels = introspect_models(blog_base)
        positions = layered_layout(tables, rels)
        assert set(positions) == {t.name for t in tables}

    def test_positions_are_non_negative(self, blog_base):
        tables, rels = introspect_models(blog_base)
        positions = layered_layout(tables, rels)
        assert all(x >= 0 and y >= 0 for x, y in positions.values())

    def test_no_two_nodes_overlap(self, blog_base):
        tables, rels = introspect_models(blog_base)
        positions = layered_layout(tables, rels)
        assert _overlaps(positions, tables) is None

    def test_is_deterministic(self, blog_base):
        tables, rels = introspect_models(blog_base)
        assert layered_layout(tables, rels) == layered_layout(tables, rels)

    def test_parent_is_left_of_child(self, blog_base):
        tables, rels = introspect_models(blog_base)
        positions = layered_layout(tables, rels)
        # FK chain: users (parent) -> posts -> comments
        assert positions["users"][0] < positions["posts"][0]
        assert positions["posts"][0] < positions["comments"][0]

    def test_single_table_placed_at_margin(self):
        tables = [_make_table("solo")]
        positions = layered_layout(tables, [])
        x, y = positions["solo"]
        assert x > 0 and y > 0

    def test_disconnected_tables_are_placed_without_overlap(self):
        tables = [_make_table("a"), _make_table("b"), _make_table("c")]
        positions = layered_layout(tables, [])
        assert set(positions) == {"a", "b", "c"}
        assert _overlaps(positions, tables) is None

    def test_circular_fk_does_not_crash_and_places_all(self, circular_metadata_fixture):
        tables, rels = introspect_models(circular_metadata_fixture)
        positions = layered_layout(tables, rels)
        assert set(positions) == {t.name for t in tables}
        assert _overlaps(positions, tables) is None

    def test_wider_node_pushes_child_column_further_right(self, blog_base):
        tables, rels = introspect_models(blog_base)
        narrow = layered_layout(tables, rels, node_w=218)
        wide = layered_layout(tables, rels, node_w=600)
        # posts sits in the second column; a wider node widens the column gap
        assert wide["posts"][0] > narrow["posts"][0]

    def test_many_to_many_does_not_overlap(self, m2m_base):
        tables, rels = introspect_models(m2m_base)
        positions = layered_layout(tables, rels)
        assert _overlaps(positions, tables) is None
