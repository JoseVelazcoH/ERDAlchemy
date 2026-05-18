"""Tests for sqlalchemy_erd.introspect — metadata extraction, relationships, association tables."""

from __future__ import annotations

from sqlalchemy_erd.introspect import (
    introspect_models,
    _classify_type,
    _column_kind,
    ColumnInfo,
    TableInfo,
    RelationshipInfo,
)
from sqlalchemy import Integer, String, Text, Float, Boolean, JSON, DateTime, Date
from sqlalchemy import BigInteger, SmallInteger, Numeric, Uuid


# ── _classify_type ───────────────────────────────────────────────────────────

class TestClassifyType:
    def test_integer(self):
        assert _classify_type(Integer()) == "int"

    def test_bigint(self):
        assert _classify_type(BigInteger()) == "bigint"

    def test_smallint(self):
        assert _classify_type(SmallInteger()) == "smallint"

    def test_string(self):
        assert _classify_type(String(100)) == "string"

    def test_text(self):
        assert _classify_type(Text()) == "text"

    def test_float(self):
        assert _classify_type(Float()) == "float"

    def test_numeric(self):
        assert _classify_type(Numeric(10, 2)) == "numeric"

    def test_datetime(self):
        assert _classify_type(DateTime()) == "datetime"

    def test_date(self):
        assert _classify_type(Date()) == "date"

    def test_boolean(self):
        assert _classify_type(Boolean()) == "bool"

    def test_json(self):
        assert _classify_type(JSON()) == "json"

    def test_uuid(self):
        assert _classify_type(Uuid()) == "uuid"

    def test_unknown_type(self):
        class CustomType:
            pass
        assert _classify_type(CustomType()) == "other"


# ── _column_kind ─────────────────────────────────────────────────────────────

class TestColumnKind:
    def test_pk_overrides_type(self):
        assert _column_kind(type("C", (), {"type": String(50)})(), is_pk=True, is_fk=False) == "pk"

    def test_fk_overrides_type(self):
        assert _column_kind(type("C", (), {"type": Integer()})(), is_pk=False, is_fk=True) == "fk"

    def test_regular_column_uses_type(self):
        assert _column_kind(type("C", (), {"type": Boolean()})(), is_pk=False, is_fk=False) == "bool"


# ── introspect_models — basic extraction ─────────────────────────────────────

class TestIntrospectBasic:
    def test_empty_schema(self, empty_base):
        tables, rels = introspect_models(empty_base)
        assert tables == []
        assert rels == []

    def test_single_table(self, single_table_base):
        tables, rels = introspect_models(single_table_base)
        assert len(tables) == 1
        assert tables[0].name == "standalone"
        assert tables[0].class_name == "Standalone"
        assert rels == []

    def test_single_table_columns(self, single_table_base):
        tables, _ = introspect_models(single_table_base)
        col_names = [c.name for c in tables[0].columns]
        assert "id" in col_names
        assert "name" in col_names

    def test_pk_detected(self, single_table_base):
        tables, _ = introspect_models(single_table_base)
        id_col = next(c for c in tables[0].columns if c.name == "id")
        assert id_col.is_pk is True
        assert id_col.kind == "pk"

    def test_non_pk_column(self, single_table_base):
        tables, _ = introspect_models(single_table_base)
        name_col = next(c for c in tables[0].columns if c.name == "name")
        assert name_col.is_pk is False
        assert name_col.kind == "string"


# ── introspect_models — relationships (1:N) ──────────────────────────────────

class TestIntrospectRelationships:
    def test_blog_table_count(self, blog_base):
        tables, _ = introspect_models(blog_base)
        assert len(tables) == 3

    def test_blog_table_names(self, blog_base):
        tables, _ = introspect_models(blog_base)
        names = {t.name for t in tables}
        assert names == {"users", "posts", "comments"}

    def test_blog_class_names(self, blog_base):
        tables, _ = introspect_models(blog_base)
        class_names = {t.class_name for t in tables}
        assert class_names == {"User", "Post", "Comment"}

    def test_blog_relationship_count(self, blog_base):
        _, rels = introspect_models(blog_base)
        assert len(rels) == 3

    def test_blog_relationship_cardinality(self, blog_base):
        _, rels = introspect_models(blog_base)
        for rel in rels:
            assert rel.from_card == "1"
            assert rel.to_card == "N"

    def test_fk_columns_detected(self, blog_base):
        tables, _ = introspect_models(blog_base)
        posts = next(t for t in tables if t.name == "posts")
        author_id_col = next(c for c in posts.columns if c.name == "author_id")
        assert author_id_col.is_fk is True
        assert author_id_col.kind == "fk"

    def test_relationship_from_to(self, blog_base):
        _, rels = introspect_models(blog_base)
        pairs = {(r.from_table, r.to_table) for r in rels}
        assert ("users", "posts") in pairs
        assert ("users", "comments") in pairs
        assert ("posts", "comments") in pairs

    def test_nullable_column(self, blog_base):
        tables, _ = introspect_models(blog_base)
        users = next(t for t in tables if t.name == "users")
        bio_col = next(c for c in users.columns if c.name == "bio")
        assert bio_col.nullable is True

    def test_non_nullable_column(self, blog_base):
        tables, _ = introspect_models(blog_base)
        users = next(t for t in tables if t.name == "users")
        username_col = next(c for c in users.columns if c.name == "username")
        assert username_col.nullable is False


# ── introspect_models — association tables (M:N) ─────────────────────────────

class TestIntrospectAssociation:
    def test_association_table_removed(self, m2m_base):
        tables, _ = introspect_models(m2m_base)
        names = {t.name for t in tables}
        assert "student_courses" not in names

    def test_m2m_tables_remain(self, m2m_base):
        tables, _ = introspect_models(m2m_base)
        names = {t.name for t in tables}
        assert names == {"students", "courses"}

    def test_m2m_relationship(self, m2m_base):
        _, rels = introspect_models(m2m_base)
        assert len(rels) == 1
        rel = rels[0]
        assert rel.from_card == "N"
        assert rel.to_card == "N"
        assert "via" in rel.fk_column

    def test_m2m_connects_correct_tables(self, m2m_base):
        _, rels = introspect_models(m2m_base)
        rel = rels[0]
        pair = {rel.from_table, rel.to_table}
        assert pair == {"students", "courses"}


# ── introspect_models — circular FKs ─────────────────────────────────────────

class TestIntrospectCircular:
    def test_circular_tables(self, circular_metadata_fixture):
        tables, _ = introspect_models(circular_metadata_fixture)
        names = {t.name for t in tables}
        assert names == {"departments", "employees"}

    def test_circular_relationships(self, circular_metadata_fixture):
        _, rels = introspect_models(circular_metadata_fixture)
        assert len(rels) == 2
        pairs = {(r.from_table, r.to_table) for r in rels}
        assert ("employees", "departments") in pairs
        assert ("departments", "employees") in pairs


# ── introspect_models — all column types ─────────────────────────────────────

class TestIntrospectColumnTypes:
    def test_all_types_detected(self, types_base):
        tables, _ = introspect_models(types_base)
        assert len(tables) == 1
        table = tables[0]
        kinds = {c.name: c.kind for c in table.columns}
        assert kinds["id"] == "pk"
        assert kinds["big"] == "bigint"
        assert kinds["small"] == "smallint"
        assert kinds["floating"] == "float"
        assert kinds["decimal_col"] == "numeric"
        assert kinds["text_col"] == "text"
        assert kinds["string_col"] == "string"
        assert kinds["date_col"] == "date"
        assert kinds["datetime_col"] == "datetime"
        assert kinds["bool_col"] == "bool"
        assert kinds["json_col"] == "json"


# ── introspect_models — MetaData input ───────────────────────────────────────

class TestIntrospectMetadata:
    def test_metadata_input(self, blog_base):
        tables, rels = introspect_models(blog_base.metadata)
        assert len(tables) == 3
        assert len(rels) == 3

    def test_metadata_uses_table_name_as_class_name(self, blog_base):
        tables, _ = introspect_models(blog_base.metadata)
        for t in tables:
            assert t.class_name == t.name


# ── introspect_models — multi-schema ─────────────────────────────────────────

class TestIntrospectMultiSchema:
    def test_multi_schema_tables(self, multi_schema_metadata_fixture):
        tables, _ = introspect_models(multi_schema_metadata_fixture)
        assert len(tables) == 2

    def test_multi_schema_display_names(self, multi_schema_metadata_fixture):
        tables, _ = introspect_models(multi_schema_metadata_fixture)
        class_names = {t.class_name for t in tables}
        assert "auth.accounts" in class_names
        assert "billing.orders" in class_names

    def test_multi_schema_cross_fk(self, multi_schema_metadata_fixture):
        _, rels = introspect_models(multi_schema_metadata_fixture)
        assert len(rels) == 1
        rel = rels[0]
        assert rel.from_table == "auth.accounts"
        assert rel.to_table == "billing.orders"

    def test_schema_filter(self, multi_schema_metadata_fixture):
        tables, rels = introspect_models(
            multi_schema_metadata_fixture, schemas=["auth"],
        )
        assert len(tables) == 1
        assert tables[0].schema == "auth"

    def test_schema_attribute_set(self, multi_schema_metadata_fixture):
        tables, _ = introspect_models(multi_schema_metadata_fixture)
        schemas = {t.schema for t in tables}
        assert schemas == {"auth", "billing"}
