#!/usr/bin/env python3
"""Dependency-free geometry utilities for full-size pattern validation."""

from __future__ import annotations

from math import ceil, hypot
from typing import Iterable, List, Sequence, Tuple

Point = Tuple[float, float]


def _quad_point(p0: Point, p1: Point, p2: Point, t: float) -> Point:
    u = 1.0 - t
    return (
        u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
        u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1],
    )


def flatten_path(path: Sequence[Tuple], tolerance_cm: float = 0.05) -> List[Point]:
    """Convert M/L/Q/Z pattern commands into a closed polyline in centimetres."""
    points: List[Point] = []
    current: Point | None = None
    start: Point | None = None
    for seg in path:
        if seg[0] == "M":
            current = (float(seg[1]), float(seg[2]))
            start = current
            points.append(current)
        elif seg[0] == "L":
            current = (float(seg[1]), float(seg[2]))
            points.append(current)
        elif seg[0] == "Q":
            if current is None:
                raise ValueError("Q command before M")
            control = (float(seg[1]), float(seg[2]))
            end = (float(seg[3]), float(seg[4]))
            chord = ((end[0] - current[0]) ** 2 + (end[1] - current[1]) ** 2) ** 0.5
            control_run = (((control[0] - current[0]) ** 2 + (control[1] - current[1]) ** 2) ** 0.5
                           + ((end[0] - control[0]) ** 2 + (end[1] - control[1]) ** 2) ** 0.5)
            steps = max(4, ceil(max(chord, control_run) / max(tolerance_cm * 8, 0.2)))
            p0 = current
            points.extend(_quad_point(p0, control, end, i / steps) for i in range(1, steps + 1))
            current = end
        elif seg[0] == "Z":
            if start is not None and points[-1] != start:
                points.append(start)
            current = start
        else:
            raise ValueError(f"unsupported path command: {seg[0]}")
    return points


def signed_area(points: Sequence[Point]) -> float:
    return 0.5 * sum(
        a[0] * b[1] - b[0] * a[1] for a, b in zip(points, points[1:])
    )


def _orientation(a: Point, b: Point, c: Point) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _strict_cross(a: Point, b: Point, c: Point, d: Point) -> bool:
    return (_orientation(a, b, c) * _orientation(a, b, d) < -1e-9
            and _orientation(c, d, a) * _orientation(c, d, b) < -1e-9)


def self_intersections(points: Sequence[Point]) -> List[Tuple[int, int]]:
    """Return indexes of non-adjacent polyline segments that strictly cross."""
    count = len(points) - 1
    hits: List[Tuple[int, int]] = []
    for i in range(count):
        for j in range(i + 1, count):
            if j == i + 1 or (i == 0 and j == count - 1):
                continue
            if _strict_cross(points[i], points[i + 1], points[j], points[j + 1]):
                hits.append((i, j))
    return hits


def horizontal_spans_at_y(points: Sequence[Point], y: float, eps: float = 1e-6) -> List[Point]:
    """Return merged x-spans formed by horizontal boundary segments at ``y``."""
    spans = []
    for a, b in zip(points, points[1:]):
        if abs(a[1] - y) <= eps and abs(b[1] - y) <= eps and abs(a[0] - b[0]) > eps:
            spans.append((min(a[0], b[0]), max(a[0], b[0])))
    spans.sort()
    merged: List[List[float]] = []
    for lo, hi in spans:
        if not merged or lo > merged[-1][1] + eps:
            merged.append([lo, hi])
        else:
            merged[-1][1] = max(merged[-1][1], hi)
    return [(lo, hi) for lo, hi in merged]


def _flatten_piece_edges(piece, tolerance_cm: float) -> Tuple[List[Point], List[float]]:
    """Flatten a Piece while retaining the allowance belonging to each edge."""
    expected = sum(1 for seg in piece.path if seg[0] in ("L", "Q", "Z"))
    if len(piece.path_allowances) != expected:
        raise ValueError(
            f"{piece.name}: {expected} boundary edges but "
            f"{len(piece.path_allowances)} path allowances"
        )
    points: List[Point] = []
    allowances: List[float] = []
    current = start = None
    allowance_index = 0
    for seg in piece.path:
        if seg[0] == "M":
            current = start = (float(seg[1]), float(seg[2]))
            points.append(current)
            continue
        allowance = float(piece.path_allowances[allowance_index])
        allowance_index += 1
        if seg[0] == "L":
            current = (float(seg[1]), float(seg[2]))
            points.append(current)
            allowances.append(allowance)
        elif seg[0] == "Q":
            control = (float(seg[1]), float(seg[2]))
            end = (float(seg[3]), float(seg[4]))
            chord = hypot(end[0] - current[0], end[1] - current[1])
            run = hypot(control[0] - current[0], control[1] - current[1]) + hypot(
                end[0] - control[0], end[1] - control[1]
            )
            steps = max(4, ceil(max(chord, run) / max(tolerance_cm * 8, 0.2)))
            p0 = current
            for i in range(1, steps + 1):
                points.append(_quad_point(p0, control, end, i / steps))
                allowances.append(allowance)
            current = end
        elif seg[0] == "Z":
            if points[-1] != start:
                points.append(start)
                allowances.append(allowance)
            current = start
    return points, allowances


def _line_intersection(p: Point, r: Point, q: Point, s: Point) -> Point | None:
    cross = r[0] * s[1] - r[1] * s[0]
    if abs(cross) < 1e-10:
        return None
    qp = (q[0] - p[0], q[1] - p[1])
    t = (qp[0] * s[1] - qp[1] * s[0]) / cross
    return p[0] + t * r[0], p[1] + t * r[1]


def build_cut_outline(piece, tolerance_cm: float = 0.05) -> List[Point]:
    """Build a measurable outside cutting line from explicit per-edge SA."""
    points, allowances = _flatten_piece_edges(piece, tolerance_cm)
    vertices = points[:-1]
    clockwise_screen = signed_area(points) > 0
    offset_lines = []
    for i, (a, b) in enumerate(zip(points, points[1:])):
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = hypot(dx, dy)
        if length < 1e-9:
            raise ValueError(f"{piece.name}: zero-length boundary edge")
        if clockwise_screen:
            nx, ny = dy / length, -dx / length
        else:
            nx, ny = -dy / length, dx / length
        sa = allowances[i]
        offset_lines.append(((a[0] + nx * sa, a[1] + ny * sa), (dx, dy), sa, (nx, ny)))

    cut: List[Point] = []
    for i, vertex in enumerate(vertices):
        prev = offset_lines[i - 1]
        curr = offset_lines[i]
        hit = _line_intersection(prev[0], prev[1], curr[0], curr[1])
        limit = max(prev[2], curr[2], 0.1) * 6.0
        if hit is None or hypot(hit[0] - vertex[0], hit[1] - vertex[1]) > limit:
            # Near-parallel curve facets need a bounded join, not a long spike.
            nx = prev[3][0] * prev[2] + curr[3][0] * curr[2]
            ny = prev[3][1] * prev[2] + curr[3][1] * curr[2]
            hit = vertex[0] + nx / 2, vertex[1] + ny / 2
        cut.append(hit)
    cut.append(cut[0])
    return cut


def _first_edge_length(piece) -> float:
    points = flatten_path(piece.path)
    # The first drafted edge is always unflattened for the two fronts; the
    # back neckline is a Q and is already available as an exact arc callout.
    first = piece.path[1]
    if first[0] == "L":
        return hypot(first[1] - points[0][0], first[2] - points[0][1])
    return next((a.length for a in piece.arcs if a.seg_index == 1), 0.0)


def validate_sample_pattern(pieces: Sequence) -> List[str]:
    """Reject topology and seam-match defects that make a muslin unsewable."""
    problems: List[str] = []
    for piece in pieces:
        net = flatten_path(piece.path)
        if len(net) < 4 or net[0] != net[-1] or abs(signed_area(net)) < 1.0:
            problems.append(f"{piece.name}: 净样不是有效闭合裁片")
        if self_intersections(net):
            problems.append(f"{piece.name}: 净样轮廓自交")
        if piece.path_allowances:
            try:
                cut = build_cut_outline(piece)
                if self_intersections(cut) or abs(signed_area(cut)) <= abs(signed_area(net)):
                    problems.append(f"{piece.name}: 毛样轮廓无效")
            except ValueError as exc:
                problems.append(str(exc))

    by_name = {p.name: p for p in pieces}
    required = ("前襟左片(大襟)", "前襟右片(小襟)", "后片", "袖子", "领子")
    if all(name in by_name for name in required):
        big, small, back, sleeve, collar = (by_name[name] for name in required)
        neckline = (_first_edge_length(big) + 2 * _first_edge_length(back)
                    + _first_edge_length(small))
        collar_len = collar.net_size()[0]
        collar_exact = path_segment_length(collar, 1)
        if abs(collar_exact - neckline) > 0.15:
            problems.append(
                f"领子: 长 {collar_len:.1f}cm 与实测领口 {neckline:.1f}cm 不匹配"
            )

        shoulder_lengths = [path_segment_length(piece, 2) for piece in (big, small, back)]
        if max(shoulder_lengths) - min(shoulder_lengths) > 0.15:
            problems.append(f"肩缝不匹配: {', '.join(f'{n:.2f}' for n in shoulder_lengths)}cm")

        side_lengths = [path_segment_length(piece, 4) for piece in (big, small, back)]
        if max(side_lengths) - min(side_lengths) > 0.15:
            problems.append(f"侧缝不匹配: {', '.join(f'{n:.2f}' for n in side_lengths)}cm")

        front_armhole = path_segment_length(big, 3)
        back_armhole = path_segment_length(back, 3)
        front_cap = path_segment_length(sleeve, 1)
        back_cap = path_segment_length(sleeve, 2)
        # This wide sleeve intentionally carries exactly 1 cm ease in each half.
        if abs((front_cap - front_armhole) - 1.0) > 0.15:
            problems.append(
                f"袖山前弧不匹配: 袖山 {front_cap:.2f}cm / 袖窿 {front_armhole:.2f}cm"
            )
        if abs((back_cap - back_armhole) - 1.0) > 0.15:
            problems.append(
                f"袖山后弧不匹配: 袖山 {back_cap:.2f}cm / 袖窿 {back_armhole:.2f}cm"
            )

        expected_notches = {
            "A": {big.name, small.name, sleeve.name},
            "B": {back.name, sleeve.name},
            "N1": {big.name, collar.name},
            "N2": {small.name, collar.name},
            "CB": {back.name, collar.name},
            "N1/N2": {back.name},
        }
        actual_notches = {}
        for piece in (big, small, back, sleeve, collar):
            for notch in piece.notches:
                actual_notches.setdefault(notch.label, set()).add(piece.name)
        for label, expected in expected_notches.items():
            if actual_notches.get(label, set()) != expected:
                problems.append(
                    f"刀口 {label} 配对错误: "
                    f"{sorted(actual_notches.get(label, set()))}，应为 {sorted(expected)}"
                )

        notch_map = lambda piece: {n.label: n.fraction for n in piece.notches}
        big_marks, small_marks = notch_map(big), notch_map(small)
        back_marks, collar_marks = notch_map(back), notch_map(collar)
        positional_ok = (
            abs(big_marks.get("N1", -1) - 1.0) < 1e-9
            and abs(small_marks.get("N2", -1) - 1.0) < 1e-9
            and abs(back_marks.get("CB", -1) - 0.0) < 1e-9
            and abs(back_marks.get("N1/N2", -1) - 1.0) < 1e-9
            and abs(collar_marks.get("N1", -1) - _first_edge_length(big) / collar_exact) < 1e-6
            and abs(collar_marks.get("CB", -1)
                    - (_first_edge_length(big) + _first_edge_length(back)) / collar_exact) < 1e-6
            and abs(collar_marks.get("N2", -1)
                    - (_first_edge_length(big) + 2 * _first_edge_length(back)) / collar_exact) < 1e-6
        )
        if not positional_ok:
            problems.append("领口刀口位置与 N1 → CB → N2 累计缝长不一致")
    return problems


def point_on_path_segment(piece, seg_index: int, fraction: float) -> Point:
    """Evaluate a point on an original L/Q boundary command."""
    if not 0.0 <= fraction <= 1.0:
        raise ValueError("notch fraction must be between 0 and 1")
    current = None
    for index, seg in enumerate(piece.path):
        if seg[0] == "M":
            current = (float(seg[1]), float(seg[2]))
        elif seg[0] == "L":
            end = (float(seg[1]), float(seg[2]))
            if index == seg_index:
                return (current[0] + (end[0] - current[0]) * fraction,
                        current[1] + (end[1] - current[1]) * fraction)
            current = end
        elif seg[0] == "Q":
            control = (float(seg[1]), float(seg[2]))
            end = (float(seg[3]), float(seg[4]))
            if index == seg_index:
                return _quad_point(current, control, end, fraction)
            current = end
    raise ValueError(f"{piece.name}: notch references unsupported segment {seg_index}")


def _segment_start(piece, seg_index: int) -> Point:
    current = None
    for index, seg in enumerate(piece.path):
        if seg[0] == "M":
            current = (float(seg[1]), float(seg[2]))
        elif index == seg_index:
            return current
        elif seg[0] == "L":
            current = (float(seg[1]), float(seg[2]))
        elif seg[0] == "Q":
            current = (float(seg[3]), float(seg[4]))
    raise ValueError(f"{piece.name}: segment {seg_index} not found")


def path_segment_length(piece, seg_index: int) -> float:
    """Measure one original L/Q seam command in centimetres."""
    seg = piece.path[seg_index]
    start = _segment_start(piece, seg_index)
    if seg[0] == "L":
        return hypot(seg[1] - start[0], seg[2] - start[1])
    if seg[0] == "Q":
        control = (float(seg[1]), float(seg[2]))
        end = (float(seg[3]), float(seg[4]))
        points = [start] + [_quad_point(start, control, end, i / 128) for i in range(1, 129)]
        return sum(hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(points, points[1:]))
    raise ValueError(f"{piece.name}: segment {seg_index} is not a measurable seam")


def _allowance_for_segment(piece, seg_index: int) -> float:
    boundary_index = -1
    for index, seg in enumerate(piece.path):
        if seg[0] in ("L", "Q", "Z"):
            boundary_index += 1
        if index == seg_index:
            return float(piece.path_allowances[boundary_index])
    raise ValueError(f"{piece.name}: no allowance for segment {seg_index}")


def cut_notch_geometry(piece, notch) -> Tuple[Point, Point, Point]:
    """Return cut-line apex and two inward V arms for a matching notch."""
    seg = piece.path[notch.seg_index]
    start = _segment_start(piece, notch.seg_index)
    t = notch.fraction
    net = point_on_path_segment(piece, notch.seg_index, t)
    if seg[0] == "L":
        tangent = (seg[1] - start[0], seg[2] - start[1])
    elif seg[0] == "Q":
        control = (float(seg[1]), float(seg[2]))
        end = (float(seg[3]), float(seg[4]))
        tangent = (2 * (1 - t) * (control[0] - start[0]) + 2 * t * (end[0] - control[0]),
                   2 * (1 - t) * (control[1] - start[1]) + 2 * t * (end[1] - control[1]))
    else:
        raise ValueError(f"{piece.name}: notch must reference L or Q")
    length = hypot(*tangent)
    tx, ty = tangent[0] / length, tangent[1] / length
    if signed_area(flatten_path(piece.path)) > 0:
        nx, ny = ty, -tx
    else:
        nx, ny = -ty, tx
    sa = _allowance_for_segment(piece, notch.seg_index)
    estimated = net[0] + nx * sa, net[1] + ny * sa
    # Curves are flattened for the actual cutting outline and corners are
    # mitered from two adjacent offsets. Project onto that rendered polyline so
    # the V apex is guaranteed to cut the red line, including endpoint marks.
    best = None
    best_distance = float("inf")
    cut = build_cut_outline(piece)
    for a, b in zip(cut, cut[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        denom = dx * dx + dy * dy
        u = 0.0 if denom < 1e-12 else max(
            0.0, min(1.0, ((estimated[0] - a[0]) * dx + (estimated[1] - a[1]) * dy) / denom)
        )
        candidate = a[0] + u * dx, a[1] + u * dy
        distance = hypot(candidate[0] - estimated[0], candidate[1] - estimated[1])
        if distance < best_distance:
            best, best_distance = candidate, distance
    apex = best
    depth, half_width = min(0.35, max(sa * 0.6, 0.18)), 0.18
    inward = net[0] - apex[0], net[1] - apex[1]
    inward_length = hypot(*inward)
    ix, iy = ((-nx, -ny) if inward_length < 1e-9
              else (inward[0] / inward_length, inward[1] / inward_length))
    base = apex[0] + ix * depth, apex[1] + iy * depth
    return (apex,
            (base[0] + tx * half_width, base[1] + ty * half_width),
            (base[0] - tx * half_width, base[1] - ty * half_width))
