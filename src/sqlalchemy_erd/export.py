from __future__ import annotations

from pathlib import Path

from sqlalchemy_erd.introspect import TableInfo, RelationshipInfo
from sqlalchemy_erd.layout import force_directed_layout
from sqlalchemy_erd.renderer import render_svg
from sqlalchemy_erd.html_renderer import render_html
from sqlalchemy_erd.theme import Theme


def to_svg(
    tables: list[TableInfo],
    relationships: list[RelationshipInfo],
    positions: dict[str, tuple[float, float]],
    theme: Theme,
) -> str:
    return render_svg(tables, relationships, positions, theme, include_xml_header=True)


def to_html(
    tables: list[TableInfo],
    relationships: list[RelationshipInfo],
    positions: dict[str, tuple[float, float]],
    theme: Theme,
    title: str = "ERD",
) -> str:
    return render_html(tables, relationships, positions, theme, title=title)


def to_png(
    tables: list[TableInfo],
    relationships: list[RelationshipInfo],
    positions: dict[str, tuple[float, float]],
    theme: Theme,
    scale: int = 2,
) -> bytes:
    try:
        import cairosvg
    except ImportError:
        raise ImportError(
            "PNG export requires 'cairosvg'. Install it with: "
            "pip install sqlalchemy-erd[png]"
        )
    svg_str = render_svg(tables, relationships, positions, theme, include_xml_header=True)
    return cairosvg.svg2png(bytestring=svg_str.encode("utf-8"), scale=scale)


def to_pdf(
    tables: list[TableInfo],
    relationships: list[RelationshipInfo],
    positions: dict[str, tuple[float, float]],
    theme: Theme,
) -> bytes:
    try:
        import cairosvg
    except ImportError:
        raise ImportError(
            "PDF export requires 'cairosvg'. Install it with: "
            "pip install sqlalchemy-erd[pdf]"
        )
    svg_str = render_svg(tables, relationships, positions, theme, include_xml_header=True)
    return cairosvg.svg2pdf(bytestring=svg_str.encode("utf-8"))
