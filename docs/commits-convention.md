# Commits Convention

## Format

```
<type>(<scope>): <description in imperative mood>
```

The description must be written in **imperative mood** (e.g., "add", "fix", "remove" — not "added", "fixes", "removed").

## Types

| Type       | When to use                                                  |
| ---------- | ------------------------------------------------------------ |
| `feat`     | Add new functionality                                        |
| `fix`      | Fix a bug                                                    |
| `update`   | Enhance or modify existing functionality without adding new features |
| `refactor` | Restructure code without changing behavior                   |
| `chore`    | Maintenance tasks (dependencies, CI, build, config)          |
| `docs`     | Documentation only changes                                   |
| `merge`    | Merge branches                                               |

## Scopes

| Scope      | Area                                          |
| ---------- | --------------------------------------------- |
| `core`     | Model introspection and internal data model   |
| `render`   | SVG and HTML diagram generation               |
| `layout`   | Table positioning and spatial arrangement     |
| `theme`    | Styling, colors, and visual appearance        |
| `export`   | PNG, PDF, and SVG file output                 |
| `cli`      | Command-line interface                        |
| `deps`     | Dependencies and package configuration        |
| `ci`       | CI/CD pipelines and GitHub Actions            |
| `examples` | Example schemas and demos                     |

The scope is **optional** when the change spans multiple areas or doesn't fit a single scope.

## Examples

```
feat(export): add PDF export support
feat(cli): add --theme flag to select color theme
feat(core): support composite foreign keys
fix(render): correct arrow direction for self-referencing tables
fix(layout): prevent table overlap on large schemas
update(theme): adjust default column font size
update(render): improve zoom controls responsiveness
refactor(render): extract relationship drawing into separate method
refactor(core): simplify column type resolution logic
chore(deps): upgrade sqlalchemy to 2.1
chore(ci): add Python 3.13 to test matrix
docs: add commits convention guide
docs(examples): add university schema walkthrough
merge: merge feature/export-pdf into develop
```
