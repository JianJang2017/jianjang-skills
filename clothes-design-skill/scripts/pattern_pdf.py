#!/usr/bin/env python3
"""Native vector PDF exporter for tiled, true-scale sample patterns."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from pathlib import Path
from typing import List, Sequence, Tuple

from pattern_geometry import (build_cut_outline, cut_notch_geometry, flatten_path,
                              validate_sample_pattern)

MM_TO_PT = 72.0 / 25.4
CM_TO_PT = MM_TO_PT * 10.0
A4_WIDTH_PT = 210.0 * MM_TO_PT
A4_HEIGHT_PT = 297.0 * MM_TO_PT


@dataclass(frozen=True)
class PdfManifest:
    page_count: int
    tile_ids: Tuple[str, ...]
    overlap_mm: float
    calibration_points: float
    sheet_size_cm: Tuple[float, float]


@dataclass
class _PlacedPiece:
    piece: object
    net: List[Tuple[float, float]]
    cut: List[Tuple[float, float]]
    x: float
    y: float
    notches: List[Tuple[Tuple[float, float], str]]


def _rotate_if_long(points, rotate):
    if not rotate:
        return list(points)
    return [(y, -x) for x, y in points]


def _normalize(points):
    x0 = min(x for x, _ in points)
    y0 = min(y for _, y in points)
    return [(x - x0, y - y0) for x, y in points]


def _layout(pieces: Sequence, max_width_cm: float = 72.0):
    prepared = []
    for piece in pieces:
        net0 = flatten_path(piece.path)
        cut0 = build_cut_outline(piece)
        width = max(px for px, _ in cut0) - min(px for px, _ in cut0)
        rotate = width > max_width_cm
        net = _normalize(_rotate_if_long(net0, rotate))
        cut = _normalize(_rotate_if_long(cut0, rotate))
        # Normalise from the same cut origin so seam and cutting lines coincide.
        cut_x0 = min(px for px, _ in _rotate_if_long(cut0, rotate))
        cut_y0 = min(py for _, py in _rotate_if_long(cut0, rotate))
        net = [(px - cut_x0, py - cut_y0) for px, py in _rotate_if_long(net0, rotate)]
        w = max(px for px, _ in cut) + 1.0
        h = max(py for _, py in cut) + 2.0
        notch_points = []
        for notch in piece.notches:
            geometry = cut_notch_geometry(piece, notch)
            transformed = _rotate_if_long(geometry, rotate)
            notch_points.append((tuple((px - cut_x0, py - cut_y0)
                                       for px, py in transformed), notch.label))
        prepared.append((piece, net, cut, notch_points, w, h, rotate))

    # Put very long bands in a narrow left column. Packing them in the same
    # shelf row as bodices made the next row start 190 cm lower and wasted 20
    # sheets of paper even though the space beside the band was empty.
    placed: List[_PlacedPiece] = []
    long_items = [item for item in prepared if item[-1]]
    normal_items = [item for item in prepared if not item[-1]]
    gap = 0.7
    long_x = long_y = gap
    long_w = 0.0
    long_bottom = gap
    for piece, net, cut, notches, w, h, _ in long_items:
        placed.append(_PlacedPiece(piece, net, cut, long_x, long_y, notches))
        long_x += w + gap
        long_w += w + gap
        long_bottom = max(long_bottom, long_y + h)

    region_x = gap + long_w
    x = region_x
    y = gap
    row_h = 0.0
    used_w = max(long_x, region_x)
    for piece, net, cut, notches, w, h, _ in normal_items:
        if x > region_x and x + w > max_width_cm:
            x = region_x
            y += row_h + gap
            row_h = 0.0
        placed.append(_PlacedPiece(piece, net, cut, x, y, notches))
        x += w + gap
        row_h = max(row_h, h)
        used_w = max(used_w, x)
    bottom = max(long_bottom, y + row_h)
    return placed, (max(used_w + gap, 10.0), bottom + gap)


def _polyline(points, ox, oy):
    if not points:
        return ""
    commands = [f"{points[0][0] + ox:.4f} {points[0][1] + oy:.4f} m"]
    commands.extend(f"{x + ox:.4f} {y + oy:.4f} l" for x, y in points[1:])
    return "\n".join(commands)


def _pdf_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _page_stream(placed, tile_x, tile_y, tile_id, size, content_w_cm, content_h_cm):
    margin = 10.0 * MM_TO_PT
    lines = [
        "q",
        f"{margin:.4f} {margin:.4f} {content_w_cm * CM_TO_PT:.4f} {content_h_cm * CM_TO_PT:.4f} re W n",
        f"{CM_TO_PT:.8f} 0 0 {-CM_TO_PT:.8f} "
        f"{margin - tile_x * CM_TO_PT:.4f} {A4_HEIGHT_PT - margin + tile_y * CM_TO_PT:.4f} cm",
    ]
    for item in placed:
        lines += [
            "0.15 0.15 0.15 RG 0.035 w",
            _polyline(item.net, item.x, item.y), "S",
            "0.85 0.10 0.10 RG 0.035 w [0.25 0.12] 0 d",
            _polyline(item.cut, item.x, item.y), "S", "[] 0 d",
        ]
        xs = [p[0] + item.x for p in item.cut]
        ys = [p[1] + item.y for p in item.cut]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        lines += [
            "0.05 0.35 0.65 RG 0.03 w",
            f"{cx:.4f} {cy - 3:.4f} m {cx:.4f} {cy + 3:.4f} l S",
            f"BT /F1 0.34 Tf {min(xs):.4f} {max(ys) + 0.9:.4f} Td "
            f"({_pdf_string(item.piece.name_en)} / SIZE {size} / CUT {item.piece.qty}) Tj ET",
        ]
        for (apex, arm1, arm2), label in item.notches:
            ax, ay = apex[0] + item.x, apex[1] + item.y
            x1, y1 = arm1[0] + item.x, arm1[1] + item.y
            x2, y2 = arm2[0] + item.x, arm2[1] + item.y
            lines += [
                "0.75 0.15 0.10 RG 0.035 w",
                f"{x1:.4f} {y1:.4f} m {ax:.4f} {ay:.4f} l {x2:.4f} {y2:.4f} l S",
                f"BT /F1 0.28 Tf {ax + 0.25:.4f} {ay - 0.25:.4f} Td (NOTCH {_pdf_string(label)}) Tj ET",
            ]
    lines += ["Q"]

    # Page furniture is in points and therefore immune to pattern transforms.
    lines += [
        "0 0 0 RG 0.6 w",
        f"BT /F1 9 Tf {A4_WIDTH_PT - margin - 120:.4f} {A4_HEIGHT_PT - 18:.4f} Td (TILE {tile_id}) Tj ET",
        f"BT /F1 7 Tf {margin:.4f} 14 Td (PRINT AT 100% / ACTUAL SIZE - DO NOT FIT) Tj ET",
        f"BT /F1 7 Tf {margin + 250:.4f} 14 Td (MUSLIN SAMPLE ONLY - NOT BULK CUTTING) Tj ET",
    ]
    # Alignment crosses at printable-area corners.
    for px, py in ((margin, margin), (A4_WIDTH_PT - margin, margin),
                   (margin, A4_HEIGHT_PT - margin), (A4_WIDTH_PT - margin, A4_HEIGHT_PT - margin)):
        lines += [f"{px - 5:.4f} {py:.4f} m {px + 5:.4f} {py:.4f} l S",
                  f"{px:.4f} {py - 5:.4f} m {px:.4f} {py + 5:.4f} l S"]
    return "\n".join(lines).encode("ascii")


def _cover_stream(size: str, tile_count: int) -> bytes:
    margin = 20.0 * MM_TO_PT
    cal = 50.0 * MM_TO_PT
    lines = [
        "0 0 0 RG 0.8 w",
        f"BT /F1 20 Tf {margin:.4f} {A4_HEIGHT_PT - margin:.4f} Td (CROSSOVER BLOUSE - SIZE {_pdf_string(size)}) Tj ET",
        f"BT /F1 12 Tf {margin:.4f} {A4_HEIGHT_PT - margin - 28:.4f} Td (1:1 TILED MUSLIN SAMPLE PATTERN) Tj ET",
        f"BT /F1 10 Tf {margin:.4f} {A4_HEIGHT_PT - margin - 62:.4f} Td (1. PRINT AT 100% / ACTUAL SIZE - DO NOT FIT.) Tj ET",
        f"BT /F1 10 Tf {margin:.4f} {A4_HEIGHT_PT - margin - 80:.4f} Td (2. MEASURE THE BOX BELOW: BOTH SIDES MUST BE 50 mm.) Tj ET",
        f"BT /F1 10 Tf {margin:.4f} {A4_HEIGHT_PT - margin - 98:.4f} Td (3. ASSEMBLE {tile_count} TILES BY ID WITH 10 mm OVERLAP.) Tj ET",
        f"BT /F1 10 Tf {margin:.4f} {A4_HEIGHT_PT - margin - 116:.4f} Td (4. CUT RED DASHED LINE; SEW BLACK SOLID LINE.) Tj ET",
        f"{margin:.4f} {margin + 80:.4f} {cal:.4f} {cal:.4f} re S",
        f"BT /F1 10 Tf {margin:.4f} {margin + 80 + cal + 10:.4f} Td (50 x 50 mm CALIBRATION) Tj ET",
        f"BT /F1 11 Tf {margin:.4f} {margin + 42:.4f} Td (MUSLIN SAMPLE ONLY - NOT A PRODUCTION PATTERN OR MARKER.) Tj ET",
        f"BT /F1 9 Tf {margin:.4f} {margin + 22:.4f} Td (Pattern-maker fitting, shrinkage, grading and production review remain required.) Tj ET",
    ]
    return "\n".join(lines).encode("ascii")


def _write_pdf(path: Path, streams: Sequence[bytes]):
    # 1 catalog, 2 pages, 3 Helvetica; every page then owns a page/content pair.
    objects = []
    page_ids = [4 + i * 2 for i in range(len(streams))]
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    kids = " ".join(f"{i} 0 R" for i in page_ids)
    objects.append(f"<< /Type /Pages /Count {len(page_ids)} /Kids [{kids}] >>".encode())
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    for index, stream in enumerate(streams):
        content_id = page_ids[index] + 1
        objects.append(
            (f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {A4_WIDTH_PT:.4f} {A4_HEIGHT_PT:.4f}] "
             f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>").encode()
        )
        objects.append(f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream")

    header = (b"%PDF-1.4\n% native-vector-pattern\n"
              b"% tile-overlap-mm: 10.0\n"
              b"% calibration-square-mm: 50.0\n")
    body = bytearray(header)
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(body))
        body.extend(f"{number} 0 obj\n".encode())
        body.extend(obj)
        body.extend(b"\nendobj\n")
    xref = len(body)
    body.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    body.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        body.extend(f"{offset:010d} 00000 n \n".encode())
    body.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)


def write_tiled_pdf(pieces: Sequence, output, size: str, paper: str = "A4",
                    overlap_mm: float = 10.0) -> PdfManifest:
    if paper != "A4":
        raise ValueError("only A4 portrait paper is currently supported")
    if abs(overlap_mm - 10.0) > 1e-9:
        raise ValueError("tile overlap must be exactly 10 mm")
    problems = validate_sample_pattern(pieces)
    if problems:
        raise ValueError("sample pattern validation failed: " + "; ".join(problems))
    placed, sheet = _layout(pieces)
    content_w_cm = 19.0
    content_h_cm = 27.7
    step_x = content_w_cm - overlap_mm / 10.0
    step_y = content_h_cm - overlap_mm / 10.0
    cols = max(1, ceil(max(sheet[0] - overlap_mm / 10.0, 0.1) / step_x))
    rows = max(1, ceil(max(sheet[1] - overlap_mm / 10.0, 0.1) / step_y))
    tiles = []
    for row in range(rows):
        for col in range(cols):
            tile_x, tile_y = col * step_x, row * step_y
            tile_right, tile_bottom = tile_x + content_w_cm, tile_y + content_h_cm
            intersects = False
            for item in placed:
                xs = [x + item.x for x, _ in item.cut]
                ys = [y + item.y for _, y in item.cut]
                if (max(xs) > tile_x + 1e-6 and min(xs) < tile_right - 1e-6
                        and max(ys) > tile_y + 1e-6 and min(ys) < tile_bottom - 1e-6):
                    intersects = True
                    break
            if intersects:
                tiles.append((row, col, f"{chr(65 + row)}{col + 1}"))
    tile_ids = tuple(tile_id for _, _, tile_id in tiles)
    streams = []
    for row, col, tile_id in tiles:
        streams.append(_page_stream(
            placed, col * step_x, row * step_y, tile_id, size,
            content_w_cm, content_h_cm,
        ))
    streams.insert(0, _cover_stream(size, len(tile_ids)))
    _write_pdf(Path(output), streams)
    return PdfManifest(len(streams), tile_ids, overlap_mm, 50.0 * MM_TO_PT, sheet)
