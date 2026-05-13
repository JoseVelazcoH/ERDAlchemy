# sqlalchemy-erd

Interactive ERD visualization for SQLAlchemy 2.0 models.

## Install

```bash
pip install sqlalchemy-erd
```

## Quick start

```python
from sqlalchemy_erd import generate_erd
from myapp.models import Base

generate_erd(Base, output="erd.html")
```

## CLI

```bash
sqlalchemy-erd myapp.models:Base --format html --output erd.html
sqlalchemy-erd myapp.models:Base --format svg --theme blue
sqlalchemy-erd myapp.models:Base --format png --scale 3
```

## Themes

Built-in: `default`, `blue`, `green`, `dark`, `rose`

Per-table colors:

```python
generate_erd(Base, table_colors={"users": "#1d4ed8", "orders": "#059669"})
```

## Export formats

- **HTML** — interactive (drag & drop, hover highlighting, in-browser export)
- **SVG** — static vector
- **PNG** — raster (requires `pip install sqlalchemy-erd[png]`)
- **PDF** — document (requires `pip install sqlalchemy-erd[pdf]`)
