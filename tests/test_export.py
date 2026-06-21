"""Tests for sqlalchemy_erd.export — HTML, SVG, PNG, PDF output."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from sqlalchemy_erd.introspect import introspect_models
from sqlalchemy_erd.force import force_directed_layout
from sqlalchemy_erd.export import to_html, to_svg, to_png, to_pdf
from sqlalchemy_erd.theme import get_theme


def _prepare(base):
    tables, rels = introspect_models(base)
    positions = force_directed_layout(tables, rels)
    theme = get_theme("default")
    return tables, rels, positions, theme


# ── to_svg ───────────────────────────────────────────────────────────────────

class TestToSvg:
    def test_returns_string(self, blog_base):
        tables, rels, positions, theme = _prepare(blog_base)
        result = to_svg(tables, rels, positions, theme)
        assert isinstance(result, str)

    def test_includes_xml_header(self, blog_base):
        tables, rels, positions, theme = _prepare(blog_base)
        result = to_svg(tables, rels, positions, theme)
        assert result.startswith("<?xml")

    def test_valid_xml(self, blog_base):
        tables, rels, positions, theme = _prepare(blog_base)
        result = to_svg(tables, rels, positions, theme)
        ET.fromstring(result)

    def test_empty_schema(self, empty_base):
        tables, rels, positions, theme = _prepare(empty_base)
        result = to_svg(tables, rels, positions, theme)
        assert isinstance(result, str)
        ET.fromstring(result)


# ── to_html ──────────────────────────────────────────────────────────────────

class TestToHtml:
    def test_returns_string(self, blog_base):
        tables, rels, positions, theme = _prepare(blog_base)
        result = to_html(tables, rels, positions, theme)
        assert isinstance(result, str)

    def test_contains_doctype(self, blog_base):
        tables, rels, positions, theme = _prepare(blog_base)
        result = to_html(tables, rels, positions, theme)
        assert "<!DOCTYPE html>" in result

    def test_contains_svg_element(self, blog_base):
        tables, rels, positions, theme = _prepare(blog_base)
        result = to_html(tables, rels, positions, theme)
        assert '<svg id="erd"' in result

    def test_contains_entities_data(self, blog_base):
        tables, rels, positions, theme = _prepare(blog_base)
        result = to_html(tables, rels, positions, theme)
        assert "ENTITIES" in result
        assert "RELATIONS" in result

    def test_custom_title(self, blog_base):
        tables, rels, positions, theme = _prepare(blog_base)
        result = to_html(tables, rels, positions, theme, title="My Blog")
        assert "<title>My Blog</title>" in result

    def test_default_title(self, blog_base):
        tables, rels, positions, theme = _prepare(blog_base)
        result = to_html(tables, rels, positions, theme)
        assert "<title>ERD</title>" in result

    def test_contains_table_names(self, blog_base):
        tables, rels, positions, theme = _prepare(blog_base)
        result = to_html(tables, rels, positions, theme)
        assert "users" in result
        assert "posts" in result
        assert "comments" in result

    def test_empty_schema(self, empty_base):
        tables, rels, positions, theme = _prepare(empty_base)
        result = to_html(tables, rels, positions, theme)
        assert isinstance(result, str)
        assert "<!DOCTYPE html>" in result


# ── to_png ───────────────────────────────────────────────────────────────────

class TestToPng:
    def test_returns_bytes(self, blog_base):
        tables, rels, positions, theme = _prepare(blog_base)
        result = to_png(tables, rels, positions, theme)
        assert isinstance(result, bytes)

    def test_png_header(self, blog_base):
        tables, rels, positions, theme = _prepare(blog_base)
        result = to_png(tables, rels, positions, theme)
        assert result[:8] == b"\x89PNG\r\n\x1a\n"

    def test_scale_parameter(self, blog_base):
        tables, rels, positions, theme = _prepare(blog_base)
        small = to_png(tables, rels, positions, theme, scale=1)
        large = to_png(tables, rels, positions, theme, scale=3)
        assert len(large) > len(small)

    def test_empty_schema(self, empty_base):
        tables, rels, positions, theme = _prepare(empty_base)
        result = to_png(tables, rels, positions, theme)
        assert isinstance(result, bytes)


# ── to_pdf ───────────────────────────────────────────────────────────────────

class TestToPdf:
    def test_returns_bytes(self, blog_base):
        tables, rels, positions, theme = _prepare(blog_base)
        result = to_pdf(tables, rels, positions, theme)
        assert isinstance(result, bytes)

    def test_pdf_header(self, blog_base):
        tables, rels, positions, theme = _prepare(blog_base)
        result = to_pdf(tables, rels, positions, theme)
        assert result[:5] == b"%PDF-"

    def test_empty_schema(self, empty_base):
        tables, rels, positions, theme = _prepare(empty_base)
        result = to_pdf(tables, rels, positions, theme)
        assert isinstance(result, bytes)
