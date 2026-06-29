import re
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import (
    ARRAY, BigInteger, Boolean, Date, DateTime, Enum, Float, Integer,
    Interval, JSON, LargeBinary, MetaData, Numeric, SmallInteger, String,
    Text, Time, Uuid,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import TypeDecorator


@dataclass
class ColumnInfo:
    name: str
    kind: str
    nullable: bool
    is_pk: bool
    is_fk: bool


@dataclass
class TableInfo:
    name: str
    class_name: str
    schema: str | None = None
    columns: list[ColumnInfo] = field(default_factory=list)
    kind: str = "table"


@dataclass
class RelationshipInfo:
    from_table: str
    to_table: str
    from_card: str
    to_card: str
    fk_column: str


@dataclass(frozen=True)
class Filters:
    """Regex filters applied during introspection.

    Patterns match the full table/column name (anchored). ``include_tables``
    takes precedence: when set, only matching tables survive; ``exclude_tables``
    is then applied to what remains. ``exclude_columns`` hides columns from the
    cards without dropping the foreign-key relationships they carry.
    """

    include_tables: list[str] | None = None
    exclude_tables: list[str] | None = None
    exclude_columns: list[str] | None = None


def _compile(patterns: list[str] | None) -> list[re.Pattern[str]] | None:
    if patterns is None:
        return None
    return [re.compile(rf"(?:{pattern})\Z") for pattern in patterns]


def _matches_any(name: str, compiled: list[re.Pattern[str]] | None) -> bool:
    return compiled is not None and any(p.match(name) for p in compiled)


def _is_table_kept(
    name: str,
    include: list[re.Pattern[str]] | None,
    exclude: list[re.Pattern[str]] | None,
) -> bool:
    if include is not None and not _matches_any(name, include):
        return False
    return not _matches_any(name, exclude)


_TYPE_MAP: list[tuple[type, str]] = [
    (BigInteger, "bigint"),
    (SmallInteger, "smallint"),
    (Integer, "int"),
    (Enum, "enum"),
    (Text, "text"),
    (String, "string"),
    (Float, "float"),
    (Numeric, "numeric"),
    (Interval, "interval"),
    (DateTime, "datetime"),
    (Date, "date"),
    (Time, "time"),
    (Boolean, "bool"),
    (JSON, "json"),
    (Uuid, "uuid"),
    (ARRAY, "array"),
    (LargeBinary, "binary"),
]


def _classify_type(sa_type: Any) -> str:
    for cls, label in _TYPE_MAP:
        if isinstance(sa_type, cls):
            return label
    if isinstance(sa_type, TypeDecorator):
        return _classify_type(sa_type.impl)
    return "other"


def _column_kind(col_info: Any, is_pk: bool, is_fk: bool) -> str:
    if is_pk:
        return "pk"
    if is_fk:
        return "fk"
    return _classify_type(col_info.type)


def _resolve_metadata(
    base_or_metadata: type[DeclarativeBase] | MetaData,
) -> tuple[MetaData, dict[str, str], dict[str, type]]:
    """Return metadata and mapper-derived lookups when available."""
    if isinstance(base_or_metadata, MetaData):
        return base_or_metadata, {}, {}

    metadata = base_or_metadata.metadata
    mappers = list(base_or_metadata.registry.mappers)
    class_names = {
        mapper.local_table.fullname: mapper.class_.__name__
        for mapper in mappers
    }
    mapped_classes = {
        mapper.local_table.fullname: mapper.class_
        for mapper in mappers
    }
    return metadata, class_names, mapped_classes


def _table_kind(table_key: str, table: Any, mapped_classes: dict[str, type]) -> str:
    cls = mapped_classes.get(table_key)
    info_kind = table.info.get("erd_kind") or table.info.get("kind")
    if info_kind in {"view", "materialized_view"}:
        return info_kind
    if (
        table.info.get("materialized_view")
        or table.info.get("is_materialized_view")
        or table.info.get("__materialized_view__")
        or (cls is not None and getattr(cls, "__materialized_view__", False))
    ):
        return "materialized_view"
    if (
        table.info.get("view")
        or table.info.get("is_view")
        or table.info.get("__view__")
        or (cls is not None and getattr(cls, "__view__", False))
    ):
        return "view"
    return "table"


def _build_table(
    table_key: str,
    table: Any,
    class_names: dict[str, str],
    mapped_classes: dict[str, type],
    multi_schema: bool,
    exclude_columns: list[re.Pattern[str]] | None = None,
) -> TableInfo:
    pk_cols = {c.name for c in table.primary_key.columns}
    fk_cols = {col.name for col in table.columns if col.foreign_keys}

    columns: list[ColumnInfo] = []
    for col in table.columns:
        if _matches_any(col.name, exclude_columns):
            continue
        is_pk = col.name in pk_cols
        is_fk = col.name in fk_cols
        columns.append(ColumnInfo(
            name=col.name,
            kind=_column_kind(col, is_pk, is_fk),
            nullable=col.nullable or False,
            is_pk=is_pk,
            is_fk=is_fk,
        ))

    display_name = class_names.get(table_key, table.name)
    if multi_schema:
        schema_label = table.schema or "default"
        display_name = f"{schema_label}.{display_name}"

    return TableInfo(
        name=table_key,
        class_name=display_name,
        schema=table.schema,
        columns=columns,
        kind=_table_kind(table_key, table, mapped_classes),
    )


def _build_relationships(
    filtered_items: list[tuple[str, Any]],
) -> list[RelationshipInfo]:
    """Derive one ``1:N`` relationship per distinct foreign key column."""
    relationships: list[RelationshipInfo] = []
    seen_fks: set[tuple[str, str, str]] = set()

    for table_key, table in filtered_items:
        for col in table.columns:
            for fk in col.foreign_keys:
                ref_table = fk.column.table.fullname
                pair = (table_key, ref_table, col.name)
                if pair in seen_fks:
                    continue
                seen_fks.add(pair)
                relationships.append(RelationshipInfo(
                    from_table=ref_table,
                    to_table=table_key,
                    from_card="1",
                    to_card="N",
                    fk_column=col.name,
                ))

    return relationships


def _collapse_association_tables(
    filtered_items: list[tuple[str, Any]],
    tables: list[TableInfo],
    relationships: list[RelationshipInfo],
) -> tuple[list[TableInfo], list[RelationshipInfo]]:
    """Replace pure ``M:N`` join tables with a single ``N:N`` edge between parents.

    A join table is one whose primary key is composed entirely of foreign keys
    pointing at exactly two distinct parent tables.
    """
    association_tables: set[str] = set()

    for table_key, table in filtered_items:
        pk_col_names = {c.name for c in table.primary_key.columns}
        if len(pk_col_names) < 2:
            continue
        pk_fk_cols = [
            c for c in table.columns
            if c.name in pk_col_names and c.foreign_keys
        ]
        if len(pk_fk_cols) != len(pk_col_names):
            continue
        fk_targets = [
            fk.column.table.fullname
            for c in pk_fk_cols
            for fk in c.foreign_keys
        ]
        if len(fk_targets) == 2 and fk_targets[0] != fk_targets[1]:
            association_tables.add(table_key)
            a, b = fk_targets
            relationships = [r for r in relationships if r.to_table != table_key]
            relationships.append(RelationshipInfo(
                from_table=a,
                to_table=b,
                from_card="N",
                to_card="N",
                fk_column=f"via {table.name}",
            ))

    tables = [t for t in tables if t.name not in association_tables]
    return tables, relationships


def introspect_models(
    base_or_metadata: type[DeclarativeBase] | MetaData,
    schemas: list[str] | None = None,
    filters: Filters | None = None,
    include_views: bool = True,
) -> tuple[list[TableInfo], list[RelationshipInfo]]:
    metadata, class_names, mapped_classes = _resolve_metadata(base_or_metadata)
    filters = filters or Filters()
    include = _compile(filters.include_tables)
    exclude = _compile(filters.exclude_tables)
    exclude_columns = _compile(filters.exclude_columns)

    filtered_items = [
        (key, table)
        for key, table in sorted(metadata.tables.items())
        if (schemas is None or table.schema in schemas)
        and _is_table_kept(table.name, include, exclude)
        and (include_views or _table_kind(key, table, mapped_classes) == "table")
    ]
    multi_schema = len({table.schema for _, table in filtered_items}) > 1

    tables = [
        _build_table(
            table_key, table, class_names, mapped_classes, multi_schema, exclude_columns,
        )
        for table_key, table in filtered_items
    ]
    relationships = _build_relationships(filtered_items)

    tables, relationships = _collapse_association_tables(
        filtered_items, tables, relationships,
    )
    kept_names = {t.name for t in tables}
    relationships = [
        rel for rel in relationships
        if rel.from_table in kept_names and rel.to_table in kept_names
    ]
    return tables, relationships
