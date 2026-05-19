# erdalchemy

Interactive ERD visualizer for SQLAlchemy 2.0 models. Introspects your `DeclarativeBase` metadata and generates diagram files with no manual configuration required.

- Drag-and-drop interactive HTML output
- Two layout algorithms: force-directed (general) and star (optimized for star/warehouse schemas)
- Hover highlighting for tables and relationships
- Export to HTML, SVG, PNG, and PDF
- Built-in color themes and per-table color overrides
- Multi-schema support with visual grouping and cross-schema FKs
- Zero dependencies beyond SQLAlchemy

![preview](https://raw.githubusercontent.com/JoseVelazcoH/ERDAlchemy/main/examples/blog/blog.png)

## Installation

```bash
pip install erdalchemy
```

PNG and PDF export require an optional dependency:

```bash
pip install "erdalchemy[all]"
```

## Quick start

```python
from sqlalchemy_erd import generate_erd
from myapp.models import Base

generate_erd(Base, output="erd.html")
```

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

# Tune layout parameters
sqlalchemy-erd myapp.models:Base --k-repulse 50000 --k-attract 0.05 --ideal-len 350

# Use star layout for star/warehouse schemas or disconnected tables
sqlalchemy-erd myapp.models:Base --layout star
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

# Tune layout parameters
generate_erd(Base, output="erd.html", k_repulse=50000, k_attract=0.05, ideal_len=350)

# Use star layout for star/warehouse schemas or disconnected tables
generate_erd(Base, output="erd.svg", format="svg", layout="star")
```

## Layout algorithms

### Force-directed (default)

General-purpose physics-based layout. Works well for most schemas with connected tables.

```python
generate_erd(Base, output="erd.html", layout="force")
```

### Star

Deterministic column-based layout optimized for star/snowflake schemas and disconnected tables. Produces clean, readable diagrams without arrow crossings for ETL/data warehouse patterns.

```python
generate_erd(Base, output="erd.html", layout="star")
```

The algorithm:
1. **Fact tables** (most FK columns) are placed in the center
2. **Catalog tables** (FK targets) are split into left and right columns, ordered by FK column position
3. **Disconnected tables** (no FK edges) are arranged in a grid below

When there are multiple fact tables, catalogs are placed above and fact tables side by side below.

## Themes

Five built-in themes: `default`, `blue`, `green`, `dark`, `rose`.

Preview images for each theme are available in [`examples/themes/`](https://github.com/JoseVelazcoH/ERDAlchemy/tree/main/examples/themes).

```python
generate_erd(Base, theme="dark")
```

Per-table color overrides let you assign any hex color to individual tables while keeping the rest of the theme intact:

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

## Force-directed layout tuning

The force-directed layout (`layout="force"`) can be customized via four parameters:

| Parameter | Default | Description |
|---|---|---|
| `k_repulse` | `35000` | Repulsion strength between all nodes. Increase to spread tables further apart. |
| `k_attract` | `0.1` | Attraction strength between connected nodes. Higher values pull FK-related tables closer. |
| `k_align` | `0.02` | Horizontal-alignment force. Pushes connected tables to the same Y, favoring side-by-side placement. |
| `ideal_len` | `280` | Target edge length (px) between connected tables. |

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
| `Boolean` | `bool` |
| `JSON` | `json` |
| `Uuid` | `uuid` |

Nullable columns display a `?` suffix (e.g. `text?`, `date?`).

## Relationship types

| Cardinality | Line style |
|---|---|
| 1:N | Solid with arrow |
| N:N | Dashed with arrow |
| Cross-schema FK | Dashed with longer gaps |

## Examples

See the [`examples/`](https://github.com/JoseVelazcoH/ERDAlchemy/tree/main/examples) directory:

- [`examples/blog/`](https://github.com/JoseVelazcoH/ERDAlchemy/tree/main/examples/blog) - blog schema (User, Post, Comment)
- [`examples/ecommerce/`](https://github.com/JoseVelazcoH/ERDAlchemy/tree/main/examples/ecommerce) - 1:N chains (Category, Product, Order, Customer, OrderItem)
- [`examples/university/`](https://github.com/JoseVelazcoH/ERDAlchemy/tree/main/examples/university) - N:N via association tables (Student, Course, Professor, Department)
- [`examples/hr/`](https://github.com/JoseVelazcoH/ERDAlchemy/tree/main/examples/hr) - 1:1 and 1:N (Employee, EmployeeProfile, Department, Project)
- [`examples/multi_schema/`](https://github.com/JoseVelazcoH/ERDAlchemy/tree/main/examples/multi_schema) - multi-schema with cross-schema FKs (public, billing, audit)

## License

MIT
