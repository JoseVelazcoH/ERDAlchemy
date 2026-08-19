"""Tests for sqlalchemy_erd.edge_routing — orthogonal (Manhattan) edge paths."""

import pytest

from sqlalchemy_erd.edge_routing import orthogonal_path, orthogonal_waypoints


def _all_segments_axis_aligned(points) -> bool:
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        if x1 != x2 and y1 != y2:
            return False
    return True


class TestOrthogonalWaypoints:
    def test_right_to_left_bends_at_mid_x(self):
        points = orthogonal_waypoints((100, 50), "right", (300, 90), "left")
        assert points[0] == (100, 50)
        assert points[-1] == (300, 90)
        mid_x = (100 + 300) / 2
        assert any(p[0] == mid_x for p in points[1:-1])

    @pytest.mark.parametrize(
        "fp,fs,tp,ts",
        [
            ((100, 50), "right", (300, 90), "left"),
            ((300, 50), "left", (100, 90), "right"),
            ((100, 50), "right", (300, 50), "right"),
            ((100, 50), "left", (300, 90), "left"),
            ((100, 50), "right", (300, 200), "top"),
            ((100, 50), "bottom", (300, 200), "left"),
            ((100, 50), "bottom", (100, 300), "top"),
        ],
    )
    def test_segments_are_axis_aligned(self, fp, fs, tp, ts):
        points = orthogonal_waypoints(fp, fs, tp, ts)
        assert _all_segments_axis_aligned(points)

    def test_endpoints_are_preserved(self):
        points = orthogonal_waypoints((10, 20), "right", (200, 80), "left")
        assert points[0] == (10, 20)
        assert points[-1] == (200, 80)

    def test_same_right_side_routes_outside_both_cards(self):
        points = orthogonal_waypoints((100, 50), "right", (120, 90), "right")
        bend_x = points[1][0]
        assert bend_x > 120  # past the rightmost card edge, not between them


class TestOrthogonalPath:
    def test_starts_at_source_point(self):
        path = orthogonal_path((100, 50), "right", (300, 90), "left")
        assert path.startswith("M 100 50")

    def test_path_is_deterministic(self):
        a = orthogonal_path((100, 50), "right", (300, 90), "left")
        b = orthogonal_path((100, 50), "right", (300, 90), "left")
        assert a == b

    def test_uses_quadratic_rounded_corners(self):
        path = orthogonal_path((100, 50), "right", (300, 90), "left")
        assert "Q" in path  # corners are rounded with quadratic curves

    def test_degenerate_straight_line_has_no_corner(self):
        path = orthogonal_path((100, 50), "right", (300, 50), "left")
        assert path.startswith("M 100 50")
        assert "300" in path
