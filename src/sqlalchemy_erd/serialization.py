"""Serialize tables and relationships to the JSON payloads the interactive HTML embeds."""

import json

from sqlalchemy_erd.introspect import RelationshipInfo, TableInfo
from sqlalchemy_erd.theme import Theme

_FK_NAME_COLOR = "#9a3412"
_FALLBACK_PK_COLOR = "#5C2472"
_FALLBACK_KIND_COLOR = "#9ca3af"


def build_entities_json(tables: list[TableInfo], theme: Theme) -> str:
    """JSON array of entity objects (id, label, colors, fields) for the client."""
    entities = []
    for t in tables:
        fields = []
        for col in t.columns:
            name_color = (
                theme.kind_colors.get("pk", _FALLBACK_PK_COLOR) if col.is_pk
                else _FK_NAME_COLOR if col.is_fk
                else theme.field_text_color
            )
            name_weight = "700" if col.is_pk else "400"
            kind_color = theme.kind_colors.get(col.kind, _FALLBACK_KIND_COLOR)
            kind_label = theme.kind_labels.get(col.kind, col.kind)
            if not col.is_pk and not col.is_fk and col.nullable:
                kind_label += "?"

            fields.append({
                "name": col.name,
                "nameColor": name_color,
                "nameWeight": name_weight,
                "kindColor": kind_color,
                "kindLabel": kind_label,
            })

        entities.append({
            "id": t.name,
            "label": t.class_name,
            "schema": t.schema,
            "headerColor": theme.get_header_color(t.name),
            "hoverColor": theme.header_hover_color,
            "fields": fields,
        })
    return json.dumps(entities)


def build_relations_json(
    relationships: list[RelationshipInfo],
    tables: list[TableInfo],
    positions: dict[str, tuple[float, float]],
) -> str:
    """JSON array of relation objects, filtered to edges between known tables."""
    table_names = {t.name for t in tables}
    rels = [
        {
            "from": r.from_table,
            "to": r.to_table,
            "fromCard": r.from_card,
            "toCard": r.to_card,
            "fkCol": r.fk_column,
        }
        for r in relationships
        if r.from_table in table_names and r.to_table in table_names
    ]
    return json.dumps(rels)
