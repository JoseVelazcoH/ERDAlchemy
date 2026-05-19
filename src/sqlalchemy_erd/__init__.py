"""sqlalchemy-erd: Interactive ERD visualization for SQLAlchemy 2.0 models."""

from __future__ import annotations

from pathlib import Path
from typing import Union

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

from sqlalchemy_erd.introspect import introspect_models
from sqlalchemy_erd.layout import force_directed_layout, star_layout
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
    layout: str = "force",
    *,
    k_repulse: float = 35000.0,
    k_attract: float = 0.1,
    k_align: float = 0.02,
    ideal_len: float = 280.0,
) -> Union[str, bytes]:
    tables, relationships = introspect_models(base_or_metadata, schemas=schemas)
    resolved_theme = get_theme(theme, table_colors)
    apply_schema_colors(resolved_theme, tables)

    if layout == "star":
        positions = star_layout(tables, relationships)
    elif layout == "force":
        positions = force_directed_layout(
            tables, relationships,
            k_repulse=k_repulse, k_attract=k_attract,
            k_align=k_align, ideal_len=ideal_len,
        )
    else:
        raise ValueError(f"Unknown layout '{layout}'. Use: force, star")

    if format == "html":
        content = to_html(tables, relationships, positions, resolved_theme, title=title)
        Path(output).write_text(content, encoding="utf-8")
        return content
    elif format == "svg":
        content = to_svg(tables, relationships, positions, resolved_theme)
        Path(output).write_text(content, encoding="utf-8")
        return content
    elif format == "png":
        data = to_png(tables, relationships, positions, resolved_theme, scale=scale)
        Path(output).write_bytes(data)
        return data
    elif format == "pdf":
        data = to_pdf(tables, relationships, positions, resolved_theme)
        Path(output).write_bytes(data)
        return data
    else:
        raise ValueError(f"Unknown format '{format}'. Use: html, svg, png, pdf")
