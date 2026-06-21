# Reference

Full reference for erdalchemy. For a quick overview, see the [README](../README.md).

## Table of contents

- [CLI](#cli)
- [Python API](#python-api)
- [Filtering](#filtering)
- [Layout algorithms](#layout-algorithms)
- [Force-directed tuning](#force-directed-tuning)
- [Card width](#card-width)
- [Themes](#themes)
- [Supported column types](#supported-column-types)
- [Relationship types](#relationship-types)

## CLI

```bash
# Interactive HTML (default)
sqlalchemy-erd myapp.models:Base

# Specific format and output path
sqlalchemy-erd myapp.models:Base --format svg --output erd.svg

# With theme and custom title
sqlalchemy-erd myapp.models:Base --format png --theme blue --title "My Schema"

# Per-table color overrides as JSON
sqlalchemy-erd myapp.models:Base --colors '{"users": "#1d4ed8", "orders": "#059669"}'

# High-resolution PNG
sqlalchemy-erd myapp.models:Base --format png --scale 3

# Only include specific database schemas
sqlalchemy-erd myapp.models:Base --schemas public,billing,audit

# Filter tables / columns by regex (full-string match)
sqlalchemy-erd myapp.models:Base --exclude-tables "audit_.*" "temp_.*"
sqlalchemy-erd myapp.models:Base --include-tables "order.*" "product.*"
sqlalchemy-erd myapp.models:Base --exclude-columns created_at updated_at

# Layered is the default; switch to force or star explicitly
sqlalchemy-erd myapp.models:Base --layout force
sqlalchemy-erd myapp.models:Base --layout star --star-cols 2

# Tune the force-directed layout (only applies to --layout force)
sqlalchemy-erd myapp.models:Base --layout force --k-repulse 50000 --k-attract 0.05 --ideal-len 350

# Auto-size or fix card width
sqlalchemy-erd myapp.models:Base --node-width auto
sqlalchemy-erd myapp.models:Base --node-width 400

# Custom header color via hex
sqlalchemy-erd myapp.models:Base --theme "#6d28d9"
```

## Python API

```python
from sqlalchemy_erd import generate_erd
from myapp.models import Base

generate_erd(Base, output="erd.html", format="html")
generate_erd(Base, output="erd.svg",  format="svg")
generate_erd(Base, output="erd.png",  format="png", scale=2)   # requires cairosvg
generate_erd(Base, output="erd.pdf",  format="pdf")             # requires cairosvg

# Only include specific database schemas
generate_erd(Base, output="erd.html", schemas=["public", "billing", "audit"])

# Use star layout for star/warehouse schemas or disconnected tables
generate_erd(Base, output="erd.svg", format="svg", layout="star")

# Auto-size or fix card width
generate_erd(Base, output="erd.svg", format="svg", node_width="auto")
generate_erd(Base, output="erd.svg", format="svg", node_width=400)
```

## Filtering

On large schemas (30-100+ tables) you usually want to focus on a subset. Pass a
`Filters` object to hide tables or columns. Patterns are **full-string regex**
(anchored), so a single pattern covers a whole naming family.

```python
from sqlalchemy_erd import generate_erd, Filters

generate_erd(
    Base,
    output="erd.html",
    filters=Filters(
        include_tables=["order.*", "product.*"],  # only these (regex)
        exclude_tables=["audit_.*", ".*_log"],     # applied after include
        exclude_columns=["created_at", "updated_at", "deleted_at"],
    ),
)
```

| Field | Behavior |
|---|---|
| `include_tables` | When set, only matching tables are rendered. Takes precedence. |
| `exclude_tables` | Removes matching tables, applied after `include_tables`. |
| `exclude_columns` | Hides matching columns from the cards. Foreign-key relationships are kept. |

Relationships that point at a filtered-out table are dropped, so no arrows dangle.
(Rendering an excluded-but-referenced table as a ghost node is a planned
enhancement.)

## Layout algorithms

### Layered (default)

Hierarchical layout that ranks tables into columns by foreign-key direction (parent → child, left to right), orders nodes within each column to reduce edge crossings, and stacks cards so they never overlap. The best general-purpose choice, especially for schemas with many tables or wide tables (10+ columns), where it reads like a hand-drawn ERD.

```python
generate_erd(Base, output="erd.html", layout="layered")
```

### Force-directed

Physics-based layout with organic placement. Works for small, highly-connected graphs, but can overlap cards on dense or wide schemas. See [Force-directed tuning](#force-directed-tuning).

```python
generate_erd(Base, output="erd.html", layout="force")
```

### Star

Deterministic column-based layout optimized for star/snowflake schemas and disconnected tables. Produces clean, readable diagrams without arrow crossings for ETL/data warehouse patterns.

```python
generate_erd(Base, output="erd.html", layout="star")
```

The `star_cols` parameter controls how many catalog columns are placed on each side of the fact table:

```python
# Auto (default): 1 per side when ≤12 catalogs, 2 per side when >12
generate_erd(Base, output="erd.html", layout="star")

# Force 2 catalog columns per side → 5 total columns
generate_erd(Base, output="erd.html", layout="star", star_cols=2)
```

| `star_cols` | Total columns | Description |
|---|---|---|
| `None` (default) | Auto | 1 per side for ≤12 catalogs, 2 per side for >12 |
| `1` | 3 | One column per side (left, center, right) |
| `2` | 5 | Two columns per side |
| `3` | 7 | Three columns per side |

The algorithm:
1. **Fact tables** (most FK columns) are placed in the center
2. **Catalog tables** (FK targets) are distributed across left and right columns, ordered by FK column position
3. **Disconnected tables** (no FK edges) are arranged in a grid below

When there are multiple fact tables, catalogs are placed above and fact tables side by side below.

## Force-directed tuning

The force-directed layout (`layout="force"`) is tuned with a `ForceParams` object in the Python API, or the matching flags on the CLI:

```python
from sqlalchemy_erd import generate_erd, ForceParams

generate_erd(
    Base, output="erd.html", layout="force",
    force=ForceParams(k_repulse=50000, k_attract=0.05, k_align=0.02, ideal_len=350),
)
```

```bash
sqlalchemy-erd myapp.models:Base --layout force \
    --k-repulse 50000 --k-attract 0.05 --k-align 0.02 --ideal-len 350
```

| Parameter | Default | Description |
|---|---|---|
| `k_repulse` | `35000` | Repulsion strength between all nodes. Increase to spread tables further apart. |
| `k_attract` | `0.1` | Attraction strength between connected nodes. Higher values pull FK-related tables closer. |
| `k_align` | `0.02` | Horizontal-alignment force. Pushes connected tables to the same Y, favoring side-by-side placement. |
| `ideal_len` | `280` | Target edge length (px) between connected tables. |

## Card width

By default, cards are 218px wide. For schemas with long column names, auto-size or set a fixed width:

```python
# Auto: calculates width based on the longest column name + type label
generate_erd(Base, node_width="auto")

# Fixed: set exact width in pixels
generate_erd(Base, node_width=400)
```

| `node_width` | Behavior |
|---|---|
| `None` (default) | 218px (built-in default) |
| `"auto"` | Fits the widest column name + type label across all tables |
| `int` | Fixed width in pixels |

## Themes

Eight built-in themes: `default`, `blue`, `green`, `dark`, `rose`, `yellow`, `pink`, `navy`.

Preview images for each theme are available in [`examples/themes/`](../examples/themes).

```python
generate_erd(Base, theme="dark")
generate_erd(Base, theme="pink")
```

Pass a hex color string to set a custom header color:

```python
generate_erd(Base, theme="#6d28d9")
```

Per-table color overrides assign any hex color to individual tables while keeping the rest of the theme intact:

```python
generate_erd(
    Base,
    theme="default",
    table_colors={
        "users":    "#1e40af",
        "orders":   "#065f46",
        "products": "#9f1239",
    },
)
```

## Supported column types

| SQLAlchemy type | Badge |
|---|---|
| Primary key | `PK` |
| Foreign key | `FK` |
| `String` | `string` |
| `Text` | `text` |
| `Integer` / `BigInteger` / `SmallInteger` | `int` / `bigint` / `smallint` |
| `Float` / `Numeric` | `float` / `numeric` |
| `Date` | `date` |
| `DateTime` | `datetime` |
| `Time` | `time` |
| `Boolean` | `bool` |
| `JSON` / `JSONB` | `json` |
| `Uuid` | `uuid` |
| `Enum` | `enum` |
| `ARRAY` | `array` |
| `Interval` | `interval` |
| `LargeBinary` | `binary` |
| `TypeDecorator` | resolves to underlying `impl` type |

Nullable columns display a `?` suffix (e.g. `text?`, `date?`).

## Relationship types

| Cardinality | Line style |
|---|---|
| 1:N | Solid with arrow |
| N:N | Dashed with arrow |
| Cross-schema FK | Dashed with longer gaps |
