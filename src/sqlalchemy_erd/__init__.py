"""sqlalchemy-erd: Interactive ERD visualization for SQLAlchemy 2.0 models."""

from typing import Union

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

from sqlalchemy_erd.constants.geometry import NODE_W
from sqlalchemy_erd.force import ForceParams
from sqlalchemy_erd.introspect import Filters, introspect_models
from sqlalchemy_erd.layout import auto_node_width
from sqlalchemy_erd.layout_select import LayoutRequest, select_layout
from sqlalchemy_erd.render import RenderRequest, render, write_output
from sqlalchemy_erd.theme import Theme, THEMES, get_theme, apply_schema_colors

__version__ = "0.5.0"  # x-release-please-version


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
    show_indexes: bool = False,
    *,
    force: ForceParams | None = None,
    filters: Filters | None = None,
) -> Union[str, bytes]:
    tables, relationships = introspect_models(
        base_or_metadata, schemas=schemas, filters=filters, show_indexes=show_indexes,
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

    result = render(format, RenderRequest(
        tables=tables,
        relationships=relationships,
        positions=positions,
        theme=resolved_theme,
        node_w=node_w,
        title=title,
        scale=scale,
    ))
    write_output(output, result)
    return result
