"""Output-format renderers behind one contract.

Each format implements the ``Renderer`` protocol: it turns a ``RenderRequest``
into ``str`` (text formats) or ``bytes`` (binary formats). Adding a format means
registering one class in ``RENDERERS`` — the introspection and layout layers stay
format-agnostic. The per-element rendering API some formats need (SVG draws each
table in Python; HTML emits a client-side template) does not generalize, so the
shared contract is at the diagram level, not per element.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from sqlalchemy_erd.html_renderer import render_html
from sqlalchemy_erd.introspect import RelationshipInfo, TableInfo
from sqlalchemy_erd.layout import NODE_W
from sqlalchemy_erd.renderer import render_svg
from sqlalchemy_erd.theme import Theme

Positions = dict[str, tuple[float, float]]


@dataclass(frozen=True)
class RenderRequest:
    """Everything a renderer may need; each format uses only what applies."""

    tables: list[TableInfo]
    relationships: list[RelationshipInfo]
    positions: Positions
    theme: Theme
    node_w: int = NODE_W
    title: str = "ERD"
    scale: int = 2


def _svg_string(request: RenderRequest) -> str:
    return render_svg(
        request.tables, request.relationships, request.positions, request.theme,
        include_xml_header=True, node_w=request.node_w,
    )


def _require_cairosvg(fmt: str):
    try:
        import cairosvg
    except ImportError:
        raise ImportError(
            f"{fmt.upper()} export requires 'cairosvg'. Install it with: "
            f"pip install sqlalchemy-erd[{fmt}]"
        ) from None
    return cairosvg


class Renderer(Protocol):
    def render(self, request: RenderRequest) -> str | bytes: ...


class SvgRenderer:
    def render(self, request: RenderRequest) -> str:
        return _svg_string(request)


class HtmlRenderer:
    def render(self, request: RenderRequest) -> str:
        return render_html(
            request.tables, request.relationships, request.positions, request.theme,
            title=request.title, node_w=request.node_w,
        )


class PngRenderer:
    def render(self, request: RenderRequest) -> bytes:
        cairosvg = _require_cairosvg("png")
        return cairosvg.svg2png(
            bytestring=_svg_string(request).encode("utf-8"), scale=request.scale,
        )


class PdfRenderer:
    def render(self, request: RenderRequest) -> bytes:
        cairosvg = _require_cairosvg("pdf")
        return cairosvg.svg2pdf(bytestring=_svg_string(request).encode("utf-8"))


RENDERERS: dict[str, Renderer] = {
    "svg": SvgRenderer(),
    "html": HtmlRenderer(),
    "png": PngRenderer(),
    "pdf": PdfRenderer(),
}


def render(fmt: str, request: RenderRequest) -> str | bytes:
    """Render ``request`` in ``fmt``; raise ``ValueError`` if the format is unknown."""
    try:
        renderer = RENDERERS[fmt]
    except KeyError:
        raise ValueError(
            f"Unknown format '{fmt}'. Use: {', '.join(RENDERERS)}"
        ) from None
    return renderer.render(request)


def write_output(path: str | Path, result: str | bytes) -> None:
    """Write a render result to disk, choosing binary vs text by its type."""
    target = Path(path)
    if isinstance(result, bytes):
        target.write_bytes(result)
    else:
        target.write_text(result, encoding="utf-8")
