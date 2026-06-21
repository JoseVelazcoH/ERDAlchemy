"""Tests for sqlalchemy_erd.layout — force-directed algorithm, star layout, node sizing."""

from __future__ import annotations

from sqlalchemy_erd.force import force_directed_layout, ForceParams, Vec
from sqlalchemy_erd.introspect import introspect_models, TableInfo, ColumnInfo, RelationshipInfo
from sqlalchemy_erd.layout import (
    auto_node_width,
    node_h,
    NODE_W,
    HEADER_H,
    FIELD_H,
    PAD,
)
from sqlalchemy_erd.star import star_layout


# ── Vec ──────────────────────────────────────────────────────────────────────

class TestVec:
    def test_vec_add_returns_componentwise_sum(self):
        assert Vec(1, 2) + Vec(3, 4) == Vec(4, 6)

    def test_vec_sub_returns_componentwise_difference(self):
        assert Vec(5, 7) - Vec(2, 3) == Vec(3, 4)

    def test_vec_mul_scales_both_components(self):
        assert Vec(3, 4) * 2 == Vec(6, 8)

    def test_vec_length_of_3_4_is_5(self):
        assert Vec(3, 4).length() == 5.0

    def test_vec_length_of_zero_is_zero(self):
        assert Vec(0, 0).length() == 0.0


# ── node_h ───────────────────────────────────────────────────────────────────

class TestNodeH:
    def test_no_columns(self):
        t = TableInfo(name="t", class_name="T", columns=[])
        assert node_h(t) == HEADER_H + PAD + 0 * FIELD_H + PAD

    def test_with_columns(self):
        cols = [ColumnInfo(name=f"c{i}", kind="int", nullable=False, is_pk=False, is_fk=False) for i in range(5)]
        t = TableInfo(name="t", class_name="T", columns=cols)
        assert node_h(t) == HEADER_H + PAD + 5 * FIELD_H + PAD

    def test_single_column(self):
        cols = [ColumnInfo(name="id", kind="pk", nullable=False, is_pk=True, is_fk=False)]
        t = TableInfo(name="t", class_name="T", columns=cols)
        assert node_h(t) == HEADER_H + PAD + 1 * FIELD_H + PAD


# ── force_directed_layout ────────────────────────────────────────────────────

class TestForceDirectedLayout:
    def test_empty_tables(self):
        result = force_directed_layout([], [])
        assert result == {}

    def test_single_table(self, single_table_base):
        tables, rels = introspect_models(single_table_base)
        positions = force_directed_layout(tables, rels)
        assert len(positions) == 1
        assert "standalone" in positions
        x, y = positions["standalone"]
        assert x > 0 and y > 0

    def test_all_tables_positioned(self, blog_base):
        tables, rels = introspect_models(blog_base)
        positions = force_directed_layout(tables, rels)
        assert len(positions) == 3
        for t in tables:
            assert t.name in positions

    def test_positions_are_positive(self, blog_base):
        tables, rels = introspect_models(blog_base)
        positions = force_directed_layout(tables, rels)
        for name, (x, y) in positions.items():
            assert x > 0, f"{name} has non-positive x"
            assert y > 0, f"{name} has non-positive y"

    def test_no_overlap(self, blog_base):
        tables, rels = introspect_models(blog_base)
        positions = force_directed_layout(tables, rels)
        table_map = {t.name: t for t in tables}
        names = list(positions.keys())
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                x1, y1 = positions[names[i]]
                x2, y2 = positions[names[j]]
                h1 = node_h(table_map[names[i]])
                h2 = node_h(table_map[names[j]])
                overlap_x = x1 < x2 + NODE_W and x2 < x1 + NODE_W
                overlap_y = y1 < y2 + h2 and y2 < y1 + h1
                assert not (overlap_x and overlap_y), (
                    f"Tables {names[i]} and {names[j]} overlap"
                )

    def test_deterministic_with_seed(self, blog_base):
        tables, rels = introspect_models(blog_base)
        pos1 = force_directed_layout(tables, rels, seed=42)
        pos2 = force_directed_layout(tables, rels, seed=42)
        assert pos1 == pos2

    def test_different_seed_different_result(self, blog_base):
        tables, rels = introspect_models(blog_base)
        pos1 = force_directed_layout(tables, rels, seed=42)
        pos2 = force_directed_layout(tables, rels, seed=99)
        assert pos1 != pos2

    def test_accepts_force_params(self, blog_base):
        tables, rels = introspect_models(blog_base)
        positions = force_directed_layout(
            tables, rels, force=ForceParams(ideal_len=400.0),
        )
        assert set(positions) == {t.name for t in tables}

    def test_force_params_change_layout(self, blog_base):
        tables, rels = introspect_models(blog_base)
        tight = force_directed_layout(tables, rels, seed=42, force=ForceParams(ideal_len=100.0))
        loose = force_directed_layout(tables, rels, seed=42, force=ForceParams(ideal_len=600.0))
        assert tight != loose

    def test_force_params_defaults_match_legacy(self):
        params = ForceParams()
        assert (params.k_repulse, params.k_attract, params.k_align, params.ideal_len) == (
            35000.0, 0.1, 0.02, 280.0,
        )

    def test_connected_tables_closer(self, blog_base):
        tables, rels = introspect_models(blog_base)
        positions = force_directed_layout(tables, rels, iterations=500)
        ux, uy = positions["users"]
        px, py = positions["posts"]
        cx, cy = positions["comments"]
        dist_users_posts = ((ux - px) ** 2 + (uy - py) ** 2) ** 0.5
        assert dist_users_posts < 1000


# ── star_layout ─────────────────────────────────────────────────────────────

class TestStarLayout:
    def test_empty_tables(self):
        assert star_layout([], []) == {}

    def test_single_table(self, single_table_base):
        tables, rels = introspect_models(single_table_base)
        positions = star_layout(tables, rels)
        assert len(positions) == 1
        assert "standalone" in positions
        x, y = positions["standalone"]
        assert x > 0 and y > 0

    def test_all_tables_positioned(self, blog_base):
        tables, rels = introspect_models(blog_base)
        positions = star_layout(tables, rels)
        assert len(positions) == 3
        for t in tables:
            assert t.name in positions

    def test_positions_are_positive(self, blog_base):
        tables, rels = introspect_models(blog_base)
        positions = star_layout(tables, rels)
        for name, (x, y) in positions.items():
            assert x > 0, f"{name} has non-positive x"
            assert y > 0, f"{name} has non-positive y"

    def test_deterministic(self, blog_base):
        tables, rels = introspect_models(blog_base)
        pos1 = star_layout(tables, rels)
        pos2 = star_layout(tables, rels)
        assert pos1 == pos2

    def test_disconnected_grid(self):
        tables = [
            TableInfo(name="a", class_name="A", columns=[
                ColumnInfo(name="id", kind="pk", nullable=False, is_pk=True, is_fk=False),
            ]),
            TableInfo(name="b", class_name="B", columns=[
                ColumnInfo(name="id", kind="pk", nullable=False, is_pk=True, is_fk=False),
            ]),
            TableInfo(name="c", class_name="C", columns=[
                ColumnInfo(name="id", kind="pk", nullable=False, is_pk=True, is_fk=False),
            ]),
        ]
        positions = star_layout(tables, [])
        assert len(positions) == 3
        xs = {x for x, _ in positions.values()}
        assert len(xs) == 2, "3 disconnected tables should form a 2-column grid"

    def test_star_fact_centered(self):
        fact = TableInfo(name="fact", class_name="Fact", columns=[
            ColumnInfo(name="id", kind="pk", nullable=False, is_pk=True, is_fk=False),
            ColumnInfo(name="a_id", kind="fk", nullable=False, is_pk=False, is_fk=True),
            ColumnInfo(name="b_id", kind="fk", nullable=False, is_pk=False, is_fk=True),
            ColumnInfo(name="c_id", kind="fk", nullable=False, is_pk=False, is_fk=True),
            ColumnInfo(name="d_id", kind="fk", nullable=False, is_pk=False, is_fk=True),
        ])
        cat = lambda name: TableInfo(name=name, class_name=name.upper(), columns=[
            ColumnInfo(name="id", kind="pk", nullable=False, is_pk=True, is_fk=False),
            ColumnInfo(name="name", kind="string", nullable=False, is_pk=False, is_fk=False),
        ])
        tables = [cat("a"), cat("b"), cat("c"), cat("d"), fact]
        rels = [
            RelationshipInfo(from_table="a", to_table="fact", from_card="1", to_card="N", fk_column="a_id"),
            RelationshipInfo(from_table="b", to_table="fact", from_card="1", to_card="N", fk_column="b_id"),
            RelationshipInfo(from_table="c", to_table="fact", from_card="1", to_card="N", fk_column="c_id"),
            RelationshipInfo(from_table="d", to_table="fact", from_card="1", to_card="N", fk_column="d_id"),
        ]

        positions = star_layout(tables, rels)
        fx, _ = positions["fact"]
        left_xs = {positions["a"][0], positions["b"][0]}
        right_xs = {positions["c"][0], positions["d"][0]}
        assert len(left_xs) == 1, "Left catalogs should share the same x"
        assert len(right_xs) == 1, "Right catalogs should share the same x"
        left_x = left_xs.pop()
        right_x = right_xs.pop()
        assert left_x < fx < right_x, "Fact table should be between left and right catalogs"

    def test_star_catalogs_ordered_by_fk_position(self):
        fact = TableInfo(name="fact", class_name="Fact", columns=[
            ColumnInfo(name="id", kind="pk", nullable=False, is_pk=True, is_fk=False),
            ColumnInfo(name="z_id", kind="fk", nullable=False, is_pk=False, is_fk=True),
            ColumnInfo(name="a_id", kind="fk", nullable=False, is_pk=False, is_fk=True),
        ])
        cat_z = TableInfo(name="z", class_name="Z", columns=[
            ColumnInfo(name="id", kind="pk", nullable=False, is_pk=True, is_fk=False),
        ])
        cat_a = TableInfo(name="a", class_name="A", columns=[
            ColumnInfo(name="id", kind="pk", nullable=False, is_pk=True, is_fk=False),
        ])
        tables = [cat_z, cat_a, fact]
        rels = [
            RelationshipInfo(from_table="z", to_table="fact", from_card="1", to_card="N", fk_column="z_id"),
            RelationshipInfo(from_table="a", to_table="fact", from_card="1", to_card="N", fk_column="a_id"),
        ]

        positions = star_layout(tables, rels)
        zx, _ = positions["z"]
        ax, _ = positions["a"]
        fx, _ = positions["fact"]
        assert zx < fx, "z (first FK) should be on the left"
        assert ax > fx, "a (second FK) should be on the right"

    def test_no_overlap(self):
        fact = TableInfo(name="fact", class_name="Fact", columns=[
            ColumnInfo(name="id", kind="pk", nullable=False, is_pk=True, is_fk=False),
            ColumnInfo(name="a_id", kind="fk", nullable=False, is_pk=False, is_fk=True),
            ColumnInfo(name="b_id", kind="fk", nullable=False, is_pk=False, is_fk=True),
            ColumnInfo(name="c_id", kind="fk", nullable=False, is_pk=False, is_fk=True),
            ColumnInfo(name="d_id", kind="fk", nullable=False, is_pk=False, is_fk=True),
            ColumnInfo(name="e_id", kind="fk", nullable=False, is_pk=False, is_fk=True),
            ColumnInfo(name="f_id", kind="fk", nullable=False, is_pk=False, is_fk=True),
        ])
        cat = lambda name: TableInfo(name=name, class_name=name.upper(), columns=[
            ColumnInfo(name="id", kind="pk", nullable=False, is_pk=True, is_fk=False),
            ColumnInfo(name="name", kind="string", nullable=False, is_pk=False, is_fk=False),
        ])
        tables = [cat("a"), cat("b"), cat("c"), cat("d"), cat("e"), cat("f"), fact]
        rels = [
            RelationshipInfo(from_table=n, to_table="fact", from_card="1", to_card="N", fk_column=f"{n}_id")
            for n in "abcdef"
        ]

        positions = star_layout(tables, rels)
        table_map = {t.name: t for t in tables}
        names = list(positions.keys())
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                x1, y1 = positions[names[i]]
                x2, y2 = positions[names[j]]
                h1 = node_h(table_map[names[i]])
                h2 = node_h(table_map[names[j]])
                overlap_x = x1 < x2 + NODE_W and x2 < x1 + NODE_W
                overlap_y = y1 < y2 + h2 and y2 < y1 + h1
                assert not (overlap_x and overlap_y), (
                    f"Tables {names[i]} and {names[j]} overlap"
                )

    def test_disconnected_below_connected(self):
        fact = TableInfo(name="fact", class_name="Fact", columns=[
            ColumnInfo(name="id", kind="pk", nullable=False, is_pk=True, is_fk=False),
            ColumnInfo(name="a_id", kind="fk", nullable=False, is_pk=False, is_fk=True),
        ])
        cat_a = TableInfo(name="a", class_name="A", columns=[
            ColumnInfo(name="id", kind="pk", nullable=False, is_pk=True, is_fk=False),
        ])
        disc = TableInfo(name="disc", class_name="Disc", columns=[
            ColumnInfo(name="id", kind="pk", nullable=False, is_pk=True, is_fk=False),
        ])
        tables = [cat_a, fact, disc]
        rels = [
            RelationshipInfo(from_table="a", to_table="fact", from_card="1", to_card="N", fk_column="a_id"),
        ]

        positions = star_layout(tables, rels)
        _, disc_y = positions["disc"]
        _, fact_y = positions["fact"]
        _, a_y = positions["a"]
        assert disc_y > max(fact_y, a_y), "Disconnected table should be below connected tables"

    def test_star_cols_explicit_1(self):
        fact = TableInfo(name="fact", class_name="Fact", columns=[
            ColumnInfo(name="id", kind="pk", nullable=False, is_pk=True, is_fk=False),
            ColumnInfo(name="a_id", kind="fk", nullable=False, is_pk=False, is_fk=True),
            ColumnInfo(name="b_id", kind="fk", nullable=False, is_pk=False, is_fk=True),
            ColumnInfo(name="c_id", kind="fk", nullable=False, is_pk=False, is_fk=True),
            ColumnInfo(name="d_id", kind="fk", nullable=False, is_pk=False, is_fk=True),
        ])
        cat = lambda name: TableInfo(name=name, class_name=name.upper(), columns=[
            ColumnInfo(name="id", kind="pk", nullable=False, is_pk=True, is_fk=False),
        ])
        tables = [cat("a"), cat("b"), cat("c"), cat("d"), fact]
        rels = [
            RelationshipInfo(from_table=n, to_table="fact", from_card="1", to_card="N", fk_column=f"{n}_id")
            for n in "abcd"
        ]
        positions = star_layout(tables, rels, star_cols=1)
        xs = sorted({x for x, _ in positions.values()})
        assert len(xs) == 3, "star_cols=1 should produce 3 x-columns (left, center, right)"

    def test_star_cols_2_produces_5_columns(self):
        fact = TableInfo(name="fact", class_name="Fact", columns=[
            ColumnInfo(name="id", kind="pk", nullable=False, is_pk=True, is_fk=False),
        ] + [
            ColumnInfo(name=f"{c}_id", kind="fk", nullable=False, is_pk=False, is_fk=True)
            for c in "abcdefgh"
        ])
        cat = lambda name: TableInfo(name=name, class_name=name.upper(), columns=[
            ColumnInfo(name="id", kind="pk", nullable=False, is_pk=True, is_fk=False),
        ])
        tables = [cat(c) for c in "abcdefgh"] + [fact]
        rels = [
            RelationshipInfo(from_table=n, to_table="fact", from_card="1", to_card="N", fk_column=f"{n}_id")
            for n in "abcdefgh"
        ]
        positions = star_layout(tables, rels, star_cols=2)
        xs = sorted({x for x, _ in positions.values()})
        assert len(xs) == 5, "star_cols=2 should produce 5 x-columns"

    def test_star_cols_2_fact_centered(self):
        fact = TableInfo(name="fact", class_name="Fact", columns=[
            ColumnInfo(name="id", kind="pk", nullable=False, is_pk=True, is_fk=False),
        ] + [
            ColumnInfo(name=f"{c}_id", kind="fk", nullable=False, is_pk=False, is_fk=True)
            for c in "abcdefgh"
        ])
        cat = lambda name: TableInfo(name=name, class_name=name.upper(), columns=[
            ColumnInfo(name="id", kind="pk", nullable=False, is_pk=True, is_fk=False),
        ])
        tables = [cat(c) for c in "abcdefgh"] + [fact]
        rels = [
            RelationshipInfo(from_table=n, to_table="fact", from_card="1", to_card="N", fk_column=f"{n}_id")
            for n in "abcdefgh"
        ]
        positions = star_layout(tables, rels, star_cols=2)
        xs = sorted({x for x, _ in positions.values()})
        fact_x = positions["fact"][0]
        assert fact_x == xs[2], "Fact should be in the center column (index 2 of 5)"

    def test_star_cols_auto_uses_2_for_many_catalogs(self):
        fact = TableInfo(name="fact", class_name="Fact", columns=[
            ColumnInfo(name="id", kind="pk", nullable=False, is_pk=True, is_fk=False),
        ] + [
            ColumnInfo(name=f"c{i}_id", kind="fk", nullable=False, is_pk=False, is_fk=True)
            for i in range(14)
        ])
        cat = lambda name: TableInfo(name=name, class_name=name.upper(), columns=[
            ColumnInfo(name="id", kind="pk", nullable=False, is_pk=True, is_fk=False),
        ])
        tables = [cat(f"c{i}") for i in range(14)] + [fact]
        rels = [
            RelationshipInfo(from_table=f"c{i}", to_table="fact", from_card="1", to_card="N", fk_column=f"c{i}_id")
            for i in range(14)
        ]
        positions = star_layout(tables, rels)
        xs = sorted({x for x, _ in positions.values()})
        assert len(xs) == 5, "Auto should use star_cols=2 for >12 catalogs"

    def test_star_cols_auto_uses_1_for_few_catalogs(self):
        fact = TableInfo(name="fact", class_name="Fact", columns=[
            ColumnInfo(name="id", kind="pk", nullable=False, is_pk=True, is_fk=False),
            ColumnInfo(name="a_id", kind="fk", nullable=False, is_pk=False, is_fk=True),
            ColumnInfo(name="b_id", kind="fk", nullable=False, is_pk=False, is_fk=True),
        ])
        cat = lambda name: TableInfo(name=name, class_name=name.upper(), columns=[
            ColumnInfo(name="id", kind="pk", nullable=False, is_pk=True, is_fk=False),
        ])
        tables = [cat("a"), cat("b"), fact]
        rels = [
            RelationshipInfo(from_table=n, to_table="fact", from_card="1", to_card="N", fk_column=f"{n}_id")
            for n in "ab"
        ]
        positions = star_layout(tables, rels)
        xs = sorted({x for x, _ in positions.values()})
        assert len(xs) == 3, "Auto should use star_cols=1 for <=12 catalogs"

    def test_star_cols_3_produces_7_columns(self):
        fact = TableInfo(name="fact", class_name="Fact", columns=[
            ColumnInfo(name="id", kind="pk", nullable=False, is_pk=True, is_fk=False),
        ] + [
            ColumnInfo(name=f"{c}_id", kind="fk", nullable=False, is_pk=False, is_fk=True)
            for c in "abcdefghijkl"
        ])
        cat = lambda name: TableInfo(name=name, class_name=name.upper(), columns=[
            ColumnInfo(name="id", kind="pk", nullable=False, is_pk=True, is_fk=False),
        ])
        tables = [cat(c) for c in "abcdefghijkl"] + [fact]
        rels = [
            RelationshipInfo(from_table=n, to_table="fact", from_card="1", to_card="N", fk_column=f"{n}_id")
            for n in "abcdefghijkl"
        ]
        positions = star_layout(tables, rels, star_cols=3)
        xs = sorted({x for x, _ in positions.values()})
        assert len(xs) == 7, "star_cols=3 should produce 7 x-columns"

    def test_star_cols_no_overlap(self):
        fact = TableInfo(name="fact", class_name="Fact", columns=[
            ColumnInfo(name="id", kind="pk", nullable=False, is_pk=True, is_fk=False),
        ] + [
            ColumnInfo(name=f"{c}_id", kind="fk", nullable=False, is_pk=False, is_fk=True)
            for c in "abcdefgh"
        ])
        cat = lambda name: TableInfo(name=name, class_name=name.upper(), columns=[
            ColumnInfo(name="id", kind="pk", nullable=False, is_pk=True, is_fk=False),
            ColumnInfo(name="name", kind="string", nullable=False, is_pk=False, is_fk=False),
        ])
        tables = [cat(c) for c in "abcdefgh"] + [fact]
        rels = [
            RelationshipInfo(from_table=n, to_table="fact", from_card="1", to_card="N", fk_column=f"{n}_id")
            for n in "abcdefgh"
        ]
        positions = star_layout(tables, rels, star_cols=2)
        table_map = {t.name: t for t in tables}
        names = list(positions.keys())
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                x1, y1 = positions[names[i]]
                x2, y2 = positions[names[j]]
                h1 = node_h(table_map[names[i]])
                h2 = node_h(table_map[names[j]])
                overlap_x = x1 < x2 + NODE_W and x2 < x1 + NODE_W
                overlap_y = y1 < y2 + h2 and y2 < y1 + h1
                assert not (overlap_x and overlap_y), (
                    f"Tables {names[i]} and {names[j]} overlap"
                )

    def test_multi_fact_catalogs_above(self):
        cat = TableInfo(name="cat", class_name="Cat", columns=[
            ColumnInfo(name="id", kind="pk", nullable=False, is_pk=True, is_fk=False),
        ])
        fact1 = TableInfo(name="f1", class_name="F1", columns=[
            ColumnInfo(name="id", kind="pk", nullable=False, is_pk=True, is_fk=False),
            ColumnInfo(name="cat_id", kind="fk", nullable=False, is_pk=False, is_fk=True),
        ])
        fact2 = TableInfo(name="f2", class_name="F2", columns=[
            ColumnInfo(name="id", kind="pk", nullable=False, is_pk=True, is_fk=False),
            ColumnInfo(name="cat_id", kind="fk", nullable=False, is_pk=False, is_fk=True),
        ])
        tables = [cat, fact1, fact2]
        rels = [
            RelationshipInfo(from_table="cat", to_table="f1", from_card="1", to_card="N", fk_column="cat_id"),
            RelationshipInfo(from_table="cat", to_table="f2", from_card="1", to_card="N", fk_column="cat_id"),
        ]

        positions = star_layout(tables, rels)
        _, cat_y = positions["cat"]
        _, f1_y = positions["f1"]
        _, f2_y = positions["f2"]
        assert cat_y < f1_y, "Catalog should be above fact tables"
        assert cat_y < f2_y, "Catalog should be above fact tables"


# ── auto_node_width ────────────────────────────────────────────────────────

class TestAutoNodeWidth:
    def test_short_names_return_default(self):
        tables = [TableInfo(name="t", class_name="T", columns=[
            ColumnInfo(name="id", kind="pk", nullable=False, is_pk=True, is_fk=False),
        ])]
        assert auto_node_width(tables) == NODE_W

    def test_long_names_exceed_default(self):
        tables = [TableInfo(name="t", class_name="T", columns=[
            ColumnInfo(name="nombre_actividad_economica_principal", kind="string", nullable=False, is_pk=False, is_fk=False),
        ])]
        assert auto_node_width(tables) > NODE_W

    def test_long_class_name_exceeds_default(self):
        tables = [TableInfo(name="t", class_name="EstablecimientosDeSaludPublicosYPrivados", columns=[
            ColumnInfo(name="id", kind="pk", nullable=False, is_pk=True, is_fk=False),
        ])]
        assert auto_node_width(tables) > NODE_W

    def test_nullable_suffix_included(self):
        col = ColumnInfo(name="x" * 30, kind="datetime", nullable=True, is_pk=False, is_fk=False)
        tables_nullable = [TableInfo(name="t", class_name="T", columns=[col])]
        col_non_null = ColumnInfo(name="x" * 30, kind="datetime", nullable=False, is_pk=False, is_fk=False)
        tables_non_null = [TableInfo(name="t", class_name="T", columns=[col_non_null])]
        assert auto_node_width(tables_nullable) >= auto_node_width(tables_non_null)

    def test_empty_tables(self):
        assert auto_node_width([]) == NODE_W


# ── node_w parameter ──────────────────────────────────────────────────────

class TestNodeWParam:
    def test_force_layout_uses_node_w(self):
        cols = [ColumnInfo(name="id", kind="pk", nullable=False, is_pk=True, is_fk=False)]
        tables = [
            TableInfo(name=f"t{i}", class_name=f"T{i}", columns=list(cols))
            for i in range(6)
        ]
        rels = [
            RelationshipInfo(from_table=f"t{i}", to_table=f"t{i+1}", from_card="1", to_card="N", fk_column="id")
            for i in range(5)
        ]
        pos_default = force_directed_layout(tables, rels, seed=42, node_w=218)
        pos_wide = force_directed_layout(tables, rels, seed=42, node_w=500)
        assert pos_default != pos_wide

    def test_star_layout_uses_node_w(self):
        fact = TableInfo(name="fact", class_name="Fact", columns=[
            ColumnInfo(name="id", kind="pk", nullable=False, is_pk=True, is_fk=False),
            ColumnInfo(name="a_id", kind="fk", nullable=False, is_pk=False, is_fk=True),
            ColumnInfo(name="b_id", kind="fk", nullable=False, is_pk=False, is_fk=True),
        ])
        cat = lambda name: TableInfo(name=name, class_name=name.upper(), columns=[
            ColumnInfo(name="id", kind="pk", nullable=False, is_pk=True, is_fk=False),
        ])
        tables = [cat("a"), cat("b"), fact]
        rels = [
            RelationshipInfo(from_table="a", to_table="fact", from_card="1", to_card="N", fk_column="a_id"),
            RelationshipInfo(from_table="b", to_table="fact", from_card="1", to_card="N", fk_column="b_id"),
        ]
        pos_default = star_layout(tables, rels)
        pos_wide = star_layout(tables, rels, node_w=400)
        spread_default = max(x for x, _ in pos_default.values()) - min(x for x, _ in pos_default.values())
        spread_wide = max(x for x, _ in pos_wide.values()) - min(x for x, _ in pos_wide.values())
        assert spread_wide > spread_default
