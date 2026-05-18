# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in ERDAlchemy, please report it responsibly.

**Do not open a public GitHub issue for security vulnerabilities.**

Instead, use [GitHub's private vulnerability reporting](https://github.com/JoseVelazcoH/ERDAlchemy/security/advisories/new) to submit your report. Include:

- A description of the vulnerability
- Steps to reproduce the issue
- The potential impact
- Any suggested fix (optional)

You can expect an initial response within **72 hours**. Once the issue is confirmed, a fix will be prioritized and released as a patch version. You will be credited in the release notes unless you prefer to remain anonymous.

## Scope

ERDAlchemy is a visualization library that reads SQLAlchemy model metadata and produces SVG/PNG/PDF diagrams. It does not handle authentication, network requests, or user-supplied SQL. Security concerns most likely to be relevant include:

- SVG injection via crafted model metadata (table names, column names)
- Path traversal in file output paths
- Dependency vulnerabilities (SQLAlchemy, CairoSVG)

## Best Practices for Users

- Keep ERDAlchemy and its dependencies up to date.
- Avoid passing untrusted input as model metadata if generating diagrams in automated pipelines.
