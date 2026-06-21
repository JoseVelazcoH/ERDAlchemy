"""sqlalchemy-erd: Interactive ERD visualization for SQLAlchemy 2.0 models."""

from __future__ import annotations

from pathlib import Path
from typing import Union

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

from sqlalchemy_erd.introspect import Filters, introspect_models
from sqlalchemy_erd.layout import auto_node_width, ForceParams, NODE_W
from sqlalchemy_erd.layout_select import LayoutRequest, select_layout
from sqlalchemy_erd.theme import Theme, THEMES, get_theme, apply_schema_colors
from sqlalchemy_erd.export import to_html, to_svg, to_png, to_pdf

__version__ = "0.1.1"


def generate_erd(
    base_or_metadata: Union[type[DeclarativeBase], MetaData],
    output: str = "erd.html",
    format: str = "html",
    theme: Union[str, Theme] = "default",
    table_colors: dict[str, str] | None = None,
    title: str = "ERD",
    scale: int = 2,
    schemas: list[str] | None = None,
    layout: str = "layered",
    star_cols: int | None = None,
    node_width: Union[int, str, None] = None,
    *,
    force: ForceParams | None = None,
    filters: Filters | None = None,
) -> Union[str, bytes]:
    tables, relationships = introspect_models(
        base_or_metadata, schemas=schemas, filters=filters,
    )
    resolved_theme = get_theme(theme, table_colors)
    apply_schema_colors(resolved_theme, tables)

    if node_width == "auto":
        node_w = auto_node_width(tables)
    elif isinstance(node_width, int):
        node_w = node_width
    else:
        node_w = NODE_W

    positions = select_layout(layout, LayoutRequest(
        tables=tables,
        relationships=relationships,
        node_w=node_w,
        star_cols=star_cols,
        force=force,
    ))

    if format == "html":
        content = to_html(tables, relationships, positions, resolved_theme, title=title, node_w=node_w)
        Path(output).write_text(content, encoding="utf-8")
        return content
    elif format == "svg":
        content = to_svg(tables, relationships, positions, resolved_theme, node_w=node_w)
        Path(output).write_text(content, encoding="utf-8")
        return content
    elif format == "png":
        data = to_png(tables, relationships, positions, resolved_theme, scale=scale, node_w=node_w)
        Path(output).write_bytes(data)
        return data
    elif format == "pdf":
        data = to_pdf(tables, relationships, positions, resolved_theme, node_w=node_w)
        Path(output).write_bytes(data)
        return data
    else:
        raise ValueError(f"Unknown format '{format}'. Use: html, svg, png, pdf")
