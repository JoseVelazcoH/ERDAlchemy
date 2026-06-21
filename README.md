# erdalchemy

Interactive ERD visualizer for SQLAlchemy 2.0 models. Point it at your `DeclarativeBase` and get a diagram — no manual configuration.

![preview](https://raw.githubusercontent.com/JoseVelazcoH/ERDAlchemy/main/examples/blog/blog.png)

- Drag-and-drop interactive HTML, with hover highlighting
- Three layouts: hierarchical **layered** (default), force-directed, and star
- Export to HTML, SVG, PNG, and PDF
- Built-in themes and per-table color overrides
- Multi-schema support with cross-schema FKs
- Zero dependencies beyond SQLAlchemy

## Install

```bash
pip install erdalchemy
```

PNG and PDF export need an optional dependency:

```bash
pip install "erdalchemy[all]"
```

## Quick start

```python
from sqlalchemy_erd import generate_erd
from myapp.models import Base

generate_erd(Base, output="erd.html")
```

Or from the command line:

```bash
sqlalchemy-erd myapp.models:Base --format svg --output erd.svg
```

## Layouts

| Layout | When to use |
|---|---|
| `layered` (default) | General purpose. Ranks tables into columns by FK direction; cards never overlap. Best for large or wide schemas. |
| `force` | Small, highly-connected graphs where an organic shape reads better. |
| `star` | Star/snowflake and ETL schemas, or many disconnected tables. |

```python
generate_erd(Base, output="erd.html", layout="layered")
```

## Documentation

Full reference — every CLI flag, the Python API, themes, layout tuning, card sizing, and supported column types — lives in [`docs/reference.md`](docs/reference.md).

## Examples

See [`examples/`](examples) for ready-to-run schemas:

- [`blog/`](examples/blog) — blog schema (User, Post, Comment)
- [`ecommerce/`](examples/ecommerce) — 1:N chains
- [`university/`](examples/university) — N:N via association tables
- [`hr/`](examples/hr) — 1:1 and 1:N
- [`multi_schema/`](examples/multi_schema) — cross-schema FKs

## License

MIT
