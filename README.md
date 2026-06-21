# erdalchemy

Interactive ERD visualizer for SQLAlchemy 2.0 models. Point it at your `DeclarativeBase` and get a diagram, no manual configuration.

<p align="center">
  <img src="https://raw.githubusercontent.com/JoseVelazcoH/ERDAlchemy/main/examples/showcase/showcase.png" alt="preview" width="90%">
</p>

- Drag-and-drop interactive HTML, with hover highlighting
- Three layouts: hierarchical **layered** (default), force-directed, and star
- Orthogonal edge routing that follows foreign keys without cutting across cards
- Regex filtering to focus large schemas (include/exclude tables and columns)
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

Full reference (every CLI flag, the Python API, themes, layout tuning, card sizing, and supported column types) lives in [`docs/reference.md`](https://github.com/JoseVelazcoH/ERDAlchemy/blob/main/docs/reference.md).

## Examples

See [`examples/`](https://github.com/JoseVelazcoH/ERDAlchemy/tree/main/examples) for ready-to-run schemas:

- [`showcase/`](https://github.com/JoseVelazcoH/ERDAlchemy/tree/main/examples/showcase) - 12 tables across four FK levels (the preview above)
- [`blog/`](https://github.com/JoseVelazcoH/ERDAlchemy/tree/main/examples/blog) - blog schema (User, Post, Comment)
- [`ecommerce/`](https://github.com/JoseVelazcoH/ERDAlchemy/tree/main/examples/ecommerce) - 1:N chains
- [`university/`](https://github.com/JoseVelazcoH/ERDAlchemy/tree/main/examples/university) - N:N via association tables
- [`hr/`](https://github.com/JoseVelazcoH/ERDAlchemy/tree/main/examples/hr) - 1:1 and 1:N
- [`multi_schema/`](https://github.com/JoseVelazcoH/ERDAlchemy/tree/main/examples/multi_schema) - cross-schema FKs

## Acknowledgments

Inspired by [eralchemy2](https://github.com/maurerle/eralchemy2) (originally [eralchemy](https://github.com/Alexis-benoist/eralchemy)), which pioneered generating ER diagrams from SQLAlchemy models. erdalchemy reimagines the idea with a self-contained, interactive, dependency-free renderer.

## License

MIT
