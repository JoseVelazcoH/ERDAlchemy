"""Card sizing helpers shared by every layout algorithm.

Geometry constants live in ``constants``; the layout algorithms live in their
own modules (``force``, ``star``, ``layered``).
"""

from sqlalchemy_erd.constants.geometry import (
    FIELD_CHAR_W, FIELD_H, FIELD_LABEL_GAP, FIELD_PADDING_LEFT,
    FIELD_PADDING_RIGHT, HEADER_CHAR_W, HEADER_H, HEADER_PADDING, NODE_W, PAD,
)
from sqlalchemy_erd.introspect import TableInfo
from sqlalchemy_erd.theme import DEFAULT_KIND_LABELS


def node_h(table: TableInfo) -> int:
    return HEADER_H + PAD + len(table.columns) * FIELD_H + PAD


def auto_node_width(tables: list[TableInfo]) -> int:
    max_w = NODE_W
    for t in tables:
        header_w = HEADER_PADDING + len(t.class_name) * HEADER_CHAR_W
        max_w = max(max_w, int(header_w))
        for col in t.columns:
            kind_label = DEFAULT_KIND_LABELS.get(col.kind, col.kind)
            if not col.is_pk and not col.is_fk and col.nullable:
                kind_label += "?"
            if col.is_unique:
                kind_label += " U"
            elif col.is_indexed:
                kind_label += " IDX"
            col_w = (
                FIELD_PADDING_LEFT
                + len(col.name) * FIELD_CHAR_W
                + FIELD_LABEL_GAP
                + len(kind_label) * FIELD_CHAR_W
                + FIELD_PADDING_RIGHT
            )
            max_w = max(max_w, int(col_w))
    return max_w
