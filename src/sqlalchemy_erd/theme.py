from __future__ import annotations

from dataclasses import dataclass, field
from copy import deepcopy


DEFAULT_KIND_COLORS: dict[str, str] = {
    "pk": "#5C2472",
    "fk": "#c2410c",
    "int": "#6b7280",
    "bigint": "#6b7280",
    "smallint": "#6b7280",
    "float": "#6b7280",
    "numeric": "#6b7280",
    "string": "#6b7280",
    "text": "#9ca3af",
    "date": "#1d4ed8",
    "datetime": "#1d4ed8",
    "time": "#1d4ed8",
    "json": "#92400e",
    "bool": "#047857",
    "uuid": "#7c3aed",
    "enum": "#0e7490",
    "array": "#b45309",
    "interval": "#1d4ed8",
    "binary": "#6b7280",
    "other": "#9ca3af",
}

DEFAULT_KIND_LABELS: dict[str, str] = {
    "pk": "PK",
    "fk": "FK",
    "int": "int",
    "bigint": "bigint",
    "smallint": "smallint",
    "float": "float",
    "numeric": "numeric",
    "string": "string",
    "text": "text",
    "date": "date",
    "datetime": "datetime",
    "time": "time",
    "json": "json",
    "bool": "bool",
    "uuid": "uuid",
    "enum": "enum",
    "array": "array",
    "interval": "interval",
    "binary": "binary",
    "other": "other",
}


@dataclass
class Theme:
    name: str = "default"
    header_color: str = "#5C2472"
    header_hover_color: str = "#4a1d5e"
    bg_color: str = "#f9fafb"
    card_bg: str = "#ffffff"
    card_border: str = "#dde1e8"
    edge_color: str = "#c4cad4"
    highlight_color: str = "#FF8300"
    dot_color: str = "#d1d5db"
    field_text_color: str = "#3d4552"
    separator_color: str = "#f0f2f5"
    kind_colors: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_KIND_COLORS))
    kind_labels: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_KIND_LABELS))
    table_colors: dict[str, str] = field(default_factory=dict)
    schema_colors: dict[str | None, str] = field(default_factory=dict)

    def get_header_color(self, table_name: str) -> str:
        return self.table_colors.get(table_name, self.header_color)


THEMES: dict[str, Theme] = {
    "default": Theme(),
    "blue": Theme(
        name="blue",
        header_color="#1e40af",
        header_hover_color="#1e3a8a",
        highlight_color="#f59e0b",
    ),
    "green": Theme(
        name="green",
        header_color="#065f46",
        header_hover_color="#064e3b",
        highlight_color="#dc2626",
    ),
    "dark": Theme(
        name="dark",
        header_color="#374151",
        header_hover_color="#1f2937",
        bg_color="#111827",
        card_bg="#1f2937",
        card_border="#374151",
        edge_color="#4b5563",
        dot_color="#374151",
        field_text_color="#d1d5db",
        separator_color="#374151",
        highlight_color="#f59e0b",
    ),
    "rose": Theme(
        name="rose",
        header_color="#9f1239",
        header_hover_color="#881337",
        highlight_color="#2563eb",
    ),
    "yellow": Theme(
        name="yellow",
        header_color="#ca8a04",
        header_hover_color="#a16207",
        highlight_color="#7c3aed",
    ),
    "pink": Theme(
        name="pink",
        header_color="#db2777",
        header_hover_color="#be185d",
        highlight_color="#2563eb",
    ),
    "navy": Theme(
        name="navy",
        header_color="#1e3a8a",
        header_hover_color="#172554",
        highlight_color="#f59e0b",
    ),
}


SCHEMA_PALETTE = [
    "#6366f1",
    "#059669",
    "#d97706",
    "#dc2626",
    "#7c3aed",
    "#0891b2",
    "#be185d",
    "#65a30d",
]


def apply_schema_colors(theme: Theme, tables: list) -> None:
    schemas_present = sorted(
        {t.schema for t in tables},
        key=lambda x: (x is None, x or ""),
    )
    if len(schemas_present) <= 1:
        return
    for i, schema in enumerate(schemas_present):
        color = SCHEMA_PALETTE[i % len(SCHEMA_PALETTE)]
        theme.schema_colors[schema] = color
    for t in tables:
        if t.name not in theme.table_colors:
            theme.table_colors[t.name] = theme.schema_colors[t.schema]


def _darken_hex(hex_color: str, factor: float = 0.8) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r, g, b = int(r * factor), int(g * factor), int(b * factor)
    return f"#{r:02x}{g:02x}{b:02x}"


def _is_hex_color(value: str) -> bool:
    if not value.startswith("#") or len(value) != 7:
        return False
    try:
        int(value[1:], 16)
        return True
    except ValueError:
        return False


def get_theme(name_or_theme: str | Theme, table_colors: dict[str, str] | None = None) -> Theme:
    if isinstance(name_or_theme, Theme):
        theme = deepcopy(name_or_theme)
    elif _is_hex_color(name_or_theme):
        theme = Theme(
            name="custom",
            header_color=name_or_theme,
            header_hover_color=_darken_hex(name_or_theme),
        )
    else:
        if name_or_theme not in THEMES:
            raise ValueError(f"Unknown theme '{name_or_theme}'. Available: {list(THEMES.keys())}")
        theme = deepcopy(THEMES[name_or_theme])
    if table_colors:
        theme.table_colors.update(table_colors)
    return theme
