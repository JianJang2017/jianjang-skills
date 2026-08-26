#!/usr/bin/env python3
"""Detect overlapping text in the rendered pattern SVGs.

Parses every <text> element, resolves its position through any <g transform>,
estimates its extent from font size and script (CJK glyphs are ~1em wide, Latin
~0.55em), then reports pairs whose boxes intersect.

This exists because label collisions are invisible to the other tests — the SVG
is well-formed and every string is present, so only geometry catches it. It found
three real defects: a caption block wider than its layout cell, the English line
of a rotated dimension drawn on top of its Chinese line, and the fold/grain
captions landing on the body-length dimension.

Rotated and horizontal text are compared separately: they cross in the gutters
by design, and flagging those pairs would bury the real collisions.
"""
import re
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://www.w3.org/2000/svg}"


def width_of(s, size):
    return sum(size * (1.0 if ord(c) > 0x2E80 else 0.55) for c in s)


def collect(path):
    """Return [(x, y, w, h, text)] in absolute coords, resolving <g transform>."""
    root = ET.parse(path).getroot()
    out = []

    def walk(node, tx, ty, rot):
        for child in node:
            t = child.get("transform", "")
            ctx, cty, crot = tx, ty, rot
            m = re.search(r"translate\(([-\d.]+),([-\d.]+)\)", t)
            if m:
                ctx += float(m.group(1))
                cty += float(m.group(2))
            if "rotate(-90)" in t:
                crot = True
            if child.tag == f"{NS}text":
                try:
                    lx_ = float(child.get("x", 0))
                    ly_ = float(child.get("y", 0))
                except ValueError:
                    continue
                size = float(child.get("font-size", 10))
                s = "".join(child.itertext())
                if not s.strip():
                    continue
                w = width_of(s, size)
                anchor = child.get("text-anchor", "start")

                if crot:
                    # Under rotate(-90), local (x, y) maps to screen (y, -x).
                    # So the *local y* becomes the screen x — that is what
                    # separates stacked lines inside a rotated group, and
                    # ignoring it made every rotated pair look coincident.
                    sx = ctx + ly_
                    sy = cty - lx_
                    if anchor == "middle":
                        y0 = sy - w / 2
                    elif anchor == "end":
                        y0 = sy - w
                    else:
                        y0 = sy
                    out.append((sx - size * 0.8, y0, size, w, s, True))
                else:
                    sx, sy = ctx + lx_, cty + ly_
                    if anchor == "middle":
                        sx -= w / 2
                    elif anchor == "end":
                        sx -= w
                    out.append((sx, sy - size * 0.8, w, size, s, False))
            walk(child, ctx, cty, crot)

    walk(root, 0.0, 0.0, False)
    return out


def overlaps(a, b, pad=-1.0):
    ax, ay, aw, ah = a[0], a[1], a[2], a[3]
    bx, by, bw, bh = b[0], b[1], b[2], b[3]
    return not (ax + aw + pad <= bx or bx + bw + pad <= ax
                or ay + ah + pad <= by or by + bh + pad <= ay)


ROOT = Path(__file__).resolve().parent.parent
SPECS = [
    ("crossover-blouse", "01-gufeng-blouse", ["--fit", "loose", "--fabric-width", "140"]),
    ("t-shirt", "03-tshirt", ["--fabric-width", "140"]),
    ("pants", "04-jeans", ["--fabric-width", "150"]),
    ("dress", "05-dress", ["--fabric-width", "114"]),
]
import subprocess
total_bad = 0
with tempfile.TemporaryDirectory(prefix="clothes-pattern-overlap-") as tmp:
    out_dir = Path(tmp)
    for gt, name, extra in SPECS:
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "draw_pattern.py"),
             "--type", gt, "--size", "M", *extra,
             "-o", str(out_dir / f"{name}-pattern.svg")],
            capture_output=True, cwd=ROOT, check=True)

    for f in sorted(out_dir.glob("*-pattern.svg")):
        items = collect(f)
        bad = []
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                a, b = items[i], items[j]
                # Rotated vs horizontal crossings are expected in gutters.
                if a[5] != b[5]:
                    continue
                if overlaps(a, b):
                    bad.append((a[4][:34], b[4][:34]))
        total_bad += len(bad)
        print(f"{'✅' if not bad else '❌'} {f.name:<32} "
              f"{len(items)} 条文本, {len(bad)} 处重叠")
        for x, y in bad[:6]:
            print(f"      ⚠ {x!r}  ×  {y!r}")

print()
if total_bad:
    print(f"❌ 共 {total_bad} 处文本重叠")
    sys.exit(1)
print("✅ 无同向文本重叠")
