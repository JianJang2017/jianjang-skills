#!/usr/bin/env python3
"""Assembly overview rendered strictly from canonical pattern-piece paths."""

from __future__ import annotations

import argparse
import html
from pathlib import Path

from calculate_garment import SIZE_CHART
from pattern_drafting import DRAFTERS


def _path_d(path, ox, oy, scale):
    out = []
    for seg in path:
        if seg[0] == "M":
            out.append(f"M {ox + seg[1] * scale:.2f} {oy + seg[2] * scale:.2f}")
        elif seg[0] == "L":
            out.append(f"L {ox + seg[1] * scale:.2f} {oy + seg[2] * scale:.2f}")
        elif seg[0] == "Q":
            out.append(
                f"Q {ox + seg[1] * scale:.2f} {oy + seg[2] * scale:.2f} "
                f"{ox + seg[3] * scale:.2f} {oy + seg[4] * scale:.2f}"
            )
        elif seg[0] == "Z":
            out.append("Z")
    return " ".join(out)


def render_assembly(pieces, size="M"):
    scale = 3.3
    padding = 42
    x = padding
    y = 112
    row_h = 0
    max_width = 1420
    nodes = []
    centres = {}
    for index, piece in enumerate(pieces):
        x0, y0, x1, y1 = piece.bbox()
        w, h = (x1 - x0) * scale, (y1 - y0) * scale
        # Long bands are rotated as whole canonical blocks; their outline is
        # never redrawn or approximated.
        rotate = w > 620
        draw_w, draw_h = (h, w) if rotate else (w, h)
        if x + draw_w + 160 > max_width and x > padding:
            x = padding
            y += row_h + 95
            row_h = 0
        ox, oy = -x0 * scale, -y0 * scale
        transform = f"translate({x:.2f},{y:.2f})"
        if rotate:
            transform += f" translate({draw_w:.2f},0) rotate(90)"
        d = _path_d(piece.path, ox, oy, scale)
        name = html.escape(piece.name_en, quote=True)
        label = html.escape(f"{index + 1}. {piece.name} / {piece.name_en} x{piece.qty}")
        nodes.append(
            f'<g transform="{transform}"><path data-piece="{name}" d="{d}" '
            f'fill="#f8fbff" stroke="#17324d" stroke-width="2"/>'
            f'<text x="0" y="{draw_h + 24:.2f}" font-size="14" fill="#17324d">{label}</text></g>'
        )
        centres[piece.name_en] = (x + draw_w / 2, y + draw_h / 2)
        x += draw_w + 120
        row_h = max(row_h, draw_h)

    height = y + row_h + 130
    arrows = []
    for front in ("Front L (overlap)", "Front R (under)"):
        if front in centres and "Back" in centres:
            a, b = centres[front], centres["Back"]
            arrows.append(
                f'<path d="M {a[0]:.1f} {a[1]:.1f} Q {(a[0]+b[0])/2:.1f} '
                f'{min(a[1],b[1])-45:.1f} {b[0]:.1f} {b[1]:.1f}" fill="none" '
                f'stroke="#d54b3d" stroke-width="2" stroke-dasharray="7 5" marker-end="url(#arrow)"/>'
            )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{max_width}" height="{height:.0f}" viewBox="0 0 {max_width} {height:.0f}">
<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#d54b3d"/></marker></defs>
<rect width="100%" height="100%" fill="#ffffff"/>
<text x="42" y="38" font-size="25" font-weight="700" fill="#17324d">Crossover blouse assembly blocks — Size {html.escape(size)}</text>
<text x="42" y="66" font-size="14" fill="#52677b">Canonical geometry: each block is the exact same outline used by the technical SVG and 1:1 PDF.</text>
<text x="42" y="88" font-size="13" fill="#d54b3d">Assembly overview only; cut from the validated tiled PDF at 100%.</text>
{''.join(arrows)}
{''.join(nodes)}
</svg>'''


def main():
    parser = argparse.ArgumentParser(description="Render canonical assembly overview SVG")
    parser.add_argument("--type", default="crossover-blouse", choices=sorted(DRAFTERS))
    parser.add_argument("--size", default="M", choices=sorted(SIZE_CHART["tops"]))
    parser.add_argument("--fit", default="regular")
    parser.add_argument("--output", "-o", required=True)
    args = parser.parse_args()
    category, drafter = DRAFTERS[args.type]
    pieces = drafter(SIZE_CHART[category][args.size], fit=args.fit)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_assembly(pieces, args.size), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
