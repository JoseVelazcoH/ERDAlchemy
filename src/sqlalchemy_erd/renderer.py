from __future__ import annotations

from xml.sax.saxutils import escape

from sqlalchemy_erd.introspect import TableInfo, RelationshipInfo
from sqlalchemy_erd.layout import NODE_W, HEADER_H, FIELD_H, PAD, node_h
from sqlalchemy_erd.theme import Theme

Side = str


def _best_side(
    from_pos: tuple[float, float],
    from_table: TableInfo,
    to_pos: tuple[float, float],
    to_table: TableInfo,
) -> tuple[Side, Side]:
    fx, fy = from_pos
    tx, ty = to_pos
    fh = node_h(from_table)
    th = node_h(to_table)
    fcx, fcy = fx + NODE_W / 2, fy + fh / 2
    tcx, tcy = tx + NODE_W / 2, ty + th / 2
    dx = tcx - fcx
    dy = tcy - fcy

    if abs(dx) > abs(dy):
        from_side = "right" if dx > 0 else "left"
        to_side = "left" if dx > 0 else "right"
    else:
        from_side = "bottom" if dy > 0 else "top"
        to_side = "top" if dy > 0 else "bottom"

    return from_side, to_side


def _conn_pt(
    pos: tuple[float, float], table: TableInfo, side: Side,
) -> tuple[float, float]:
    x, y = pos
    h = node_h(table)
    if side == "top":
        return x + NODE_W / 2, y
    if side == "bottom":
        return x + NODE_W / 2, y + h
    if side == "left":
        return x, y + h / 2
    return x + NODE_W, y + h / 2


def _side_vec(side: Side, d: float) -> tuple[float, float]:
    if side == "top":
        return 0, -d
    if side == "bottom":
        return 0, d
    if side == "left":
        return -d, 0
    return d, 0


def _make_path(
    fp: tuple[float, float], fs: Side,
    tp: tuple[float, float], ts: Side,
) -> str:
    d = 70
    o1 = _side_vec(fs, d)
    o2 = _side_vec(ts, d)
    c1x, c1y = fp[0] + o1[0], fp[1] + o1[1]
    c2x, c2y = tp[0] + o2[0], tp[1] + o2[1]
    return f"M {fp[0]} {fp[1]} C {c1x} {c1y} {c2x} {c2y} {tp[0]} {tp[1]}"


def _label_pos(pt: tuple[float, float], side: Side) -> tuple[float, float]:
    ax, ay = _side_vec(side, 20)
    if side in ("top", "bottom"):
        px, py = 13, 0
    else:
        px, py = 0, -12
    return pt[0] + ax + px, pt[1] + ay + py


def render_svg(
    tables: list[TableInfo],
    relationships: list[RelationshipInfo],
    positions: dict[str, tuple[float, float]],
    theme: Theme,
    *,
    include_xml_header: bool = False,
) -> str:
    table_map = {t.name: t for t in tables}

    max_x = max((positions[t.name][0] + NODE_W + 60 for t in tables), default=980)
    max_y = max((positions[t.name][1] + node_h(t) + 60 for t in tables), default=600)
    svg_w = max(980, max_x)
    svg_h = max(600, max_y)

    parts: list[str] = []

    if include_xml_header:
        parts.append('<?xml version="1.0" encoding="UTF-8"?>')

    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w}" height="{svg_h}" '
        f'style="font-family: system-ui, -apple-system, sans-serif;">'
    )

    parts.append(f"""  <defs>
    <pattern id="erd-dots" width="24" height="24" patternUnits="userSpaceOnUse">
      <circle cx="1" cy="1" r="0.8" fill="{theme.dot_color}" />
    </pattern>
    <marker id="arr" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="{theme.edge_color}" />
    </marker>
    <marker id="arr-hi" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="{theme.highlight_color}" />
    </marker>
  </defs>""")

    parts.append(f'  <rect width="100%" height="100%" fill="{theme.bg_color}" />')
    parts.append(f'  <rect width="100%" height="100%" fill="url(#erd-dots)" />')

    for rel in relationships:
        if rel.from_table not in table_map or rel.to_table not in table_map:
            continue
        ft = table_map[rel.from_table]
        tt = table_map[rel.to_table]
        fp = positions[rel.from_table]
        tp = positions[rel.to_table]
        fs, ts = _best_side(fp, ft, tp, tt)
        fpt = _conn_pt(fp, ft, fs)
        tpt = _conn_pt(tp, tt, ts)
        path_d = _make_path(fpt, fs, tpt, ts)
        is_nn = rel.from_card == "N" and rel.to_card == "N"
        dash = ' stroke-dasharray="5 3"' if is_nn else ""

        fl = _label_pos(fpt, fs)
        tl = _label_pos(tpt, ts)

        parts.append(f'  <g class="erd-rel" data-from="{rel.from_table}" data-to="{rel.to_table}">')
        parts.append(f'    <path d="{path_d}" fill="none" stroke="transparent" stroke-width="18" />')
        parts.append(
            f'    <path class="erd-edge" d="{path_d}" fill="none" '
            f'stroke="{theme.edge_color}" stroke-width="1.5"{dash} marker-end="url(#arr)" />'
        )
        parts.append(
            f'    <text x="{fl[0]}" y="{fl[1]}" font-size="11" '
            f'font-family="monospace" fill="{theme.edge_color}" '
            f'text-anchor="middle" dominant-baseline="middle">{rel.from_card}</text>'
        )
        parts.append(
            f'    <text x="{tl[0]}" y="{tl[1]}" font-size="11" '
            f'font-family="monospace" fill="{theme.edge_color}" '
            f'text-anchor="middle" dominant-baseline="middle">{rel.to_card}</text>'
        )
        parts.append("  </g>")

    for table in tables:
        pos = positions[table.name]
        x, y = pos
        h = node_h(table)
        header_col = theme.get_header_color(table.name)

        parts.append(
            f'  <g class="erd-node" data-table="{table.name}" '
            f'transform="translate({x}, {y})" style="cursor: grab;">'
        )
        parts.append(f'    <rect x="3" y="3" rx="7" width="{NODE_W}" height="{h}" fill="rgba(0,0,0,0.06)" />')
        parts.append(
            f'    <rect class="erd-card" rx="7" width="{NODE_W}" height="{h}" '
            f'fill="{theme.card_bg}" stroke="{theme.card_border}" stroke-width="1" />'
        )
        parts.append(f'    <rect rx="7" width="{NODE_W}" height="{HEADER_H}" fill="{header_col}" />')
        parts.append(f'    <rect y="{HEADER_H - 7}" width="{NODE_W}" height="7" fill="{header_col}" />')

        parts.append(
            f'    <text x="12" y="{HEADER_H / 2 + 1}" font-size="13" font-weight="600" '
            f'fill="white" dominant-baseline="middle" '
            f'style="letter-spacing: 0.01em;">{escape(table.class_name)}</text>'
        )

        for i, col in enumerate(table.columns):
            fy = HEADER_H + PAD + i * FIELD_H + FIELD_H / 2 + 1
            if i > 0:
                sep_y = HEADER_H + PAD + i * FIELD_H
                parts.append(
                    f'    <line x1="10" y1="{sep_y}" x2="{NODE_W - 10}" y2="{sep_y}" '
                    f'stroke="{theme.separator_color}" stroke-width="1" />'
                )
            col_color = (
                theme.kind_colors.get("pk", "#5C2472") if col.is_pk
                else "#9a3412" if col.is_fk
                else theme.field_text_color
            )
            col_weight = "700" if col.is_pk else "400"
            kind_color = theme.kind_colors.get(col.kind, "#9ca3af")
            kind_label = theme.kind_labels.get(col.kind, col.kind)
            if not col.is_pk and not col.is_fk and col.nullable:
                kind_label += "?"

            parts.append(
                f'    <text x="10" y="{fy}" font-size="10" '
                f'font-family="\'Courier New\', Courier, monospace" '
                f'fill="{col_color}" font-weight="{col_weight}" '
                f'dominant-baseline="middle">{escape(col.name)}</text>'
            )
            parts.append(
                f'    <text x="{NODE_W - 8}" y="{fy}" font-size="9" '
                f'font-family="\'Courier New\', Courier, monospace" '
                f'fill="{kind_color}" text-anchor="end" '
                f'dominant-baseline="middle" opacity="0.9">{escape(kind_label)}</text>'
            )

        parts.append("  </g>")

    parts.append("</svg>")
    return "\n".join(parts)
