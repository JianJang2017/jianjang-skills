#!/usr/bin/env python3
"""Structural checks for the maintained crossover-blouse example bundle."""

import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "crossover-blouse-a"
SVG_NS = "{http://www.w3.org/2000/svg}"


class CurrentExampleTests(unittest.TestCase):
    def test_bundle_contains_the_six_documented_deliverables(self):
        expected = {
            "01-garment-look.png",
            "02-pattern-reference.svg",
            "03-assembly-guide.svg",
            "04-making-process.md",
            "05-specification.md",
            "README.md",
        }
        actual = {path.name for path in EXAMPLE.iterdir() if path.is_file()}
        self.assertEqual(actual, expected)

    def test_vector_outputs_are_valid_and_complete(self):
        pattern = ET.parse(EXAMPLE / "02-pattern-reference.svg").getroot()
        assembly = ET.parse(EXAMPLE / "03-assembly-guide.svg").getroot()
        cut_paths = pattern.findall(f".//{SVG_NS}path[@data-cut-method='true-offset']")
        cards = assembly.findall(f".//{SVG_NS}g[@data-piece-card]")
        self.assertEqual(len(cut_paths), 6)
        self.assertEqual(len(cards), 6)

    def test_raster_and_documents_are_nonempty(self):
        image = (EXAMPLE / "01-garment-look.png").read_bytes()
        self.assertTrue(image.startswith(b"\x89PNG\r\n\x1a\n"))
        for name in ("04-making-process.md", "05-specification.md", "README.md"):
            self.assertGreater(len((EXAMPLE / name).read_text(encoding="utf-8")), 200)


if __name__ == "__main__":
    unittest.main(verbosity=2)
