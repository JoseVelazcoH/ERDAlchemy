"""Tests for the public generate_erd API and CLI."""

import os
import pytest
from pathlib import Path

from sqlalchemy_erd import generate_erd
from sqlalchemy_erd.cli import main, _resolve_target
from sqlalchemy_erd.introspect import Filters


# ── generate_erd API ─────────────────────────────────────────────────────────

class TestGenerateErd:
    def test_html_output(self, blog_base, tmp_path):
        out = tmp_path / "test.html"
        result = generate_erd(blog_base, output=str(out), format="html")
        assert isinstance(result, str)
        assert out.exists()
        assert "<!DOCTYPE html>" in out.read_text()

    def test_svg_output(self, blog_base, tmp_path):
        out = tmp_path / "test.svg"
        result = generate_erd(blog_base, output=str(out), format="svg")
        assert isinstance(result, str)
        assert out.exists()
        assert "<?xml" in result

    def test_png_output(self, blog_base, tmp_path):
        out = tmp_path / "test.png"
        result = generate_erd(blog_base, output=str(out), format="png")
        assert isinstance(result, bytes)
        assert out.exists()
        assert result[:8] == b"\x89PNG\r\n\x1a\n"

    def test_pdf_output(self, blog_base, tmp_path):
        out = tmp_path / "test.pdf"
        result = generate_erd(blog_base, output=str(out), format="pdf")
        assert isinstance(result, bytes)
        assert out.exists()
        assert result[:5] == b"%PDF-"

    def test_unknown_format_raises(self, blog_base, tmp_path):
        with pytest.raises(ValueError, match="Unknown format"):
            generate_erd(blog_base, output=str(tmp_path / "test.xyz"), format="xyz")

    def test_custom_theme(self, blog_base, tmp_path):
        out = tmp_path / "test.html"
        result = generate_erd(blog_base, output=str(out), format="html", theme="dark")
        assert isinstance(result, str)

    def test_table_colors(self, blog_base, tmp_path):
        out = tmp_path / "test.html"
        result = generate_erd(
            blog_base, output=str(out), format="html",
            table_colors={"users": "#ff0000"},
        )
        assert "#ff0000" in result

    def test_custom_title(self, blog_base, tmp_path):
        out = tmp_path / "test.html"
        result = generate_erd(blog_base, output=str(out), format="html", title="My ERD")
        assert "My ERD" in result

    def test_metadata_input(self, blog_base, tmp_path):
        out = tmp_path / "test.html"
        result = generate_erd(blog_base.metadata, output=str(out), format="html")
        assert isinstance(result, str)

    def test_schemas_param(self, multi_schema_metadata_fixture, tmp_path):
        out = tmp_path / "test.html"
        result = generate_erd(
            multi_schema_metadata_fixture,
            output=str(out), format="html",
            schemas=["auth"],
        )
        assert isinstance(result, str)

    def test_star_layout(self, blog_base, tmp_path):
        out = tmp_path / "test.svg"
        result = generate_erd(blog_base, output=str(out), format="svg", layout="star")
        assert isinstance(result, str)
        assert "<svg" in result

    def test_star_layout_with_star_cols(self, blog_base, tmp_path):
        out = tmp_path / "test.svg"
        result = generate_erd(blog_base, output=str(out), format="svg", layout="star", star_cols=1)
        assert isinstance(result, str)
        assert "<svg" in result

    def test_node_width_auto(self, blog_base, tmp_path):
        out = tmp_path / "test.svg"
        result = generate_erd(blog_base, output=str(out), format="svg", node_width="auto")
        assert isinstance(result, str)
        assert "<svg" in result

    def test_node_width_fixed(self, blog_base, tmp_path):
        out = tmp_path / "test.svg"
        result = generate_erd(blog_base, output=str(out), format="svg", node_width=400)
        assert isinstance(result, str)
        assert 'width="400"' in result

    def test_unknown_layout_raises(self, blog_base, tmp_path):
        with pytest.raises(ValueError, match="Unknown layout"):
            generate_erd(blog_base, output=str(tmp_path / "test.svg"), format="svg", layout="bad")

    def test_default_layout_is_layered(self, blog_base, tmp_path):
        out = tmp_path / "test.svg"
        result = generate_erd(blog_base, output=str(out), format="svg")
        assert isinstance(result, str)
        assert "<svg" in result

    def test_layered_layout_explicit(self, blog_base, tmp_path):
        out = tmp_path / "test.svg"
        result = generate_erd(blog_base, output=str(out), format="svg", layout="layered")
        assert isinstance(result, str)
        assert "<svg" in result

    def test_exclude_tables_filter_drops_table_from_output(self, blog_base, tmp_path):
        out = tmp_path / "test.svg"
        result = generate_erd(
            blog_base, output=str(out), format="svg",
            filters=Filters(exclude_tables=["comments"]),
        )
        assert 'data-table="comments"' not in result
        assert 'data-table="users"' in result

    def test_exclude_columns_filter_hides_column(self, blog_base, tmp_path):
        out = tmp_path / "test.svg"
        result = generate_erd(
            blog_base, output=str(out), format="svg",
            filters=Filters(exclude_columns=["created_at"]),
        )
        assert ">created_at<" not in result

    def test_custom_force_params_accepted(self, blog_base, tmp_path):
        from sqlalchemy_erd import ForceParams
        out = tmp_path / "test.svg"
        result = generate_erd(
            blog_base, output=str(out), format="svg",
            force=ForceParams(ideal_len=400.0, k_repulse=50000.0),
        )
        assert isinstance(result, str)
        assert "<svg" in result


# ── CLI ──────────────────────────────────────────────────────────────────────

class TestCli:
    def test_cli_generates_file(self, tmp_path, monkeypatch):
        models_file = tmp_path / "models.py"
        models_file.write_text(
            "from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column\n"
            "from sqlalchemy import String\n\n"
            "class Base(DeclarativeBase):\n"
            "    pass\n\n"
            "class Foo(Base):\n"
            "    __tablename__ = 'foo'\n"
            "    id: Mapped[int] = mapped_column(primary_key=True)\n"
            "    name: Mapped[str] = mapped_column(String(50))\n"
        )
        out_file = tmp_path / "out.html"
        monkeypatch.chdir(tmp_path)
        main(["models:Base", "-o", str(out_file)])
        assert out_file.exists()
        content = out_file.read_text()
        assert "<!DOCTYPE html>" in content

    def test_cli_svg_format(self, tmp_path, monkeypatch):
        models_file = tmp_path / "models.py"
        models_file.write_text(
            "from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column\n"
            "from sqlalchemy import String\n\n"
            "class Base(DeclarativeBase):\n"
            "    pass\n\n"
            "class Bar(Base):\n"
            "    __tablename__ = 'bar'\n"
            "    id: Mapped[int] = mapped_column(primary_key=True)\n"
        )
        out_file = tmp_path / "out.svg"
        monkeypatch.chdir(tmp_path)
        main(["models:Base", "-f", "svg", "-o", str(out_file)])
        assert out_file.exists()
        content = out_file.read_text()
        assert "<svg" in content

    def test_cli_exclude_tables(self, tmp_path, monkeypatch):
        models_file = tmp_path / "filter_models.py"
        models_file.write_text(
            "from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column\n"
            "from sqlalchemy import String, ForeignKey\n\n"
            "class Base(DeclarativeBase):\n"
            "    pass\n\n"
            "class Keep(Base):\n"
            "    __tablename__ = 'keep'\n"
            "    id: Mapped[int] = mapped_column(primary_key=True)\n\n"
            "class AuditLog(Base):\n"
            "    __tablename__ = 'audit_log'\n"
            "    id: Mapped[int] = mapped_column(primary_key=True)\n"
        )
        out_file = tmp_path / "out.svg"
        monkeypatch.chdir(tmp_path)
        main(["filter_models:Base", "-f", "svg", "--exclude-tables", "audit_.*", "-o", str(out_file)])
        content = out_file.read_text()
        assert 'data-table="keep"' in content
        assert 'data-table="audit_log"' not in content

    def test_cli_layered_layout(self, tmp_path, monkeypatch):
        models_file = tmp_path / "models.py"
        models_file.write_text(
            "from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column\n"
            "from sqlalchemy import String, ForeignKey\n\n"
            "class Base(DeclarativeBase):\n"
            "    pass\n\n"
            "class Parent(Base):\n"
            "    __tablename__ = 'parent'\n"
            "    id: Mapped[int] = mapped_column(primary_key=True)\n\n"
            "class Child(Base):\n"
            "    __tablename__ = 'child'\n"
            "    id: Mapped[int] = mapped_column(primary_key=True)\n"
            "    parent_id: Mapped[int] = mapped_column(ForeignKey('parent.id'))\n"
        )
        out_file = tmp_path / "out.svg"
        monkeypatch.chdir(tmp_path)
        main(["models:Base", "-f", "svg", "--layout", "layered", "-o", str(out_file)])
        assert out_file.exists()
        assert "<svg" in out_file.read_text()

    def test_cli_star_layout(self, tmp_path, monkeypatch):
        models_file = tmp_path / "models.py"
        models_file.write_text(
            "from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column\n"
            "from sqlalchemy import String\n\n"
            "class Base(DeclarativeBase):\n"
            "    pass\n\n"
            "class Baz(Base):\n"
            "    __tablename__ = 'baz'\n"
            "    id: Mapped[int] = mapped_column(primary_key=True)\n"
        )
        out_file = tmp_path / "out.svg"
        monkeypatch.chdir(tmp_path)
        main(["models:Base", "-f", "svg", "--layout", "star", "-o", str(out_file)])
        assert out_file.exists()
        content = out_file.read_text()
        assert "<svg" in content

    def test_cli_star_cols(self, tmp_path, monkeypatch):
        models_file = tmp_path / "models.py"
        models_file.write_text(
            "from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column\n"
            "from sqlalchemy import String\n\n"
            "class Base(DeclarativeBase):\n"
            "    pass\n\n"
            "class Qux(Base):\n"
            "    __tablename__ = 'qux'\n"
            "    id: Mapped[int] = mapped_column(primary_key=True)\n"
        )
        out_file = tmp_path / "out.svg"
        monkeypatch.chdir(tmp_path)
        main(["models:Base", "-f", "svg", "--layout", "star", "--star-cols", "2", "-o", str(out_file)])
        assert out_file.exists()

    def test_cli_node_width_auto(self, tmp_path, monkeypatch):
        models_file = tmp_path / "models.py"
        models_file.write_text(
            "from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column\n"
            "from sqlalchemy import String\n\n"
            "class Base(DeclarativeBase):\n"
            "    pass\n\n"
            "class Wide(Base):\n"
            "    __tablename__ = 'wide'\n"
            "    id: Mapped[int] = mapped_column(primary_key=True)\n"
            "    name: Mapped[str] = mapped_column(String(50))\n"
        )
        out_file = tmp_path / "out.svg"
        monkeypatch.chdir(tmp_path)
        main(["models:Base", "-f", "svg", "--node-width", "auto", "-o", str(out_file)])
        assert out_file.exists()

    def test_cli_node_width_fixed(self, tmp_path, monkeypatch):
        models_file = tmp_path / "models.py"
        models_file.write_text(
            "from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column\n"
            "from sqlalchemy import String\n\n"
            "class Base(DeclarativeBase):\n"
            "    pass\n\n"
            "class Fixed(Base):\n"
            "    __tablename__ = 'fixed'\n"
            "    id: Mapped[int] = mapped_column(primary_key=True)\n"
        )
        out_file = tmp_path / "out.svg"
        monkeypatch.chdir(tmp_path)
        main(["models:Base", "-f", "svg", "--node-width", "350", "-o", str(out_file)])
        assert out_file.exists()
        content = out_file.read_text()
        assert 'width="350"' in content


# ── CLI error paths ──────────────────────────────────────────────────────────

class TestCliErrors:
    def test_resolve_target_missing_module_raises(self):
        with pytest.raises(ModuleNotFoundError):
            _resolve_target("this_module_does_not_exist:Base")

    def test_resolve_target_missing_attribute_raises(self, tmp_path, monkeypatch):
        models_file = tmp_path / "empty_models.py"
        models_file.write_text("X = 1\n")
        monkeypatch.chdir(tmp_path)
        with pytest.raises(AttributeError):
            _resolve_target("empty_models:Base")

    def test_resolve_target_no_base_or_metadata_exits(self, tmp_path, monkeypatch):
        models_file = tmp_path / "no_models.py"
        models_file.write_text("VALUE = 42\n")
        monkeypatch.chdir(tmp_path)
        with pytest.raises(SystemExit) as exc:
            _resolve_target("no_models")
        assert exc.value.code == 1

    def test_resolve_target_finds_metadata_without_attr(self, tmp_path, monkeypatch):
        models_file = tmp_path / "meta_models.py"
        models_file.write_text(
            "from sqlalchemy import MetaData, Table, Column, Integer\n"
            "md = MetaData()\n"
            "Table('t', md, Column('id', Integer, primary_key=True))\n"
        )
        monkeypatch.chdir(tmp_path)
        from sqlalchemy import MetaData
        assert isinstance(_resolve_target("meta_models"), MetaData)

    def test_cli_no_tables_exits(self, tmp_path, monkeypatch):
        models_file = tmp_path / "bare_models.py"
        models_file.write_text(
            "from sqlalchemy.orm import DeclarativeBase\n"
            "class Base(DeclarativeBase):\n"
            "    pass\n"
        )
        monkeypatch.chdir(tmp_path)
        with pytest.raises(SystemExit) as exc:
            main(["bare_models:Base", "-o", str(tmp_path / "out.html")])
        assert exc.value.code == 1
