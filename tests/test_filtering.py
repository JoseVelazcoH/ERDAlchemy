"""Tests for regex table/column filtering in introspect_models."""

from sqlalchemy_erd.introspect import Filters, introspect_models


def _names(tables) -> set[str]:
    return {t.name for t in tables}


class TestIncludeTables:
    def test_include_limits_to_matching_table(self, blog_base):
        tables, _ = introspect_models(blog_base, filters=Filters(include_tables=["posts"]))
        assert _names(tables) == {"posts"}

    def test_include_regex_matches_a_family(self, blog_base):
        tables, _ = introspect_models(
            blog_base, filters=Filters(include_tables=["post.*", "comment.*"]),
        )
        assert _names(tables) == {"posts", "comments"}

    def test_include_pattern_is_full_string_anchored(self, blog_base):
        # "post" must not match "posts"
        tables, _ = introspect_models(blog_base, filters=Filters(include_tables=["post"]))
        assert _names(tables) == set()


class TestExcludeTables:
    def test_exclude_removes_matching_table(self, blog_base):
        tables, _ = introspect_models(blog_base, filters=Filters(exclude_tables=["comments"]))
        assert "comments" not in _names(tables)
        assert "users" in _names(tables)

    def test_exclude_regex_removes_a_family(self, blog_base):
        tables, _ = introspect_models(
            blog_base, filters=Filters(exclude_tables=["post.*", "comment.*"]),
        )
        assert _names(tables) == {"users"}


class TestPrecedence:
    def test_exclude_is_applied_after_include(self, blog_base):
        tables, _ = introspect_models(
            blog_base,
            filters=Filters(include_tables=[".*"], exclude_tables=["comments"]),
        )
        assert "comments" not in _names(tables)
        assert {"users", "posts"} <= _names(tables)


class TestRelationshipsToExcludedTables:
    def test_relationships_only_reference_kept_tables(self, blog_base):
        tables, relationships = introspect_models(
            blog_base, filters=Filters(exclude_tables=["users"]),
        )
        names = _names(tables)
        for rel in relationships:
            assert rel.from_table in names
            assert rel.to_table in names


class TestExcludeColumns:
    def test_excluded_column_is_hidden_from_every_card(self, blog_base):
        tables, _ = introspect_models(blog_base, filters=Filters(exclude_columns=["created_at"]))
        for table in tables:
            assert all(col.name != "created_at" for col in table.columns)

    def test_exclude_columns_regex_hides_a_family(self, blog_base):
        tables, _ = introspect_models(blog_base, filters=Filters(exclude_columns=[".*_at"]))
        for table in tables:
            assert all(not col.name.endswith("_at") for col in table.columns)

    def test_hiding_an_fk_column_keeps_its_relationship(self, blog_base):
        tables, relationships = introspect_models(
            blog_base, filters=Filters(exclude_columns=["author_id"]),
        )
        posts = next(t for t in tables if t.name == "posts")
        assert all(col.name != "author_id" for col in posts.columns)
        assert any(
            rel.from_table == "users" and rel.to_table == "posts"
            for rel in relationships
        )


class TestNoFilters:
    def test_default_filters_keep_everything(self, blog_base):
        baseline, _ = introspect_models(blog_base)
        filtered, _ = introspect_models(blog_base, filters=Filters())
        assert _names(baseline) == _names(filtered)
