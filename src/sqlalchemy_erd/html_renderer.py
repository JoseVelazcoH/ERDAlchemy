from __future__ import annotations

import json
from xml.sax.saxutils import escape

from sqlalchemy_erd.introspect import TableInfo, RelationshipInfo
from sqlalchemy_erd.layout import NODE_W, HEADER_H, FIELD_H, PAD, node_h
from sqlalchemy_erd.theme import Theme


def render_html(
    tables: list[TableInfo],
    relationships: list[RelationshipInfo],
    positions: dict[str, tuple[float, float]],
    theme: Theme,
    title: str = "ERD",
) -> str:
    entities_js = _build_entities_json(tables, theme)
    relations_js = _build_relations_json(relationships, tables, positions)
    positions_js = json.dumps({t.name: list(positions[t.name]) for t in tables})
    schema_colors_js = json.dumps({
        (s if s is not None else "_default"): c
        for s, c in theme.schema_colors.items()
    })

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(title)}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ background: {theme.bg_color}; overflow: auto; font-family: system-ui, -apple-system, sans-serif; }}
.toolbar {{
  position: fixed; top: 0; left: 0; right: 0; z-index: 10;
  display: flex; align-items: center; gap: 8px;
  padding: 8px 16px;
  background: rgba(255,255,255,0.92); backdrop-filter: blur(8px);
  border-bottom: 1px solid #e5e7eb;
}}
.toolbar h1 {{ font-size: 14px; font-weight: 600; color: #1f2937; margin-right: auto; }}
.toolbar button {{
  padding: 5px 12px; font-size: 11px; border-radius: 6px; cursor: pointer;
  border: 1px solid #d1d5db; background: white; color: #374151;
  transition: background 0.15s;
}}
.toolbar button:hover {{ background: #f3f4f6; }}
.toolbar select {{
  padding: 5px 8px; font-size: 11px; border-radius: 6px;
  border: 1px solid #d1d5db; background: white; color: #374151;
}}
.hint {{
  position: fixed; bottom: 12px; right: 16px;
  font-size: 11px; color: #9ca3af; pointer-events: none; user-select: none;
}}
svg {{ display: block; user-select: none; }}
</style>
</head>
<body>
<div class="toolbar">
  <h1>{escape(title)}</h1>
  <select id="exportFmt">
    <option value="html">HTML</option>
    <option value="svg">SVG</option>
    <option value="png">PNG</option>
  </select>
  <button onclick="exportDiagram()">Export</button>
  <button onclick="resetLayout()">Reset</button>
</div>
<p class="hint">Drag to move &middot; Hover to highlight</p>

<svg id="erd" style="margin-top: 44px;"></svg>

<script>
// ── Data ──
const ENTITIES = {entities_js};
const RELATIONS = {relations_js};
const INITIAL_POS = {positions_js};
const SCHEMA_COLORS = {schema_colors_js};

const NODE_W = {NODE_W};
const HEADER_H = {HEADER_H};
const FIELD_H = {FIELD_H};
const PAD_ = {PAD};

const THEME = {{
  bgColor: "{theme.bg_color}",
  cardBg: "{theme.card_bg}",
  cardBorder: "{theme.card_border}",
  edgeColor: "{theme.edge_color}",
  hiColor: "{theme.highlight_color}",
  dotColor: "{theme.dot_color}",
  fieldText: "{theme.field_text_color}",
  separator: "{theme.separator_color}",
}};

// ── State ──
let positions = JSON.parse(JSON.stringify(INITIAL_POS));
let dragging = null;
let hoveredId = null;

const ENTITY_MAP = Object.fromEntries(ENTITIES.map(e => [e.id, e]));

function nodeH(e) {{ return HEADER_H + PAD_ + e.fields.length * FIELD_H + PAD_; }}

function colIndex(entity, colName) {{
  for (let i = 0; i < entity.fields.length; i++) {{
    if (entity.fields[i].name === colName) return i;
  }}
  return null;
}}

function firstPkIndex(entity) {{
  for (let i = 0; i < entity.fields.length; i++) {{
    if (entity.fields[i].nameWeight === '700') return i;
  }}
  return null;
}}

function connPt(id, side, cIdx) {{
  const [x, y] = positions[id];
  const e = ENTITY_MAP[id];
  const h = nodeH(e);
  const cy = cIdx != null ? y + HEADER_H + PAD_ + cIdx * FIELD_H + Math.floor(FIELD_H/2) : y + h/2;
  if (side === 'top')    return [x + NODE_W/2, y];
  if (side === 'bottom') return [x + NODE_W/2, y + h];
  if (side === 'left')   return [x, cy];
  return [x + NODE_W, cy];
}}

function bestSide(fromId, toId) {{
  const [fx, fy] = positions[fromId];
  const [tx, ty] = positions[toId];
  const fh = nodeH(ENTITY_MAP[fromId]);
  const th = nodeH(ENTITY_MAP[toId]);
  const dx = (tx + NODE_W/2) - (fx + NODE_W/2);
  const dy = (ty + th/2) - (fy + fh/2);
  if (Math.abs(dx) > Math.abs(dy)) {{
    return dx > 0 ? ['right','left'] : ['left','right'];
  }}
  return dy > 0 ? ['bottom','top'] : ['top','bottom'];
}}

function sideVec(side, d) {{
  if (side === 'top')    return [0, -d];
  if (side === 'bottom') return [0,  d];
  if (side === 'left')   return [-d, 0];
  return [d, 0];
}}

function makePath(fp, fs, tp, ts) {{
  const D = 70;
  const o1 = sideVec(fs, D), o2 = sideVec(ts, D);
  return `M ${{fp[0]}} ${{fp[1]}} C ${{fp[0]+o1[0]}} ${{fp[1]+o1[1]}} ${{tp[0]+o2[0]}} ${{tp[1]+o2[1]}} ${{tp[0]}} ${{tp[1]}}`;
}}

function labelPos(pt, side) {{
  const a = sideVec(side, 20);
  const p = (side==='top'||side==='bottom') ? [13,0] : [0,-12];
  return [pt[0]+a[0]+p[0], pt[1]+a[1]+p[1]];
}}

// ── Render ──
const NS = 'http://www.w3.org/2000/svg';
function el(tag, attrs, parent) {{
  const e = document.createElementNS(NS, tag);
  for (const [k,v] of Object.entries(attrs||{{}})) {{
    if (k === 'textContent') e.textContent = v;
    else e.setAttribute(k, v);
  }}
  if (parent) parent.appendChild(e);
  return e;
}}

function render() {{
  const svg = document.getElementById('erd');
  svg.innerHTML = '';

  const maxX = Math.max(...ENTITIES.map(e => positions[e.id][0] + NODE_W + 60));
  const maxY = Math.max(...ENTITIES.map(e => positions[e.id][1] + nodeH(e) + 60));
  svg.setAttribute('width', maxX);
  svg.setAttribute('height', maxY);
  svg.style.cursor = dragging ? 'grabbing' : 'default';

  const defs = el('defs', {{}}, svg);
  const pat = el('pattern', {{ id:'erd-dots', width:'24', height:'24', patternUnits:'userSpaceOnUse' }}, defs);
  el('circle', {{ cx:'1', cy:'1', r:'0.8', fill: THEME.dotColor }}, pat);
  const mk = el('marker', {{ id:'arr', markerWidth:'10', markerHeight:'7', refX:'9', refY:'3.5', orient:'auto' }}, defs);
  el('polygon', {{ points:'0 0, 10 3.5, 0 7', fill: THEME.edgeColor }}, mk);
  const mkHi = el('marker', {{ id:'arr-hi', markerWidth:'10', markerHeight:'7', refX:'9', refY:'3.5', orient:'auto' }}, defs);
  el('polygon', {{ points:'0 0, 10 3.5, 0 7', fill: THEME.hiColor }}, mkHi);

  el('rect', {{ width:'100%', height:'100%', fill: THEME.bgColor }}, svg);
  el('rect', {{ width:'100%', height:'100%', fill:'url(#erd-dots)' }}, svg);

  // Edges — tagged with data attributes for updateHighlights
  for (const rel of RELATIONS) {{
    if (!ENTITY_MAP[rel.from] || !ENTITY_MAP[rel.to]) continue;
    const fe = ENTITY_MAP[rel.from], te = ENTITY_MAP[rel.to];
    const isVia = rel.fkCol && rel.fkCol.startsWith('via ');
    const fromIdx = isVia ? null : firstPkIndex(fe);
    const toIdx = isVia ? null : colIndex(te, rel.fkCol);

    let fs, ts, fp, tp;
    if (isVia) {{
      [fs, ts] = bestSide(rel.from, rel.to);
      fp = connPt(rel.from, fs);
      tp = connPt(rel.to, ts);
    }} else {{
      const [fx, fy] = positions[rel.from];
      const [tx, ty] = positions[rel.to];
      const dx = (tx + NODE_W/2) - (fx + NODE_W/2);
      const dy = (ty + nodeH(te)/2) - (fy + nodeH(fe)/2);
      if (Math.abs(dx) > Math.abs(dy)) {{
        fs = dx > 0 ? 'right' : 'left';
        ts = dx > 0 ? 'left' : 'right';
      }} else {{
        const side = dx >= 0 ? 'right' : 'left';
        fs = ts = side;
      }}
      fp = connPt(rel.from, fs, fromIdx);
      tp = connPt(rel.to, ts, toIdx);
    }}

    const d = makePath(fp, fs, tp, ts);
    const isNN = rel.fromCard === 'N' && rel.toCard === 'N';
    const isCross = Object.keys(SCHEMA_COLORS).length > 0 &&
      (fe.schema != null ? fe.schema : '_default') !== (te.schema != null ? te.schema : '_default');

    const g = el('g', {{ 'data-rel-from': rel.from, 'data-rel-to': rel.to }}, svg);
    el('path', {{ d, fill:'none', stroke:'transparent', 'stroke-width':'18' }}, g);
    const edgeAttrs = {{
      class: 'erd-edge', d, fill:'none',
      stroke: THEME.edgeColor, 'stroke-width': '1.5',
      'marker-end': 'url(#arr)'
    }};
    if (isNN) edgeAttrs['stroke-dasharray'] = '5 3';
    else if (isCross) edgeAttrs['stroke-dasharray'] = '8 4';
    el('path', edgeAttrs, g);

    const fl = labelPos(fp, fs);
    el('text', {{
      class: 'erd-label', x: fl[0], y: fl[1], 'font-size':'11', 'font-family':'monospace',
      fill: THEME.edgeColor, 'text-anchor':'middle', 'dominant-baseline':'middle',
      textContent: rel.fromCard
    }}, g);
    const tl = labelPos(tp, ts);
    el('text', {{
      class: 'erd-label', x: tl[0], y: tl[1], 'font-size':'11', 'font-family':'monospace',
      fill: THEME.edgeColor, 'text-anchor':'middle', 'dominant-baseline':'middle',
      textContent: rel.toCard
    }}, g);
  }}

  // Nodes — tagged with data attributes for updateHighlights
  for (const entity of ENTITIES) {{
    const [x, y] = positions[entity.id];
    const h = nodeH(entity);

    const g = el('g', {{
      transform: `translate(${{x}}, ${{y}})`,
      style: 'cursor: grab',
      'data-id': entity.id,
    }}, svg);

    el('rect', {{ x:'3', y:'3', rx:'7', width: NODE_W, height: h, fill:'rgba(0,0,0,0.06)' }}, g);
    el('rect', {{
      class: 'erd-card', rx:'7', width: NODE_W, height: h,
      fill: THEME.cardBg, stroke: THEME.cardBorder, 'stroke-width': '1'
    }}, g);
    el('rect', {{ class: 'erd-hdr1', rx:'7', width: NODE_W, height: HEADER_H, fill: entity.headerColor }}, g);
    el('rect', {{ class: 'erd-hdr2', y: HEADER_H - 7, width: NODE_W, height:'7', fill: entity.headerColor }}, g);
    el('text', {{
      x:'12', y: HEADER_H/2+1, 'font-size':'13', 'font-weight':'600',
      fill:'white', 'dominant-baseline':'middle',
      style:'letter-spacing:0.01em;',
      textContent: entity.label
    }}, g);

    for (let i = 0; i < entity.fields.length; i++) {{
      const field = entity.fields[i];
      const fy = HEADER_H + PAD_ + i * FIELD_H + FIELD_H/2 + 1;
      if (i > 0) {{
        const sy = HEADER_H + PAD_ + i * FIELD_H;
        el('line', {{ x1:'10', y1:sy, x2:NODE_W-10, y2:sy, stroke: THEME.separator, 'stroke-width':'1' }}, g);
      }}
      el('text', {{
        x:'10', y:fy, 'font-size':'10',
        'font-family':"'Courier New', Courier, monospace",
        fill: field.nameColor, 'font-weight': field.nameWeight,
        'dominant-baseline':'middle', textContent: field.name
      }}, g);
      el('text', {{
        x: NODE_W-8, y:fy, 'font-size':'9',
        'font-family':"'Courier New', Courier, monospace",
        fill: field.kindColor, 'text-anchor':'end',
        'dominant-baseline':'middle', opacity:'0.9', textContent: field.kindLabel
      }}, g);
    }}

    g.addEventListener('pointerdown', e => {{
      e.preventDefault();
      dragging = {{
        id: entity.id,
        startX: e.clientX, startY: e.clientY,
        origX: positions[entity.id][0], origY: positions[entity.id][1]
      }};
    }});
    g.addEventListener('mouseenter', () => {{ hoveredId = entity.id; updateHighlights(); }});
    g.addEventListener('mouseleave', () => {{ hoveredId = null; updateHighlights(); }});
  }}
}}

// Lightweight: only mutates attributes on existing DOM nodes, never destroys them.
function updateHighlights() {{
  const svg = document.getElementById('erd');

  // Update edges
  svg.querySelectorAll('g[data-rel-from]').forEach(g => {{
    const from = g.getAttribute('data-rel-from');
    const to = g.getAttribute('data-rel-to');
    const hi = hoveredId && (from === hoveredId || to === hoveredId);
    const edge = g.querySelector('.erd-edge');
    if (edge) {{
      edge.setAttribute('stroke', hi ? THEME.hiColor : THEME.edgeColor);
      edge.setAttribute('stroke-width', hi ? '2' : '1.5');
      edge.setAttribute('marker-end', `url(#${{hi ? 'arr-hi' : 'arr'}})`);
    }}
    g.querySelectorAll('.erd-label').forEach(lbl => {{
      lbl.setAttribute('fill', hi ? THEME.hiColor : THEME.edgeColor);
    }});
  }});

  // Update nodes
  svg.querySelectorAll('g[data-id]').forEach(g => {{
    const id = g.getAttribute('data-id');
    const entity = ENTITY_MAP[id];
    const isHv = hoveredId === id;
    const isCn = hoveredId && hoveredId !== id &&
      RELATIONS.some(r => (r.from === hoveredId && r.to === id) || (r.to === hoveredId && r.from === id));

    const card = g.querySelector('.erd-card');
    if (card) {{
      card.setAttribute('stroke', isHv ? entity.headerColor : isCn ? THEME.hiColor : THEME.cardBorder);
      card.setAttribute('stroke-width', (isHv || isCn) ? '2' : '1');
    }}
    const hdr1 = g.querySelector('.erd-hdr1');
    const hdr2 = g.querySelector('.erd-hdr2');
    const headerCol = isHv ? entity.hoverColor : entity.headerColor;
    if (hdr1) hdr1.setAttribute('fill', headerCol);
    if (hdr2) hdr2.setAttribute('fill', headerCol);
  }});
}}

window.addEventListener('pointermove', e => {{
  if (!dragging) return;
  const dx = e.clientX - dragging.startX;
  const dy = e.clientY - dragging.startY;
  positions[dragging.id] = [
    Math.max(8, dragging.origX + dx),
    Math.max(8, dragging.origY + dy)
  ];
  render();
}});

window.addEventListener('pointerup', () => {{
  if (dragging) {{ dragging = null; render(); }}
}});

function resetLayout() {{
  positions = JSON.parse(JSON.stringify(INITIAL_POS));
  hoveredId = null;
  render();
}}

function exportDiagram() {{
  const fmt = document.getElementById('exportFmt').value;
  const svg = document.getElementById('erd');

  if (fmt === 'html') {{
    const blob = new Blob([document.documentElement.outerHTML], {{ type: 'text/html' }});
    downloadBlob(blob, 'erd.html');
  }} else if (fmt === 'svg') {{
    const blob = new Blob([svg.outerHTML], {{ type: 'image/svg+xml' }});
    downloadBlob(blob, 'erd.svg');
  }} else if (fmt === 'png') {{
    const svgData = new XMLSerializer().serializeToString(svg);
    const canvas = document.createElement('canvas');
    const scale = 2;
    canvas.width = parseInt(svg.getAttribute('width')) * scale;
    canvas.height = parseInt(svg.getAttribute('height')) * scale;
    const ctx = canvas.getContext('2d');
    ctx.scale(scale, scale);
    const img = new Image();
    img.onload = () => {{
      ctx.drawImage(img, 0, 0);
      canvas.toBlob(blob => downloadBlob(blob, 'erd.png'), 'image/png');
    }};
    img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)));
  }}
}}

function downloadBlob(blob, name) {{
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = name;
  a.click();
  URL.revokeObjectURL(a.href);
}}

render();
</script>
</body>
</html>"""


def _build_entities_json(
    tables: list[TableInfo],
    theme: Theme,
) -> str:
    entities = []
    for t in tables:
        fields = []
        for col in t.columns:
            name_color = (
                theme.kind_colors.get("pk", "#5C2472") if col.is_pk
                else "#9a3412" if col.is_fk
                else theme.field_text_color
            )
            name_weight = "700" if col.is_pk else "400"
            kind_color = theme.kind_colors.get(col.kind, "#9ca3af")
            kind_label = theme.kind_labels.get(col.kind, col.kind)
            if not col.is_pk and not col.is_fk and col.nullable:
                kind_label += "?"

            fields.append({
                "name": col.name,
                "nameColor": name_color,
                "nameWeight": name_weight,
                "kindColor": kind_color,
                "kindLabel": kind_label,
            })

        header_color = theme.get_header_color(t.name)
        entities.append({
            "id": t.name,
            "label": t.class_name,
            "schema": t.schema,
            "headerColor": header_color,
            "hoverColor": theme.header_hover_color,
            "fields": fields,
        })
    return json.dumps(entities)


def _build_relations_json(
    relationships: list[RelationshipInfo],
    tables: list[TableInfo],
    positions: dict[str, tuple[float, float]],
) -> str:
    table_names = {t.name for t in tables}
    rels = []
    for r in relationships:
        if r.from_table in table_names and r.to_table in table_names:
            rels.append({
                "from": r.from_table,
                "to": r.to_table,
                "fromCard": r.from_card,
                "toCard": r.to_card,
                "fkCol": r.fk_column,
            })
    return json.dumps(rels)
