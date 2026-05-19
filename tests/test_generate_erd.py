"""Tests for the public generate_erd API and CLI."""

from __future__ import annotations

import os
import pytest
from pathlib import Path

from sqlalchemy_erd import generate_erd
from sqlalchemy_erd.cli import main


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
