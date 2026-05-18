"""Tests for sqlalchemy_erd.theme — themes, schema colors, kind maps."""

from __future__ import annotations

import pytest

from sqlalchemy_erd.theme import (
    Theme,
    THEMES,
    get_theme,
    apply_schema_colors,
    SCHEMA_PALETTE,
    DEFAULT_KIND_COLORS,
    DEFAULT_KIND_LABELS,
)
from sqlalchemy_erd.introspect import TableInfo, ColumnInfo


class TestThemeDefaults:
    def test_default_theme_exists(self):
        assert "default" in THEMES

    def test_all_themes_valid(self):
        for name, theme in THEMES.items():
            assert theme.name == name
            assert theme.header_color.startswith("#")
            assert theme.bg_color.startswith("#")

    def test_kind_colors_complete(self):
        expected = {"pk", "fk", "int", "bigint", "smallint", "float", "numeric",
                    "string", "text", "date", "datetime", "json", "bool", "uuid", "other"}
        assert set(DEFAULT_KIND_COLORS.keys()) == expected

    def test_kind_labels_complete(self):
        assert set(DEFAULT_KIND_LABELS.keys()) == set(DEFAULT_KIND_COLORS.keys())


class TestGetTheme:
    def test_get_by_name(self):
        theme = get_theme("dark")
        assert theme.name == "dark"

    def test_get_returns_copy(self):
        t1 = get_theme("default")
        t2 = get_theme("default")
        t1.header_color = "#000000"
        assert t2.header_color != "#000000"

    def test_get_with_table_colors(self):
        theme = get_theme("default", table_colors={"users": "#ff0000"})
        assert theme.table_colors["users"] == "#ff0000"

    def test_get_unknown_theme_raises(self):
        with pytest.raises(ValueError, match="Unknown theme"):
            get_theme("nonexistent")

    def test_pass_theme_instance(self):
        original = Theme(name="custom", header_color="#123456")
        result = get_theme(original)
        assert result.header_color == "#123456"
        assert result is not original

    def test_get_header_color_default(self):
        theme = get_theme("default")
        assert theme.get_header_color("unknown_table") == theme.header_color

    def test_get_header_color_override(self):
        theme = get_theme("default", table_colors={"users": "#aabbcc"})
        assert theme.get_header_color("users") == "#aabbcc"


class TestApplySchemaColors:
    def _make_tables(self, schemas):
        tables = []
        for i, schema in enumerate(schemas):
            tables.append(TableInfo(
                name=f"{schema}.t{i}" if schema else f"t{i}",
                class_name=f"T{i}",
                schema=schema,
                columns=[ColumnInfo(name="id", kind="pk", nullable=False, is_pk=True, is_fk=False)],
            ))
        return tables

    def test_single_schema_no_colors(self):
        theme = get_theme("default")
        tables = self._make_tables(["public", "public"])
        apply_schema_colors(theme, tables)
        assert theme.schema_colors == {}

    def test_multi_schema_assigns_colors(self):
        theme = get_theme("default")
        tables = self._make_tables(["auth", "billing"])
        apply_schema_colors(theme, tables)
        assert len(theme.schema_colors) == 2
        assert "auth" in theme.schema_colors
        assert "billing" in theme.schema_colors

    def test_schema_colors_from_palette(self):
        theme = get_theme("default")
        tables = self._make_tables(["a", "b", "c"])
        apply_schema_colors(theme, tables)
        for color in theme.schema_colors.values():
            assert color in SCHEMA_PALETTE

    def test_table_colors_populated(self):
        theme = get_theme("default")
        tables = self._make_tables(["auth", "billing"])
        apply_schema_colors(theme, tables)
        for t in tables:
            assert t.name in theme.table_colors

    def test_existing_table_color_preserved(self):
        theme = get_theme("default", table_colors={"auth.t0": "#custom"})
        tables = self._make_tables(["auth", "billing"])
        apply_schema_colors(theme, tables)
        assert theme.table_colors["auth.t0"] == "#custom"
