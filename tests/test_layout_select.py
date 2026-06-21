"""Tests for sqlalchemy_erd.layout_select — the layout strategy registry."""

import pytest

from sqlalchemy_erd.introspect import introspect_models
from sqlalchemy_erd.layout_select import LAYOUTS, LayoutRequest, select_layout


@pytest.mark.parametrize("layout", ["layered", "star", "force"])
def test_select_layout_known_name_positions_all_tables(blog_base, layout):
    tables, rels = introspect_models(blog_base)
    request = LayoutRequest(tables=tables, relationships=rels)
    positions = select_layout(layout, request)
    assert set(positions) == {t.name for t in tables}


def test_select_layout_unknown_name_raises():
    request = LayoutRequest(tables=[], relationships=[])
    with pytest.raises(ValueError, match="Unknown layout"):
        select_layout("bogus", request)


def test_registry_lists_available_layouts():
    assert set(LAYOUTS) == {"layered", "star", "force"}
