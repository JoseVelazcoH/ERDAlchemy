from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

from sqlalchemy_erd.introspect import introspect_models
from sqlalchemy_erd.layout import force_directed_layout, star_layout
from sqlalchemy_erd.theme import get_theme, apply_schema_colors, THEMES
from sqlalchemy_erd.export import to_svg, to_html, to_png, to_pdf


def _resolve_target(spec: str) -> type[DeclarativeBase] | MetaData:
    if ":" in spec:
        module_path, attr_name = spec.rsplit(":", 1)
    else:
        module_path = spec
        attr_name = None

    sys.path.insert(0, str(Path.cwd()))
    module = importlib.import_module(module_path)

    if attr_name:
        obj = getattr(module, attr_name)
    else:
        obj = None
        for name in dir(module):
            val = getattr(module, name)
            if isinstance(val, type) and issubclass(val, DeclarativeBase) and val is not DeclarativeBase:
                obj = val
                break
        if obj is None:
            for name in dir(module):
                val = getattr(module, name)
                if isinstance(val, MetaData):
                    obj = val
                    break
        if obj is None:
            print(f"Error: no DeclarativeBase subclass or MetaData found in '{module_path}'", file=sys.stderr)
            sys.exit(1)

    return obj


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="sqlalchemy-erd",
        description="Generate ERD diagrams from SQLAlchemy 2.0 models",
    )
    parser.add_argument(
        "target",
        help="Python import path to Base class (e.g., myapp.models:Base)",
    )
    parser.add_argument(
        "-f", "--format",
        choices=["html", "svg", "png", "pdf"],
        default="html",
        help="Output format (default: html)",
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file path (default: erd.<format>)",
    )
    parser.add_argument(
        "-t", "--theme",
        default="default",
        help=f"Color theme or hex color (available: {', '.join(THEMES.keys())}, or #hex) (default: default)",
    )
    parser.add_argument(
        "--colors",
        help='Per-table color overrides as JSON: \'{"users": "#1d4ed8"}\'',
    )
    parser.add_argument(
        "--scale",
        type=int,
        default=2,
        help="Scale factor for PNG export (default: 2)",
    )
    parser.add_argument(
        "--title",
        default="ERD",
        help="Title for HTML output (default: ERD)",
    )
    parser.add_argument(
        "--schemas",
        help="Comma-separated list of database schemas to include (e.g., public,billing,audit)",
    )
    parser.add_argument(
        "--layout",
        choices=["force", "star"],
        default="force",
        help="Layout algorithm: force (force-directed) or star (column-based) (default: force)",
    )
    parser.add_argument(
        "--k-repulse", type=float, default=35000.0,
        help="Repulsion strength between all nodes (default: 35000)",
    )
    parser.add_argument(
        "--k-attract", type=float, default=0.1,
        help="Attraction strength between connected nodes (default: 0.1)",
    )
    parser.add_argument(
        "--k-align", type=float, default=0.02,
        help="Horizontal-alignment force for connected nodes (default: 0.02)",
    )
    parser.add_argument(
        "--ideal-len", type=float, default=280.0,
        help="Target edge length in pixels between connected nodes (default: 280)",
    )

    args = parser.parse_args(argv)

    target = _resolve_target(args.target)
    schemas_list = [s.strip() for s in args.schemas.split(",") if s.strip()] if args.schemas else None
    tables, relationships = introspect_models(target, schemas=schemas_list)

    if not tables:
        print("No tables found.", file=sys.stderr)
        sys.exit(1)

    table_colors = json.loads(args.colors) if args.colors else None
    theme = get_theme(args.theme, table_colors)
    apply_schema_colors(theme, tables)
    if args.layout == "star":
        positions = star_layout(tables, relationships)
    else:
        positions = force_directed_layout(
            tables, relationships,
            k_repulse=args.k_repulse, k_attract=args.k_attract,
            k_align=args.k_align, ideal_len=args.ideal_len,
        )

    output_path = args.output or f"erd.{args.format}"

    if args.format == "html":
        content = to_html(tables, relationships, positions, theme, title=args.title)
        Path(output_path).write_text(content, encoding="utf-8")
    elif args.format == "svg":
        content = to_svg(tables, relationships, positions, theme)
        Path(output_path).write_text(content, encoding="utf-8")
    elif args.format == "png":
        data = to_png(tables, relationships, positions, theme, scale=args.scale)
        Path(output_path).write_bytes(data)
    elif args.format == "pdf":
        data = to_pdf(tables, relationships, positions, theme)
        Path(output_path).write_bytes(data)

    print(f"Generated {output_path}")


if __name__ == "__main__":
    main()
