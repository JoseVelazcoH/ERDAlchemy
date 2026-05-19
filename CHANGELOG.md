# Changelog

## [0.4.0](https://github.com/JoseVelazcoH/ERDAlchemy/compare/erdalchemy-v0.3.0...erdalchemy-v0.4.0) (2026-05-19)


### Features

* **layout:** add star_cols and node_width parameters ([bc03457](https://github.com/JoseVelazcoH/ERDAlchemy/commit/bc034576d565cc92b5655833f55eab46289b2015))
* **layout:** add star_cols parameter and node_width auto-sizing ([de4e9e7](https://github.com/JoseVelazcoH/ERDAlchemy/commit/de4e9e703bcaaa90a55a6d795a80edec9e52e2f9))

## [0.3.0](https://github.com/JoseVelazcoH/ERDAlchemy/compare/erdalchemy-v0.2.0...erdalchemy-v0.3.0) (2026-05-19)


### Features

* **core:** add support for Enum, ARRAY, Interval, Time, LargeBinary and TypeDecorator column types ([6731ee5](https://github.com/JoseVelazcoH/ERDAlchemy/commit/6731ee50651fb77757ee56394f5310bd152020a7))
* **core:** add support for missing SQLAlchemy column types ([df5071d](https://github.com/JoseVelazcoH/ERDAlchemy/commit/df5071d1ddf974722eb487aac56d4f585a49344f))
* **layout:** add star_layout algorithm for star schemas and disconnected graphs ([1a1381f](https://github.com/JoseVelazcoH/ERDAlchemy/commit/1a1381f6a279ee361ae7d8ead48b42b90c5e897f))
* **layout:** add star_layout algorithm for star schemas and disconnected graphs ([f3ad948](https://github.com/JoseVelazcoH/ERDAlchemy/commit/f3ad9487eb7e1a66257bddcc35f661497cb22e88))
* **theme:** add yellow, pink, navy themes and custom hex header color ([0d6aee8](https://github.com/JoseVelazcoH/ERDAlchemy/commit/0d6aee8e7d615a5cba306c42be6bdba9610cce1b))
* **theme:** add yellow, pink, navy themes and custom hex header color ([d742e59](https://github.com/JoseVelazcoH/ERDAlchemy/commit/d742e592c18d197dfa8f4d509baecf768fd7e214))

## [0.2.0](https://github.com/JoseVelazcoH/ERDAlchemy/compare/erdalchemy-v0.1.1...erdalchemy-v0.2.0) (2026-05-18)


### Features

* CLI entry point with format, theme, colors and scale flags ([c8be2c6](https://github.com/JoseVelazcoH/ERDAlchemy/commit/c8be2c68da01bb25a5d8d637c2b48b2aa52ac323))
* **cli:** add --schemas flag and schemas API parameter ([de74dd2](https://github.com/JoseVelazcoH/ERDAlchemy/commit/de74dd256486bd070a6bfc965a195e16c2e9d24a))
* color themes — default, blue, green, dark, rose with per-table overrides ([3f5132e](https://github.com/JoseVelazcoH/ERDAlchemy/commit/3f5132ee2da18fa896f2aafb01c8bc4b286c287e))
* **core:** support multi-schema introspection and layout grouping ([f70e9ea](https://github.com/JoseVelazcoH/ERDAlchemy/commit/f70e9ea1054590c7a11f151d77804634e75933e6))
* export API for HTML, SVG, PNG and PDF formats ([1d83d65](https://github.com/JoseVelazcoH/ERDAlchemy/commit/1d83d65b2fd46e239f1306eeb5160266b0497bcc))
* force-directed auto-layout algorithm with cooling schedule ([075e3cd](https://github.com/JoseVelazcoH/ERDAlchemy/commit/075e3cdf304933c9053d63f3a424afd7bdad42bc))
* interactive HTML renderer with drag-and-drop, hover highlights and in-browser export ([7a95f70](https://github.com/JoseVelazcoH/ERDAlchemy/commit/7a95f7035c761fdd9d6e45e69a7ae835978d6064))
* public API — generate_erd() with format, theme, table_colors and scale options ([6f0f599](https://github.com/JoseVelazcoH/ERDAlchemy/commit/6f0f599bc4f307ad2384300c55a9e3b0caa15cea))
* **render:** add column-level FK arrows and improve layout algorithm ([0c9b969](https://github.com/JoseVelazcoH/ERDAlchemy/commit/0c9b9696840302730fa4fdcfc912b90d46d30284))
* **render:** add cross-schema FK dashed lines and schema data to HTML ([3aee9e4](https://github.com/JoseVelazcoH/ERDAlchemy/commit/3aee9e4a5b5e611b15136c682e30ccf18f92af1c))
* support multiple PostgreSQL schemas in a single diagram ([9c57737](https://github.com/JoseVelazcoH/ERDAlchemy/commit/9c57737dc20a8f3a9953aea6d43d9a3acf96bc2e))
* **theme:** add schema color palette and auto-assignment ([80144c5](https://github.com/JoseVelazcoH/ERDAlchemy/commit/80144c5fd2ffcaf682d3fefbbe7a5a7e354061e7))


### Bug Fixes

* **introspect:** improve association table detection heuristic ([8d8edb1](https://github.com/JoseVelazcoH/ERDAlchemy/commit/8d8edb1d3fa6cebd3847f732492fd2ff35fcf596))
* **introspect:** improve association table detection heuristic ([8d6d8f7](https://github.com/JoseVelazcoH/ERDAlchemy/commit/8d6d8f7da809f33ddcf520c1fbc9c2e5c13ab3e6)), closes [#2](https://github.com/JoseVelazcoH/ERDAlchemy/issues/2)
* **introspect:** render all FKs when multiple point to the same target ([ff310b1](https://github.com/JoseVelazcoH/ERDAlchemy/commit/ff310b13963b0f7cd3f63ff0d128c4c2983b6676))
* **introspect:** render all FKs when multiple point to the same target ([1dd56e7](https://github.com/JoseVelazcoH/ERDAlchemy/commit/1dd56e7bcda7c266108b2c75b365fa84cb779150)), closes [#3](https://github.com/JoseVelazcoH/ERDAlchemy/issues/3)
* **introspect:** render all FKs when multiple point to the same target ([0845dde](https://github.com/JoseVelazcoH/ERDAlchemy/commit/0845ddee4ba2d20d0b46273ad824af2aef5f68f4)), closes [#3](https://github.com/JoseVelazcoH/ERDAlchemy/issues/3)
* use absolute GitHub raw URLs for images so they render on PyPI ([04d3c98](https://github.com/JoseVelazcoH/ERDAlchemy/commit/04d3c9810afd6ca92ee4915b93ec4c5936af9ee1))


### Improvements

* fix output paths in example scripts to match new subfolder structure ([f2c911e](https://github.com/JoseVelazcoH/ERDAlchemy/commit/f2c911e50ce6f5f833bdaefeaa90760c7cb77bfe))
* generic English examples, simplified README with single preview image ([409a6ff](https://github.com/JoseVelazcoH/ERDAlchemy/commit/409a6ff1e127e5de2e449b8b1919dfffb4144398))


### Documentation

* add commits convention guide ([4836c73](https://github.com/JoseVelazcoH/ERDAlchemy/commit/4836c7367f96705c38393d81275a27312f641866))
* add project documentation and GitHub community templates ([0d0b7c2](https://github.com/JoseVelazcoH/ERDAlchemy/commit/0d0b7c282760cf3b35113e858b6ac656249d1d76))
* demo example with sample SQLAlchemy models matching dashboard-tracking schema ([18d20d6](https://github.com/JoseVelazcoH/ERDAlchemy/commit/18d20d62568d3ddb675e68c494437dce70f1e530))
* e-commerce example with 1:N chains (Category→Product→OrderItem, Customer→Order) ([0b0035a](https://github.com/JoseVelazcoH/ERDAlchemy/commit/0b0035acb8db0e0a4f2a9c316458d2cd644c4fc0))
* **examples:** add multi-schema demo with cross-schema FKs ([ed922f5](https://github.com/JoseVelazcoH/ERDAlchemy/commit/ed922f5b80adab6685e97fd1470a49cbf3a60b9a))
* HR example with 1:1 (Employee↔Profile) and 1:N (Department→Employee, Department→Project) ([3a56c3b](https://github.com/JoseVelazcoH/ERDAlchemy/commit/3a56c3b43fafc84100029db07031d627a04c8fea))
* theme preview images, professional README with examples and LICENSE ([f2eff8c](https://github.com/JoseVelazcoH/ERDAlchemy/commit/f2eff8cc77779a30c208059924262206855e272a))
* university example with N:N relationships via association tables (Student↔Course, Professor↔Course) ([6946029](https://github.com/JoseVelazcoH/ERDAlchemy/commit/6946029e3b3897ee198d57f95db18d9a5b665f90))
* update README preview to generic 3-table blog schema, fix example links ([ae8ca21](https://github.com/JoseVelazcoH/ERDAlchemy/commit/ae8ca21c9817ab08e9c4f4c045b94d98cf992ad3))
* update README with multi-schema CLI and API usage ([8fc20e2](https://github.com/JoseVelazcoH/ERDAlchemy/commit/8fc20e2c3da01dc898af1f5c899bbd9092a994dc))
