from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import inspect, MetaData
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import (
    Boolean, Date, DateTime, Float, Integer, BigInteger, SmallInteger,
    JSON, Numeric, String, Text, Uuid,
)


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


@dataclass
class RelationshipInfo:
    from_table: str
    to_table: str
    from_card: str
    to_card: str
    fk_column: str


_TYPE_MAP: list[tuple[type, str]] = [
    (BigInteger, "bigint"),
    (SmallInteger, "smallint"),
    (Integer, "int"),
    (Text, "text"),
    (String, "string"),
    (Float, "float"),
    (Numeric, "numeric"),
    (DateTime, "datetime"),
    (Date, "date"),
    (Boolean, "bool"),
    (JSON, "json"),
    (Uuid, "uuid"),
]


def _classify_type(sa_type: Any) -> str:
    for cls, label in _TYPE_MAP:
        if isinstance(sa_type, cls):
            return label
    return "other"


def _column_kind(col_info: Any, is_pk: bool, is_fk: bool) -> str:
    if is_pk:
        return "pk"
    if is_fk:
        return "fk"
    return _classify_type(col_info.type)


def introspect_models(
    base_or_metadata: type[DeclarativeBase] | MetaData,
    schemas: list[str] | None = None,
) -> tuple[list[TableInfo], list[RelationshipInfo]]:
    if isinstance(base_or_metadata, MetaData):
        metadata = base_or_metadata
        class_names: dict[str, str] = {}
    else:
        metadata = base_or_metadata.metadata
        class_names = {}
        for mapper in base_or_metadata.registry.mappers:
            class_names[mapper.local_table.fullname] = mapper.class_.__name__

    filtered_items = [
        (key, table)
        for key, table in sorted(metadata.tables.items())
        if schemas is None or table.schema in schemas
    ]
    present_schemas = {table.schema for _, table in filtered_items}
    multi_schema = len(present_schemas) > 1

    tables: list[TableInfo] = []
    relationships: list[RelationshipInfo] = []
    seen_fks: set[tuple[str, str]] = set()

    for table_key, table in filtered_items:
        pk_cols = {c.name for c in table.primary_key.columns}
        fk_cols = {
            col.name
            for col in table.columns
            if col.foreign_keys
        }

        columns: list[ColumnInfo] = []
        for col in table.columns:
            is_pk = col.name in pk_cols
            is_fk = col.name in fk_cols
            kind = _column_kind(col, is_pk, is_fk)
            columns.append(ColumnInfo(
                name=col.name,
                kind=kind,
                nullable=col.nullable or False,
                is_pk=is_pk,
                is_fk=is_fk,
            ))

        display_name = class_names.get(table_key, table.name)
        if multi_schema:
            schema_label = table.schema or "default"
            display_name = f"{schema_label}.{display_name}"

        tables.append(TableInfo(
            name=table_key,
            class_name=display_name,
            schema=table.schema,
            columns=columns,
        ))

        for col in table.columns:
            for fk in col.foreign_keys:
                ref_table = fk.column.table.fullname
                pair = (table_key, ref_table)
                if pair not in seen_fks:
                    seen_fks.add(pair)
                    relationships.append(RelationshipInfo(
                        from_table=ref_table,
                        to_table=table_key,
                        from_card="1",
                        to_card="N",
                        fk_column=col.name,
                    ))

    association_tables = set()
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
        fk_targets = []
        for c in pk_fk_cols:
            for fk in c.foreign_keys:
                fk_targets.append(fk.column.table.fullname)
        if len(fk_targets) == 2 and fk_targets[0] != fk_targets[1]:
            association_tables.add(table_key)
            a, b = fk_targets
            relationships = [
                r for r in relationships
                if not (r.to_table == table_key)
            ]
            relationships.append(RelationshipInfo(
                from_table=a,
                to_table=b,
                from_card="N",
                to_card="N",
                fk_column=f"via {table.name}",
            ))

    tables = [t for t in tables if t.name not in association_tables]

    return tables, relationships
