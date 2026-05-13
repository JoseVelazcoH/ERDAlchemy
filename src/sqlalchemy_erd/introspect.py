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
) -> tuple[list[TableInfo], list[RelationshipInfo]]:
    if isinstance(base_or_metadata, MetaData):
        metadata = base_or_metadata
        class_names: dict[str, str] = {}
    else:
        metadata = base_or_metadata.metadata
        class_names = {}
        for mapper in base_or_metadata.registry.mappers:
            tname = mapper.local_table.name
            class_names[tname] = mapper.class_.__name__

    tables: list[TableInfo] = []
    relationships: list[RelationshipInfo] = []
    seen_fks: set[tuple[str, str]] = set()

    for table_name, table in sorted(metadata.tables.items()):
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

        display_name = class_names.get(table_name, table_name)
        tables.append(TableInfo(
            name=table_name,
            class_name=display_name,
            columns=columns,
        ))

        for col in table.columns:
            for fk in col.foreign_keys:
                ref_table = fk.column.table.name
                pair = (table_name, ref_table)
                if pair not in seen_fks:
                    seen_fks.add(pair)
                    relationships.append(RelationshipInfo(
                        from_table=ref_table,
                        to_table=table_name,
                        from_card="1",
                        to_card="N",
                        fk_column=col.name,
                    ))

    association_tables = set()
    for table_name, table in metadata.tables.items():
        cols = list(table.columns)
        fk_count = sum(1 for c in cols if c.foreign_keys)
        if fk_count >= 2 and len(cols) <= fk_count + 1:
            fk_targets = []
            for c in cols:
                for fk in c.foreign_keys:
                    fk_targets.append(fk.column.table.name)
            if len(fk_targets) == 2:
                association_tables.add(table_name)
                a, b = fk_targets
                pair_key = tuple(sorted([a, b]))
                relationships = [
                    r for r in relationships
                    if not (r.to_table == table_name)
                ]
                relationships.append(RelationshipInfo(
                    from_table=a,
                    to_table=b,
                    from_card="N",
                    to_card="N",
                    fk_column=f"via {table_name}",
                ))

    tables = [t for t in tables if t.name not in association_tables]

    return tables, relationships
