"""Backward-compatible ``to_<format>`` helpers; thin adapters over the renderers."""

from __future__ import annotations

from sqlalchemy_erd.introspect import RelationshipInfo, TableInfo
from sqlalchemy_erd.layout import NODE_W
from sqlalchemy_erd.render import (
    HtmlRenderer, PdfRenderer, PngRenderer, Positions, RenderRequest, SvgRenderer,
)
from sqlalchemy_erd.theme import Theme


def to_svg(
    tables: list[TableInfo],
    relationships: list[RelationshipInfo],
    positions: Positions,
    theme: Theme,
    node_w: int = NODE_W,
) -> str:
    return SvgRenderer().render(
        RenderRequest(tables, relationships, positions, theme, node_w=node_w),
    )


def to_html(
    tables: list[TableInfo],
    relationships: list[RelationshipInfo],
    positions: Positions,
    theme: Theme,
    title: str = "ERD",
    node_w: int = NODE_W,
) -> str:
    return HtmlRenderer().render(
        RenderRequest(tables, relationships, positions, theme, node_w=node_w, title=title),
    )


def to_png(
    tables: list[TableInfo],
    relationships: list[RelationshipInfo],
    positions: Positions,
    theme: Theme,
    scale: int = 2,
    node_w: int = NODE_W,
) -> bytes:
    return PngRenderer().render(
        RenderRequest(tables, relationships, positions, theme, node_w=node_w, scale=scale),
    )


def to_pdf(
    tables: list[TableInfo],
    relationships: list[RelationshipInfo],
    positions: Positions,
    theme: Theme,
    node_w: int = NODE_W,
) -> bytes:
    return PdfRenderer().render(
        RenderRequest(tables, relationships, positions, theme, node_w=node_w),
    )
