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


def _label_width(text, font_size=14):
    """Conservative width estimate for mixed CJK/Latin SVG labels."""
    return sum(font_size * (1.0 if ord(ch) > 0x2E80 else 0.58) for ch in text)


def render_assembly(pieces, size="M"):
    padding = 42
    max_width = 1420
    top = 112
    columns = 3
    gap = 22
    card_w = (max_width - 2 * padding - (columns - 1) * gap) / columns
    card_h = 330
    drawing_w = card_w - 36
    drawing_h = 226
    nodes = []
    centres = {}
    for index, piece in enumerate(pieces):
        row, column = divmod(index, columns)
        card_x = padding + column * (card_w + gap)
        card_y = top + row * (card_h + gap)
        x0, y0, x1, y1 = piece.bbox()
        raw_w, raw_h = x1 - x0, y1 - y0
        scale = min(3.3, drawing_w / raw_w, drawing_h / raw_h)
        draw_w, draw_h = raw_w * scale, raw_h * scale
        piece_x = card_x + (card_w - draw_w) / 2
        piece_y = card_y + 20 + (drawing_h - draw_h) / 2
        ox, oy = piece_x - x0 * scale, piece_y - y0 * scale
        d = _path_d(piece.path, ox, oy, scale)
        name = html.escape(piece.name_en, quote=True)
        zh_label = html.escape(f"{index + 1}. {piece.name}  ×{piece.qty}")
        en_label = html.escape(f"{piece.name_en}  /  cut quantity {piece.qty}")
        label_x = card_x + 12
        label_y = card_y + card_h - 45
        label_w = card_w - 24
        nodes.append(
            f'<g data-piece-card="{name}" data-card-x="{card_x:.2f}" '
            f'data-card-y="{card_y:.2f}" data-card-width="{card_w:.2f}" '
            f'data-card-height="{card_h:.2f}">'
            f'<rect x="{card_x:.2f}" y="{card_y:.2f}" width="{card_w:.2f}" '
            f'height="{card_h:.2f}" rx="8" fill="#fbfcfd" stroke="#b7c2cc"/>'
            f'<path data-piece="{name}" d="{d}" fill="#f8fbff" '
            f'stroke="#17324d" stroke-width="2"/>'
            f'<text data-piece-label="{name}" data-box-x="{label_x:.2f}" '
            f'data-box-y="{label_y:.2f}" data-box-width="{label_w:.2f}" '
            f'data-max-width="{label_w:.2f}" x="{label_x:.2f}" y="{label_y:.2f}" '
            f'font-size="14" fill="#17324d">'
            f'<tspan x="{label_x:.2f}" dy="0" font-weight="700">{zh_label}</tspan>'
            f'<tspan x="{label_x:.2f}" dy="20" font-size="12" fill="#52677b">{en_label}</tspan>'
            f'</text></g>'
        )
        centres[piece.name_en] = (piece_x + draw_w / 2, piece_y + draw_h / 2)

    rows = (len(pieces) + columns - 1) // columns
    height = top + rows * card_h + (rows - 1) * gap + 42
    arrows = []
    for front in ("Front L (overlap)", "Front R (under)"):
        if front in centres and "Back" in centres:
            a, b = centres[front], centres["Back"]
            arrows.append(
                f'<path d="M {a[0]:.1f} {a[1]:.1f} Q {(a[0]+b[0])/2:.1f} '
                f'{top + 5:.1f} {b[0]:.1f} {b[1]:.1f}" fill="none" '
                f'stroke="#d54b3d" stroke-width="1.5" stroke-dasharray="7 5" '
                f'opacity="0.65" marker-end="url(#arrow)"/>'
            )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{max_width}" height="{height:.0f}" viewBox="0 0 {max_width} {height:.0f}">
<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#d54b3d"/></marker></defs>
<rect width="100%" height="100%" fill="#ffffff"/>
<text data-document-title="true" x="42" y="38" font-size="25" font-weight="700" fill="#17324d">交领上衣裁片拼装示意 / Crossover Blouse Assembly Guide — {html.escape(size)}码 / Size {html.escape(size)}</text>
<text x="42" y="66" font-size="14" fill="#52677b">Canonical geometry: each block uses the exact same outline as the technical SVG.</text>
<text x="42" y="88" font-size="13" fill="#d54b3d">Assembly overview only; not a cutting pattern. Use it to verify piece identity and joining relationships.</text>
{''.join(nodes)}
{''.join(arrows)}
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
