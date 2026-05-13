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
    "json": "#92400e",
    "bool": "#047857",
    "uuid": "#7c3aed",
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
    "json": "json",
    "bool": "bool",
    "uuid": "uuid",
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
}


def get_theme(name_or_theme: str | Theme, table_colors: dict[str, str] | None = None) -> Theme:
    if isinstance(name_or_theme, Theme):
        theme = deepcopy(name_or_theme)
    else:
        if name_or_theme not in THEMES:
            raise ValueError(f"Unknown theme '{name_or_theme}'. Available: {list(THEMES.keys())}")
        theme = deepcopy(THEMES[name_or_theme])
    if table_colors:
        theme.table_colors.update(table_colors)
    return theme
