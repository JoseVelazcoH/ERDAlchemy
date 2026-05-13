# erdalchemy

Interactive ERD visualizer for SQLAlchemy 2.0 models. Introspects your `DeclarativeBase` metadata and generates diagram files with no manual configuration required.

- Drag-and-drop interactive HTML output
- Auto-layout via force-directed algorithm
- Hover highlighting for tables and relationships
- Export to HTML, SVG, PNG, and PDF
- Built-in color themes and per-table color overrides
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
```

## Python API

```python
from sqlalchemy_erd import generate_erd
from myapp.models import Base

generate_erd(Base, output="erd.html", format="html")
generate_erd(Base, output="erd.svg",  format="svg")
generate_erd(Base, output="erd.png",  format="png", scale=2)   # requires cairosvg
generate_erd(Base, output="erd.pdf",  format="pdf")             # requires cairosvg
```

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

## Examples

See the [`examples/`](https://github.com/JoseVelazcoH/ERDAlchemy/tree/main/examples) directory:

- [`examples/blog/`](https://github.com/JoseVelazcoH/ERDAlchemy/tree/main/examples/blog) - blog schema (User, Post, Comment)
- [`examples/ecommerce/`](https://github.com/JoseVelazcoH/ERDAlchemy/tree/main/examples/ecommerce) - 1:N chains (Category, Product, Order, Customer, OrderItem)
- [`examples/university/`](https://github.com/JoseVelazcoH/ERDAlchemy/tree/main/examples/university) - N:N via association tables (Student, Course, Professor, Department)
- [`examples/hr/`](https://github.com/JoseVelazcoH/ERDAlchemy/tree/main/examples/hr) - 1:1 and 1:N (Employee, EmployeeProfile, Department, Project)

## License

MIT
