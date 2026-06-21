"""Tests for sqlalchemy_erd.renderer — SVG output validity and structure."""

import xml.etree.ElementTree as ET

from sqlalchemy_erd.force import force_directed_layout
from sqlalchemy_erd.introspect import introspect_models
from sqlalchemy_erd.renderer import render_svg, _best_side, _conn_pt, _side_vec
from sqlalchemy_erd.theme import get_theme
from sqlalchemy_erd.introspect import TableInfo, ColumnInfo


# ── SVG validity ─────────────────────────────────────────────────────────────

class TestSvgValidity:
    def test_valid_xml(self, blog_base):
        tables, rels = introspect_models(blog_base)
        positions = force_directed_layout(tables, rels)
        theme = get_theme("default")
        svg = render_svg(tables, rels, positions, theme)
        ET.fromstring(svg)

    def test_valid_xml_with_header(self, blog_base):
        tables, rels = introspect_models(blog_base)
        positions = force_directed_layout(tables, rels)
        theme = get_theme("default")
        svg = render_svg(tables, rels, positions, theme, include_xml_header=True)
        ET.fromstring(svg)

    def test_root_is_svg(self, blog_base):
        tables, rels = introspect_models(blog_base)
        positions = force_directed_layout(tables, rels)
        theme = get_theme("default")
        svg = render_svg(tables, rels, positions, theme)
        root = ET.fromstring(svg)
        assert root.tag == "{http://www.w3.org/2000/svg}svg"


# ── SVG structure ────────────────────────────────────────────────────────────

NS = {"svg": "http://www.w3.org/2000/svg"}


class TestSvgStructure:
    def _render_blog(self, blog_base):
        tables, rels = introspect_models(blog_base)
        positions = force_directed_layout(tables, rels)
        theme = get_theme("default")
        svg = render_svg(tables, rels, positions, theme)
        return ET.fromstring(svg), tables, rels

    def test_has_defs(self, blog_base):
        root, _, _ = self._render_blog(blog_base)
        defs = root.find("svg:defs", NS)
        assert defs is not None

    def test_has_background_rects(self, blog_base):
        root, _, _ = self._render_blog(blog_base)
        rects = root.findall("svg:rect", NS)
        assert len(rects) >= 2

    def test_node_groups(self, blog_base):
        root, tables, _ = self._render_blog(blog_base)
        node_groups = [g for g in root.findall("svg:g", NS) if g.get("class") == "erd-node"]
        assert len(node_groups) == len(tables)

    def test_node_data_table_attr(self, blog_base):
        root, tables, _ = self._render_blog(blog_base)
        node_groups = [g for g in root.findall("svg:g", NS) if g.get("class") == "erd-node"]
        data_tables = {g.get("data-table") for g in node_groups}
        expected = {t.name for t in tables}
        assert data_tables == expected

    def test_rel_groups(self, blog_base):
        root, _, rels = self._render_blog(blog_base)
        rel_groups = [g for g in root.findall("svg:g", NS) if g.get("class") == "erd-rel"]
        assert len(rel_groups) == len(rels)

    def test_has_markers(self, blog_base):
        root, _, _ = self._render_blog(blog_base)
        defs = root.find("svg:defs", NS)
        markers = defs.findall("svg:marker", NS)
        assert len(markers) >= 2

    def test_table_name_in_text(self, blog_base):
        root, tables, _ = self._render_blog(blog_base)
        all_text = " ".join(t.text or "" for t in root.iter("{http://www.w3.org/2000/svg}text"))
        for table in tables:
            assert table.class_name in all_text

    def test_single_table_no_rels(self, single_table_base):
        tables, rels = introspect_models(single_table_base)
        positions = force_directed_layout(tables, rels)
        theme = get_theme("default")
        svg = render_svg(tables, rels, positions, theme)
        root = ET.fromstring(svg)
        rel_groups = [g for g in root.findall("svg:g", NS) if g.get("class") == "erd-rel"]
        assert len(rel_groups) == 0

    def test_dimensions_fit_content(self, blog_base):
        root, _, _ = self._render_blog(blog_base)
        w = float(root.get("width"))
        h = float(root.get("height"))
        assert w > 0
        assert h > 0


# ── Helper functions ─────────────────────────────────────────────────────────

class TestHelperFunctions:
    def _make_table(self, ncols):
        cols = [ColumnInfo(name=f"c{i}", kind="int", nullable=False, is_pk=False, is_fk=False) for i in range(ncols)]
        return TableInfo(name="t", class_name="T", columns=cols)

    def test_best_side_horizontal(self):
        t1 = self._make_table(2)
        t2 = self._make_table(2)
        fs, ts = _best_side((0, 100), t1, (500, 100), t2)
        assert fs == "right"
        assert ts == "left"

    def test_best_side_vertical(self):
        t1 = self._make_table(2)
        t2 = self._make_table(2)
        fs, ts = _best_side((100, 0), t1, (100, 500), t2)
        assert fs == "bottom"
        assert ts == "top"

    def test_side_vec_top(self):
        assert _side_vec("top", 10) == (0, -10)

    def test_side_vec_bottom(self):
        assert _side_vec("bottom", 10) == (0, 10)

    def test_side_vec_left(self):
        assert _side_vec("left", 10) == (-10, 0)

    def test_side_vec_right(self):
        assert _side_vec("right", 10) == (10, 0)


# ── Theme variations ─────────────────────────────────────────────────────────

class TestThemeRendering:
    def test_dark_theme_valid_svg(self, blog_base):
        tables, rels = introspect_models(blog_base)
        positions = force_directed_layout(tables, rels)
        theme = get_theme("dark")
        svg = render_svg(tables, rels, positions, theme)
        ET.fromstring(svg)

    def test_all_themes_produce_valid_svg(self, blog_base):
        from sqlalchemy_erd.theme import THEMES
        tables, rels = introspect_models(blog_base)
        positions = force_directed_layout(tables, rels)
        for name in THEMES:
            theme = get_theme(name)
            svg = render_svg(tables, rels, positions, theme)
            ET.fromstring(svg)

    def test_custom_table_colors(self, blog_base):
        tables, rels = introspect_models(blog_base)
        positions = force_directed_layout(tables, rels)
        theme = get_theme("default", table_colors={"users": "#ff0000"})
        svg = render_svg(tables, rels, positions, theme)
        assert "#ff0000" in svg
