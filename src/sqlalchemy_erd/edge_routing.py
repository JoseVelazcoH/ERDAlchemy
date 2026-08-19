"""Orthogonal (Manhattan) edge routing with rounded corners.

Edges leave a card edge, travel through the empty gap between columns, and
enter the target edge using right-angle segments. This reads like a dbdiagram /
Graphviz ``dot`` connector and, with the layered layout, avoids cutting across
other cards. The same math is mirrored in the interactive JS renderer so that
dragging keeps the routing identical.
"""

from sqlalchemy_erd.constants.routing import CORNER_RADIUS, SAME_SIDE_STUB

Side = str
Point = tuple[float, float]


def _is_horizontal(side: Side) -> bool:
    return side in ("left", "right")


def _same_side_x(fs: Side, fx: float, tx: float) -> float:
    if fs == "right":
        return max(fx, tx) + SAME_SIDE_STUB
    return min(fx, tx) - SAME_SIDE_STUB


def _same_side_y(fs: Side, fy: float, ty: float) -> float:
    if fs == "bottom":
        return max(fy, ty) + SAME_SIDE_STUB
    return min(fy, ty) - SAME_SIDE_STUB


def orthogonal_waypoints(fp: Point, fs: Side, tp: Point, ts: Side) -> list[Point]:
    """Axis-aligned corner points from ``fp`` (side ``fs``) to ``tp`` (side ``ts``)."""
    fx, fy = fp
    tx, ty = tp
    points: list[Point] = [fp]

    if _is_horizontal(fs) and _is_horizontal(ts):
        bend_x = _same_side_x(fs, fx, tx) if fs == ts else (fx + tx) / 2
        points += [(bend_x, fy), (bend_x, ty)]
    elif not _is_horizontal(fs) and not _is_horizontal(ts):
        bend_y = _same_side_y(fs, fy, ty) if fs == ts else (fy + ty) / 2
        points += [(fx, bend_y), (tx, bend_y)]
    elif _is_horizontal(fs):
        points.append((tx, fy))  # exit horizontally, enter vertically
    else:
        points.append((fx, ty))  # exit vertically, enter horizontally

    points.append(tp)
    return _simplify(points)


def _simplify(points: list[Point]) -> list[Point]:
    """Drop consecutive duplicate and collinear points."""
    deduped: list[Point] = []
    for point in points:
        if not deduped or point != deduped[-1]:
            deduped.append(point)

    simplified: list[Point] = []
    for i, point in enumerate(deduped):
        if 0 < i < len(deduped) - 1:
            prev, nxt = deduped[i - 1], deduped[i + 1]
            on_horizontal = prev[1] == point[1] == nxt[1]
            on_vertical = prev[0] == point[0] == nxt[0]
            if on_horizontal or on_vertical:
                continue
        simplified.append(point)
    return simplified


def _point_towards(origin: Point, target: Point, distance: float) -> Point:
    ox, oy = origin
    tx, ty = target
    dx, dy = tx - ox, ty - oy
    length = (dx * dx + dy * dy) ** 0.5
    if length == 0:
        return origin
    step = min(distance, length / 2)
    return round(ox + dx / length * step, 1), round(oy + dy / length * step, 1)


def _fmt(point: Point) -> str:
    return f"{round(point[0], 1)} {round(point[1], 1)}"


def rounded_orthogonal_path(points: list[Point], radius: float = CORNER_RADIUS) -> str:
    """SVG path string for ``points`` with quadratic-rounded corners."""
    if len(points) < 2:
        return ""
    if len(points) == 2:
        return f"M {_fmt(points[0])} L {_fmt(points[1])}"

    segments = [f"M {_fmt(points[0])}"]
    for i in range(1, len(points) - 1):
        corner = points[i]
        entry = _point_towards(corner, points[i - 1], radius)
        exit_point = _point_towards(corner, points[i + 1], radius)
        segments.append(f"L {_fmt(entry)}")
        segments.append(f"Q {_fmt(corner)} {_fmt(exit_point)}")
    segments.append(f"L {_fmt(points[-1])}")
    return " ".join(segments)


def orthogonal_path(fp: Point, fs: Side, tp: Point, ts: Side) -> str:
    """Full SVG path for an orthogonal connector between two card edges."""
    return rounded_orthogonal_path(orthogonal_waypoints(fp, fs, tp, ts))
