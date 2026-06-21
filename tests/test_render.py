"""Tests for sqlalchemy_erd.render — the output-format renderer registry."""

import pytest

from sqlalchemy_erd.force import force_directed_layout
from sqlalchemy_erd.introspect import introspect_models
from sqlalchemy_erd.render import RENDERERS, RenderRequest, render
from sqlalchemy_erd.theme import get_theme


def _request(base, **overrides):
    tables, rels = introspect_models(base)
    positions = force_directed_layout(tables, rels)
    return RenderRequest(
        tables=tables, relationships=rels, positions=positions,
        theme=get_theme("default"), **overrides,
    )


class TestRendererRegistry:
    def test_registry_lists_supported_formats(self):
        assert set(RENDERERS) == {"svg", "html", "png", "pdf"}

    def test_svg_renders_text_with_xml_header(self, blog_base):
        result = render("svg", _request(blog_base))
        assert isinstance(result, str)
        assert result.startswith("<?xml")

    def test_html_renders_text_document(self, blog_base):
        result = render("html", _request(blog_base))
        assert isinstance(result, str)
        assert "<!DOCTYPE html>" in result

    def test_html_uses_request_title(self, blog_base):
        result = render("html", _request(blog_base, title="My Schema"))
        assert "<title>My Schema</title>" in result

    def test_png_renders_bytes_with_png_signature(self, blog_base):
        result = render("png", _request(blog_base))
        assert isinstance(result, bytes)
        assert result[:8] == b"\x89PNG\r\n\x1a\n"

    def test_pdf_renders_bytes_with_pdf_signature(self, blog_base):
        result = render("pdf", _request(blog_base))
        assert isinstance(result, bytes)
        assert result[:5] == b"%PDF-"

    def test_unknown_format_raises_value_error(self, blog_base):
        with pytest.raises(ValueError, match="Unknown format"):
            render("bogus", _request(blog_base))


class TestRenderRequest:
    def test_defaults(self, blog_base):
        request = _request(blog_base)
        assert request.title == "ERD"
        assert request.scale == 2
