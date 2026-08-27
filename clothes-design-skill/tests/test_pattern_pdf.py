#!/usr/bin/env python3
"""Contract tests for the dependency-free physical-scale PDF output."""

import tempfile
import unittest
import subprocess
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from calculate_garment import SIZE_CHART  # noqa: E402
from pattern_drafting import draft_crossover_blouse  # noqa: E402
from pattern_pdf import MM_TO_PT, write_tiled_pdf  # noqa: E402


class PatternPdfTests(unittest.TestCase):
    def test_a4_tiles_have_physical_scale_overlap_and_calibration(self):
        pieces = draft_crossover_blouse(SIZE_CHART["tops"]["M"], fit="regular")
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "sample.pdf"
            manifest = write_tiled_pdf(pieces, output, size="M")
            raw = output.read_bytes()

        self.assertTrue(raw.startswith(b"%PDF-1.4"))
        self.assertIn(b"/MediaBox [0 0 595.2756 841.8898]", raw)
        self.assertIn(b"% tile-overlap-mm: 10.0", raw)
        self.assertIn(b"% calibration-square-mm: 50.0", raw)
        self.assertIn(b"PRINT AT 100% / ACTUAL SIZE", raw)
        self.assertIn(b"MUSLIN SAMPLE ONLY", raw)
        for mark in (b"NOTCH A", b"NOTCH B", b"NOTCH N1", b"NOTCH N2"):
            self.assertIn(mark, raw)
        self.assertGreater(manifest.page_count, 1)
        self.assertLessEqual(manifest.page_count, 33, manifest.sheet_size_cm)
        self.assertAlmostEqual(manifest.calibration_points, 50 * MM_TO_PT, places=4)
        self.assertAlmostEqual(manifest.overlap_mm, 10.0, places=4)
        self.assertNotIn("A4", manifest.tile_ids, "known empty grid cell must not be emitted")
        self.assertEqual(manifest.page_count, len(manifest.tile_ids) + 1)

    def test_every_tile_has_a_coordinate_label(self):
        pieces = draft_crossover_blouse(SIZE_CHART["tops"]["M"], fit="regular")
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "sample.pdf"
            manifest = write_tiled_pdf(pieces, output, size="M")
            raw = output.read_bytes()
        for tile in manifest.tile_ids:
            self.assertIn(f"TILE {tile}".encode("ascii"), raw)

    def test_draw_pattern_cli_can_emit_pdf_without_svg(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "sample.pdf"
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "draw_pattern.py"),
                 "--type", "crossover-blouse", "--size", "M",
                 "--fit", "regular", "--pdf", str(output)],
                cwd=ROOT, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(output.exists())
            self.assertTrue(output.read_bytes().startswith(b"%PDF-1.4"))

    def test_only_the_documented_a4_tiling_contract_is_accepted(self):
        pieces = draft_crossover_blouse(SIZE_CHART["tops"]["M"], fit="regular")
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "sample.pdf"
            with self.assertRaisesRegex(ValueError, "10 mm"):
                write_tiled_pdf(pieces, output, size="M", overlap_mm=20)
            with self.assertRaisesRegex(ValueError, "A4"):
                write_tiled_pdf(pieces, output, size="M", paper="Letter")


if __name__ == "__main__":
    unittest.main()
