#!/usr/bin/env python3
"""Geometry gates for patterns that claim to support full-size sampling."""

import sys
import unittest
import xml.etree.ElementTree as ET
import subprocess
import tempfile
import copy
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from calculate_garment import SIZE_CHART  # noqa: E402
from pattern_drafting import EASE, Piece, draft_crossover_blouse  # noqa: E402
from pattern_geometry import (  # noqa: E402
    build_cut_outline,
    cut_notch_geometry,
    flatten_path,
    horizontal_spans_at_y,
    self_intersections,
    signed_area,
    validate_sample_pattern,
    point_on_path_segment,
)
from pattern_assembly import render_assembly  # noqa: E402


class CrossoverFrontGeometryTests(unittest.TestCase):
    def setUp(self):
        self.measurements = SIZE_CHART["tops"]["M"]
        self.big, self.small = draft_crossover_blouse(
            self.measurements, fit="regular"
        )[:2]
        self.quarter = (
            self.measurements["bust"] + EASE["regular"]["bust"]
        ) / 4
        self.overlap = self.measurements["bust"] / 12

    def test_big_front_keeps_body_width_at_hem(self):
        """Moving only the bbox edge must not leave a ribbon-width lower body."""
        spans = horizontal_spans_at_y(flatten_path(self.big.path), self.measurements["length"])
        self.assertEqual(len(spans), 1)
        self.assertAlmostEqual(spans[0][1] - spans[0][0], self.quarter + self.overlap, places=2)

    def test_small_front_keeps_quarter_bust_width_at_hem(self):
        spans = horizontal_spans_at_y(flatten_path(self.small.path), self.measurements["length"])
        self.assertEqual(len(spans), 1)
        self.assertAlmostEqual(spans[0][1] - spans[0][0], self.quarter, places=2)

    def test_fronts_are_simple_positive_closed_polygons(self):
        for piece in (self.big, self.small):
            with self.subTest(piece=piece.name):
                points = flatten_path(piece.path)
                self.assertEqual(points[0], points[-1])
                self.assertGreater(abs(signed_area(points)), 100.0)
                self.assertEqual(self_intersections(points), [])

    def test_collar_matches_the_actual_three_neckline_edges(self):
        pieces = draft_crossover_blouse(self.measurements, fit="regular")
        problems = validate_sample_pattern(pieces)
        self.assertFalse([p for p in problems if "领子" in p], problems)
        # M/regular: big front + two mirrored back-neck halves + small front.
        self.assertAlmostEqual(pieces[4].net_size()[0], 58.4, places=1)

    def test_validator_rejects_each_broken_seam_relationship(self):
        mutations = []

        shoulder = draft_crossover_blouse(self.measurements, fit="regular")
        shoulder[2].path[2] = ("L", shoulder[2].path[2][1] + 2.0, shoulder[2].path[2][2])
        mutations.append(("肩缝", shoulder))

        side = draft_crossover_blouse(self.measurements, fit="regular")
        side[2].path[4] = ("L", side[2].path[4][1], side[2].path[4][2] + 3.0)
        mutations.append(("侧缝", side))

        sleeve = draft_crossover_blouse(self.measurements, fit="regular")
        q = sleeve[3].path[1]
        sleeve[3].path[1] = ("Q", q[1], q[2], q[3] + 2.0, q[4])
        mutations.append(("袖山", sleeve))

        for expected, pieces in mutations:
            with self.subTest(expected=expected):
                problems = validate_sample_pattern(pieces)
                self.assertTrue(any(expected in p for p in problems), problems)

    def test_validator_rejects_unpaired_notch_label(self):
        pieces = draft_crossover_blouse(self.measurements, fit="regular")
        pieces[4].notches[0].label = "WRONG"
        problems = validate_sample_pattern(pieces)
        self.assertTrue(any("刀口" in p for p in problems), problems)

    def test_neckline_marks_follow_full_unfolded_sewing_sequence(self):
        pieces = draft_crossover_blouse(self.measurements, fit="regular")
        back, collar = pieces[2], pieces[4]
        back_marks = {n.label: n.fraction for n in back.notches}
        collar_marks = {n.label: n.fraction for n in collar.notches}
        self.assertEqual(back_marks["CB"], 0.0)
        self.assertEqual(back_marks["N1/N2"], 1.0)
        self.assertLess(collar_marks["N1"], collar_marks["CB"])
        self.assertLess(collar_marks["CB"], collar_marks["N2"])
        self.assertAlmostEqual(
            collar_marks["CB"] - collar_marks["N1"],
            collar_marks["N2"] - collar_marks["CB"],
            places=5,
        )


class CuttingOutlineTests(unittest.TestCase):
    def test_one_centimetre_allowance_is_a_measurable_parallel_offset(self):
        piece = Piece(
            name="test", name_en="test", qty=1,
            path=[("M", 0, 0), ("L", 10, 0), ("L", 10, 20),
                  ("L", 0, 20), ("Z",)],
            path_allowances=[1.0, 1.0, 1.0, 1.0],
        )
        cut = build_cut_outline(piece)
        xs, ys = [p[0] for p in cut], [p[1] for p in cut]
        self.assertAlmostEqual(min(xs), -1.0, places=4)
        self.assertAlmostEqual(max(xs), 11.0, places=4)
        self.assertAlmostEqual(min(ys), -1.0, places=4)
        self.assertAlmostEqual(max(ys), 21.0, places=4)

    def test_fold_edge_receives_zero_allowance(self):
        piece = Piece(
            name="fold", name_en="fold", qty=1, fold_edge="left",
            path=[("M", 0, 0), ("L", 10, 0), ("L", 10, 20),
                  ("L", 0, 20), ("Z",)],
            path_allowances=[1.0, 1.0, 1.0, 0.0],
        )
        cut = build_cut_outline(piece)
        self.assertAlmostEqual(min(p[0] for p in cut), 0.0, places=4)
        self.assertEqual(self_intersections(cut), [])

    def test_notch_apex_is_on_cut_line_not_net_line(self):
        piece = Piece(
            name="notch", name_en="notch", qty=1,
            path=[("M", 0, 0), ("L", 10, 0), ("L", 10, 20),
                  ("L", 0, 20), ("Z",)],
            path_allowances=[1.0, 1.0, 1.0, 1.0],
        )
        from pattern_drafting import Notch
        notch = Notch(1, 0.5, "A")
        apex, arm1, arm2 = cut_notch_geometry(piece, notch)
        net = point_on_path_segment(piece, 1, 0.5)
        self.assertAlmostEqual(math.dist(apex, net), 1.0, places=4)
        self.assertLess(math.dist(arm1, net), math.dist(apex, net))
        self.assertLess(math.dist(arm2, net), math.dist(apex, net))

    def test_every_real_notch_apex_lies_on_its_cut_outline(self):
        pieces = draft_crossover_blouse(SIZE_CHART["tops"]["M"], fit="regular")

        def point_segment_distance(p, a, b):
            dx, dy = b[0] - a[0], b[1] - a[1]
            if dx == dy == 0:
                return math.dist(p, a)
            t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy)
                                  / (dx * dx + dy * dy)))
            return math.dist(p, (a[0] + t * dx, a[1] + t * dy))

        for piece in pieces:
            cut = build_cut_outline(piece)
            for notch in piece.notches:
                with self.subTest(piece=piece.name, notch=notch.label):
                    apex, _, _ = cut_notch_geometry(piece, notch)
                    distance = min(point_segment_distance(apex, a, b)
                                   for a, b in zip(cut, cut[1:]))
                    self.assertLess(distance, 1e-5)


class AssemblyGuideTests(unittest.TestCase):
    def test_assembly_guide_uses_every_canonical_piece_outline(self):
        pieces = draft_crossover_blouse(SIZE_CHART["tops"]["M"], fit="regular")
        svg = render_assembly(pieces, size="M")
        root = ET.fromstring(svg)
        outlines = root.findall(".//{http://www.w3.org/2000/svg}path[@data-piece]")
        self.assertEqual(len(outlines), len(pieces))
        self.assertEqual(
            {node.attrib["data-piece"] for node in outlines},
            {piece.name_en for piece in pieces},
        )
        self.assertIn("Canonical geometry", svg)

    def test_assembly_labels_have_explicit_non_overlapping_boxes(self):
        pieces = draft_crossover_blouse(SIZE_CHART["tops"]["M"], fit="regular")
        root = ET.fromstring(render_assembly(pieces, size="M"))
        labels = root.findall(".//{http://www.w3.org/2000/svg}text[@data-piece-label]")
        self.assertEqual(len(labels), len(pieces))
        rows = {}
        for node in labels:
            rows.setdefault(float(node.attrib["data-box-y"]), []).append(
                (float(node.attrib["data-box-x"]),
                 float(node.attrib["data-box-x"]) + float(node.attrib["data-box-width"]))
            )
        for boxes in rows.values():
            boxes.sort()
            for (_, right), (left, _) in zip(boxes, boxes[1:]):
                self.assertLessEqual(right, left)
        self.assertTrue(all("transform" not in node.attrib for node in labels))

    def test_each_assembly_piece_has_an_isolated_label_card(self):
        pieces = draft_crossover_blouse(SIZE_CHART["tops"]["M"], fit="regular")
        root = ET.fromstring(render_assembly(pieces, size="M"))
        ns = "{http://www.w3.org/2000/svg}"
        cards = root.findall(f".//{ns}g[@data-piece-card]")
        self.assertEqual(len(cards), len(pieces))
        boxes = []
        for card in cards:
            x = float(card.attrib["data-card-x"])
            y = float(card.attrib["data-card-y"])
            w = float(card.attrib["data-card-width"])
            h = float(card.attrib["data-card-height"])
            boxes.append((x, y, x + w, y + h))
            labels = card.findall(f"{ns}text[@data-piece-label]")
            self.assertEqual(len(labels), 1)
            self.assertEqual(len(labels[0].findall(f"{ns}tspan")), 2)
            self.assertLessEqual(float(labels[0].attrib["data-max-width"]), w - 24)
        for index, a in enumerate(boxes):
            for b in boxes[index + 1:]:
                separated = a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1]
                self.assertTrue(separated, (a, b))

    def test_assembly_copy_does_not_refer_to_removed_pdf_workflow(self):
        pieces = draft_crossover_blouse(SIZE_CHART["tops"]["M"], fit="regular")
        svg = render_assembly(pieces, size="M")
        self.assertNotIn("PDF", svg)
        self.assertNotIn("tiled", svg.lower())
        self.assertIn("not a cutting pattern", svg.lower())

    def test_assembly_title_is_bilingual(self):
        pieces = draft_crossover_blouse(SIZE_CHART["tops"]["M"], fit="regular")
        root = ET.fromstring(render_assembly(pieces, size="M"))
        ns = "{http://www.w3.org/2000/svg}"
        title = root.find(f"{ns}text[@data-document-title]")
        self.assertIsNotNone(title)
        copy = "".join(title.itertext())
        self.assertIn("交领上衣裁片拼装示意", copy)
        self.assertIn("Crossover Blouse Assembly Guide", copy)
        self.assertIn("M码 / Size M", copy)

    def test_technical_svg_uses_measurable_cut_outline(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "pattern.svg"
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "draw_pattern.py"),
                 "--type", "crossover-blouse", "--size", "M",
                 "--output", str(output)],
                cwd=ROOT, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            root = ET.parse(output).getroot()
            paths = root.findall(
                ".//{http://www.w3.org/2000/svg}path[@data-cut-method='true-offset']"
            )
            self.assertEqual(len(paths), 6)


if __name__ == "__main__":
    unittest.main()
