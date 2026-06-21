"""Shared layout primitives: card geometry constants and sizing helpers.

The layout algorithms live in their own modules (``force``, ``star``,
``layered``) and import the constants and ``node_h`` / ``auto_node_width``
helpers from here.
"""

from __future__ import annotations

from sqlalchemy_erd.introspect import TableInfo
from sqlalchemy_erd.theme import DEFAULT_KIND_LABELS

NODE_W = 218
HEADER_H = 36
FIELD_H = 21
PAD = 6

GAP_X = 60
GAP_Y = 40
MARGIN = 60.0

# Approximate glyph widths (px) used to size a card to its widest text.
# These track the font sizes/families in renderer.py and html_renderer.py.
FIELD_CHAR_W = 6.2       # monospace field-name / kind-label font
HEADER_CHAR_W = 7.8      # bold header-title font
HEADER_PADDING = 24      # left + right padding around the header label
FIELD_PADDING_LEFT = 10  # left inset of the field name
FIELD_LABEL_GAP = 12     # gap between field name and kind label
FIELD_PADDING_RIGHT = 8  # right inset of the kind label


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
            col_w = (
                FIELD_PADDING_LEFT
                + len(col.name) * FIELD_CHAR_W
                + FIELD_LABEL_GAP
                + len(kind_label) * FIELD_CHAR_W
                + FIELD_PADDING_RIGHT
            )
            max_w = max(max_w, int(col_w))
    return max_w
