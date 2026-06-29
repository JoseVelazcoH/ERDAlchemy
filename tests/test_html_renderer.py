"""Tests for sqlalchemy_erd.html_renderer — interactive HTML output and its JSON payloads."""

import json
import re

from sqlalchemy_erd.force import force_directed_layout
from sqlalchemy_erd.html_renderer import render_html
from sqlalchemy_erd.introspect import introspect_models
from sqlalchemy_erd.serialization import (
    build_entities_json as _build_entities_json,
    build_relations_json as _build_relations_json,
)
from sqlalchemy_erd.theme import get_theme


def _prepare(base):
    tables, rels = introspect_models(base)
    positions = force_directed_layout(tables, rels)
    theme = get_theme("default")
    return tables, rels, positions, theme


def _entities(base):
    tables, rels = introspect_models(base)
    return json.loads(_build_entities_json(tables, get_theme("default")))


def _field(entity, name):
    for f in entity["fields"]:
        if f["name"] == name:
            return f
    raise AssertionError(f"field {name!r} not found in {entity['id']}")


def _entity(entities, table_name):
    for e in entities:
        if e["id"] == table_name:
            return e
    raise AssertionError(f"entity {table_name!r} not found")


# ── _build_entities_json ─────────────────────────────────────────────────────

class TestBuildEntitiesJson:
    def test_returns_valid_json_list(self, blog_base):
        tables, _ = introspect_models(blog_base)
        result = _build_entities_json(tables, get_theme("default"))
        parsed = json.loads(result)
        assert isinstance(parsed, list)

    def test_entity_has_expected_keys(self, blog_base):
        entities = _entities(blog_base)
        entity = _entity(entities, "users")
        assert set(entity) == {"id", "label", "schema", "headerColor", "hoverColor", "fields"}

    def test_entity_count_matches_table_count(self, blog_base):
        tables, _ = introspect_models(blog_base)
        entities = _entities(blog_base)
        assert len(entities) == len(tables)

    def test_pk_field_has_bold_weight(self, blog_base):
        entities = _entities(blog_base)
        pk_field = _field(_entity(entities, "users"), "id")
        assert pk_field["nameWeight"] == "700"

    def test_non_pk_field_has_normal_weight(self, blog_base):
        entities = _entities(blog_base)
        field = _field(_entity(entities, "users"), "username")
        assert field["nameWeight"] == "400"

    def test_fk_field_uses_fk_name_color(self, blog_base):
        entities = _entities(blog_base)
        fk_field = _field(_entity(entities, "posts"), "author_id")
        assert fk_field["nameColor"] == "#9a3412"

    def test_nullable_non_key_field_gets_question_mark(self, blog_base):
        entities = _entities(blog_base)
        # User.bio is a nullable Text column, neither pk nor fk
        bio = _field(_entity(entities, "users"), "bio")
        assert bio["kindLabel"].endswith("?")

    def test_non_nullable_field_has_no_question_mark(self, blog_base):
        entities = _entities(blog_base)
        username = _field(_entity(entities, "users"), "username")
        assert not username["kindLabel"].endswith("?")

    def test_header_color_uses_theme_default(self, blog_base):
        entities = _entities(blog_base)
        theme = get_theme("default")
        assert _entity(entities, "users")["headerColor"] == theme.header_color

    def test_per_table_color_override_applied(self, blog_base):
        tables, _ = introspect_models(blog_base)
        theme = get_theme("default", table_colors={"users": "#ff0000"})
        entities = json.loads(_build_entities_json(tables, theme))
        assert _entity(entities, "users")["headerColor"] == "#ff0000"

    def test_column_comment_is_serialized(self, comments_metadata_fixture):
        tables, _ = introspect_models(comments_metadata_fixture)
        entities = json.loads(_build_entities_json(tables, get_theme("default")))
        email = _field(_entity(entities, "accounts"), "email")
        assert email["comment"] == "Primary login email"


# ── _build_relations_json ────────────────────────────────────────────────────

class TestBuildRelationsJson:
    def test_returns_valid_json_list(self, blog_base):
        tables, rels = introspect_models(blog_base)
        positions = force_directed_layout(tables, rels)
        result = _build_relations_json(rels, tables, positions)
        assert isinstance(json.loads(result), list)

    def test_relation_has_expected_keys(self, blog_base):
        tables, rels = introspect_models(blog_base)
        positions = force_directed_layout(tables, rels)
        parsed = json.loads(_build_relations_json(rels, tables, positions))
        assert set(parsed[0]) == {"from", "to", "fromCard", "toCard", "fkCol"}

    def test_via_relation_keeps_via_prefix(self, m2m_base):
        tables, rels = introspect_models(m2m_base)
        positions = force_directed_layout(tables, rels)
        parsed = json.loads(_build_relations_json(rels, tables, positions))
        assert any(r["fkCol"].startswith("via ") for r in parsed)

    def test_relation_to_unknown_table_is_filtered_out(self, blog_base):
        tables, rels = introspect_models(blog_base)
        positions = force_directed_layout(tables, rels)
        # Drop one table so its relations become dangling
        kept = [t for t in tables if t.name != "comments"]
        parsed = json.loads(_build_relations_json(rels, kept, positions))
        assert all(r["from"] != "comments" and r["to"] != "comments" for r in parsed)


# ── render_html ──────────────────────────────────────────────────────────────

def _extract_js_object(html, var_name):
    match = re.search(rf"const {var_name} = (.*?);\n", html)
    assert match, f"{var_name} not found in HTML"
    return json.loads(match.group(1))


class TestRenderHtml:
    def test_returns_string(self, blog_base):
        tables, rels, positions, theme = _prepare(blog_base)
        assert isinstance(render_html(tables, rels, positions, theme), str)

    def test_contains_doctype(self, blog_base):
        tables, rels, positions, theme = _prepare(blog_base)
        assert render_html(tables, rels, positions, theme).startswith("<!DOCTYPE html>")

    def test_title_is_escaped(self, blog_base):
        tables, rels, positions, theme = _prepare(blog_base)
        html = render_html(tables, rels, positions, theme, title="<script>")
        assert "<title>&lt;script&gt;</title>" in html

    def test_embeds_parseable_entities(self, blog_base):
        tables, rels, positions, theme = _prepare(blog_base)
        html = render_html(tables, rels, positions, theme)
        entities = _extract_js_object(html, "ENTITIES")
        assert {e["id"] for e in entities} == {t.name for t in tables}

    def test_embeds_parseable_relations(self, blog_base):
        tables, rels, positions, theme = _prepare(blog_base)
        html = render_html(tables, rels, positions, theme)
        relations = _extract_js_object(html, "RELATIONS")
        assert isinstance(relations, list)

    def test_embeds_node_width(self, blog_base):
        tables, rels, positions, theme = _prepare(blog_base)
        html = render_html(tables, rels, positions, theme, node_w=400)
        assert "const NODE_W = 400;" in html

    def test_empty_schema_still_renders(self, empty_base):
        tables, rels, positions, theme = _prepare(empty_base)
        html = render_html(tables, rels, positions, theme)
        assert "<!DOCTYPE html>" in html
        assert _extract_js_object(html, "ENTITIES") == []

    def test_html_contains_tooltip_binding(self, comments_metadata_fixture):
        tables, rels = introspect_models(comments_metadata_fixture)
        positions = force_directed_layout(tables, rels)
        html = render_html(tables, rels, positions, get_theme("default"))
        assert "field.comment" in html
        assert "Primary login email" in html
