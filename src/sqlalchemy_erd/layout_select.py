"""Single source of truth for choosing a layout algorithm by name.

Both the public ``generate_erd`` API and the CLI dispatch through here so the
name → algorithm mapping lives in exactly one place. Adding a layout means
registering one entry in ``LAYOUTS`` — no caller needs to change (OCP).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from sqlalchemy_erd.force import force_directed_layout, ForceParams
from sqlalchemy_erd.introspect import RelationshipInfo, TableInfo
from sqlalchemy_erd.layered import layered_layout
from sqlalchemy_erd.layout import NODE_W
from sqlalchemy_erd.star import star_layout

Positions = dict[str, tuple[float, float]]


@dataclass(frozen=True)
class LayoutRequest:
    """Everything a layout algorithm may need; each uses only what applies."""

    tables: list[TableInfo]
    relationships: list[RelationshipInfo]
    node_w: int = NODE_W
    star_cols: int | None = None
    force: ForceParams | None = None


def _layered(request: LayoutRequest) -> Positions:
    return layered_layout(request.tables, request.relationships, node_w=request.node_w)


def _star(request: LayoutRequest) -> Positions:
    return star_layout(
        request.tables, request.relationships,
        star_cols=request.star_cols, node_w=request.node_w,
    )


def _force(request: LayoutRequest) -> Positions:
    return force_directed_layout(
        request.tables, request.relationships,
        force=request.force or ForceParams(), node_w=request.node_w,
    )


LAYOUTS: dict[str, Callable[[LayoutRequest], Positions]] = {
    "layered": _layered,
    "star": _star,
    "force": _force,
}


def select_layout(layout: str, request: LayoutRequest) -> Positions:
    """Run the layout registered under ``layout``; raise ``ValueError`` if unknown."""
    try:
        strategy = LAYOUTS[layout]
    except KeyError:
        raise ValueError(
            f"Unknown layout '{layout}'. Use: {', '.join(LAYOUTS)}"
        ) from None
    return strategy(request)
