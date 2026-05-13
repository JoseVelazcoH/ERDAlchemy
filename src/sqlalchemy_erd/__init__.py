"""sqlalchemy-erd: Interactive ERD visualization for SQLAlchemy 2.0 models."""

from __future__ import annotations

from pathlib import Path
from typing import Union

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

from sqlalchemy_erd.introspect import introspect_models
from sqlalchemy_erd.layout import force_directed_layout
from sqlalchemy_erd.theme import Theme, THEMES, get_theme
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
) -> Union[str, bytes]:
    tables, relationships = introspect_models(base_or_metadata)
    resolved_theme = get_theme(theme, table_colors)
    positions = force_directed_layout(tables, relationships)

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
