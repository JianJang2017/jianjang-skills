#!/usr/bin/env python3
"""
Render pattern pieces as a dimensioned SVG cutting diagram.

Why SVG rather than an AI-generated raster: dimension text has to be exact and
legible at print size, and every number has to trace back to the size chart.
A vector drawing gives crisp text at any zoom and — because the geometry and
the annotations come from the same computation —
cannot disagree with itself.

The SVG is a complete single-canvas vector reference that can be enlarged
without loss. It remains a scaled technical reference, not a cutting pattern.

Output conventions follow garment-industry drafting practice:
  solid outline     净样线 (net/sewing line)
  dashed outline    毛样线 (cutting line = net + seam allowance)
  long-dash-dot     对折线 (fold edge, no seam allowance)
  arrow with ↕      布纹方向 (grain line, must align with warp)
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

from calculate_garment import SIZE_CHART, SIZE_ORDER          # noqa: E402
from pattern_drafting import (                                 # noqa: E402
    DRAFTERS, Piece, Dim, validate_pieces, validate_fabric_width,
    SEAM_ALLOWANCE, EASE,
    dim_english, seam_label, quad_max_depth,
)
from pattern_geometry import build_cut_outline                 # noqa: E402

# ─── Drawing constants ──────────────────────────────────────────────────────
PX_PER_CM = 3.2          # on-screen scale; 1:10 ⇒ ~0.32 px/mm
MARGIN = 42
GAP = 34                 # gutter between pieces
LABEL_BAND = 74          # room under each piece for its name/size block
TITLE_H = 100
FOOTER_H = 148

C_OUTLINE = "#0f2b3d"
C_CUT = "#e8734a"
C_FOLD = "#2f7fb8"
C_DIM = "#c0392b"
C_GRAIN = "#1f7a4d"
C_ARC = "#7d3cad"      # 弧长标注（与直线尺寸区分开）
C_GRID = "#dce6ec"
C_TEXT = "#0f2b3d"
C_MUTED = "#5b7183"
C_BG = "#fbfdfe"

FONT = "'Helvetica Neue',Helvetica,'PingFang SC','Hiragino Sans GB',Arial,sans-serif"


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def text_width(s: str, size: float) -> float:
    """
    Approximate rendered width. CJK glyphs occupy roughly a full em, Latin
    about 0.55em. Needed because the caption block sits in a fixed-width cell —
    without measuring, a long bilingual line silently runs into the piece
    drawn to its right.
    """
    return sum(size * (1.0 if ord(ch) > 0x2E80 else 0.55) for ch in s)


def wrap_to_width(parts: List[str], sep: str, size: float, max_w: float
                  ) -> List[str]:
    """Greedily pack `parts` into lines no wider than max_w."""
    lines: List[str] = []
    cur = ""
    for part in parts:
        trial = part if not cur else cur + sep + part
        if cur and text_width(trial, size) > max_w:
            lines.append(cur)
            cur = part
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


class Canvas:
    def __init__(self):
        self.parts: List[str] = []

    def add(self, s: str):
        self.parts.append(s)

    def line(self, x1, y1, x2, y2, stroke=C_OUTLINE, w=1.0, dash=None, cap="round"):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
                 f'stroke="{stroke}" stroke-width="{w}"{d} stroke-linecap="{cap}"/>')

    def path(self, d, stroke=C_OUTLINE, w=1.6, fill="none", dash=None):
        da = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{w}"'
                 f'{da} stroke-linejoin="round"/>')

    def text(self, x, y, s, size=11, fill=C_TEXT, anchor="start", weight="400",
             style="normal", family=FONT):
        self.add(f'<text x="{x:.2f}" y="{y:.2f}" font-family="{family}" '
                 f'font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
                 f'font-weight="{weight}" font-style="{style}">{esc(s)}</text>')

    def rect(self, x, y, w, h, fill="none", stroke=None, sw=1.0, rx=0, dash=None):
        st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
        da = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" '
                 f'fill="{fill}"{st}{da} rx="{rx}"/>')

    def svg(self, w, h) -> str:
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" '
                f'height="{h:.0f}" viewBox="0 0 {w:.0f} {h:.0f}">')
        defs = (
            '<defs>'
            f'<marker id="ar" markerWidth="9" markerHeight="9" refX="8" refY="3.2" '
            f'orient="auto"><path d="M0,0 L8,3.2 L0,6.4 z" fill="{C_DIM}"/></marker>'
            f'<marker id="al" markerWidth="9" markerHeight="9" refX="0" refY="3.2" '
            f'orient="auto"><path d="M8,0 L0,3.2 L8,6.4 z" fill="{C_DIM}"/></marker>'
            f'<marker id="gr" markerWidth="10" markerHeight="10" refX="9" refY="3.4" '
            f'orient="auto"><path d="M0,0 L9,3.4 L0,6.8 z" fill="{C_GRAIN}"/></marker>'
            f'<marker id="gl" markerWidth="10" markerHeight="10" refX="1" refY="3.4" '
            f'orient="auto"><path d="M9,0 L0,3.4 L9,6.8 z" fill="{C_GRAIN}"/></marker>'
            '<pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">'
            f'<path d="M32 0 L0 0 0 32" fill="none" stroke="{C_GRID}" stroke-width="0.6"/>'
            '</pattern>'
            '</defs>'
        )
        return head + defs + "".join(self.parts) + "</svg>"


def piece_path_d(p: Piece, ox: float, oy: float, sx: float, sy: float) -> str:
    """Convert a piece outline into an SVG path, translated and scaled."""
    out = []
    for seg in p.path:
        if seg[0] == "M":
            out.append(f"M {ox + seg[1]*sx:.2f} {oy + seg[2]*sy:.2f}")
        elif seg[0] == "L":
            out.append(f"L {ox + seg[1]*sx:.2f} {oy + seg[2]*sy:.2f}")
        elif seg[0] == "Q":
            out.append(f"Q {ox + seg[1]*sx:.2f} {oy + seg[2]*sy:.2f} "
                       f"{ox + seg[3]*sx:.2f} {oy + seg[4]*sy:.2f}")
        elif seg[0] == "Z":
            out.append("Z")
    return " ".join(out)


def draw_dim(c: Canvas, d: Dim, ox: float, oy: float, s: float):
    """
    Draw one dimension: extension lines, a double-arrowed measure line, and the
    value text. The number shown is the one stored on the Dim, which
    validate_pieces() has already checked against the geometry.
    """
    x1, y1 = ox + d.p1[0] * s, oy + d.p1[1] * s
    x2, y2 = ox + d.p2[0] * s, oy + d.p2[1] * s
    off = d.offset * s

    en = d.en or dim_english(d.label)
    # Chinese term + number on top, English term beneath in smaller type. Both
    # sit on an opaque plate so the grid and outline don't show through.
    w_box = max(len(d.label) * 6.2, len(en) * 5.0) + 6

    if d.kind == "h":
        ly = max(y1, y2) + off if off >= 0 else min(y1, y2) + off
        c.line(x1, y1, x1, ly, C_DIM, 0.5, dash="2,2")
        c.line(x2, y2, x2, ly, C_DIM, 0.5, dash="2,2")
        c.add(f'<line x1="{x1:.2f}" y1="{ly:.2f}" x2="{x2:.2f}" y2="{ly:.2f}" '
              f'stroke="{C_DIM}" stroke-width="0.9" marker-start="url(#al)" '
              f'marker-end="url(#ar)"/>')
        tx = (x1 + x2) / 2
        ty = ly - 5.0 if off >= 0 else ly + 12
        h_box = 21 if en else 12
        y_box = (ty - 9.5) if off >= 0 else (ty - 9.5)
        if en and off >= 0:
            y_box = ty - 9.5
        c.add(f'<rect x="{tx - w_box/2:.2f}" y="{y_box:.2f}" '
              f'width="{w_box:.2f}" height="{h_box}" fill="{C_BG}" opacity="0.9" rx="2"/>')
        c.text(tx, ty, d.label, size=9.5, fill=C_DIM, anchor="middle", weight="600")
        if en:
            c.text(tx, ty + 9, en, size=7.6, fill=C_MUTED, anchor="middle",
                   style="italic")
    else:
        lx = max(x1, x2) + off if off >= 0 else min(x1, x2) + off
        c.line(x1, y1, lx, y1, C_DIM, 0.5, dash="2,2")
        c.line(x2, y2, lx, y2, C_DIM, 0.5, dash="2,2")
        c.add(f'<line x1="{lx:.2f}" y1="{y1:.2f}" x2="{lx:.2f}" y2="{y2:.2f}" '
              f'stroke="{C_DIM}" stroke-width="0.9" marker-start="url(#al)" '
              f'marker-end="url(#ar)"/>')
        my = (y1 + y2) / 2
        # In the rotated group the two lines stack along screen-x, so they need
        # a full line's separation. y=-11 / y=-1 keeps the 9.5px Chinese line
        # clear of the 7.6px English one; y=+5 (the earlier value) overlapped it.
        h_box = 24 if en else 13
        en_line = (f'<text x="0" y="-1.5" font-family="{FONT}" font-size="7.4" '
                   f'fill="{C_MUTED}" text-anchor="middle" font-style="italic">'
                   f'{esc(en)}</text>') if en else ""
        c.add(f'<g transform="translate({lx:.2f},{my:.2f}) rotate(-90)">'
              f'<rect x="{-w_box/2:.2f}" y="{-13 if en else -11.5:.1f}" '
              f'width="{w_box:.2f}" '
              f'height="{h_box}" fill="{C_BG}" opacity="0.92" rx="2"/>'
              f'<text x="0" y="{-12 if en else -3.5:.1f}" font-family="{FONT}" '
              f'font-size="9.5" fill="{C_DIM}" '
              f'text-anchor="middle" font-weight="600">{esc(d.label)}</text>'
              f'{en_line}</g>')


def draw_arcs(c: Canvas, p: Piece, ox: float, oy: float, s: float):
    """
    Annotate each curve with its arc length and scoop depth.

    A curve dimensioned only by its endpoints is not reproducible — the scoop
    depth is what a pattern maker sets with a curve ruler, and the arc length is
    what has to match the piece it sews into. Both are drawn with a leader line
    to the deepest point of the curve so it is unambiguous which edge is meant.
    """
    cursor = None
    for idx, seg in enumerate(p.path):
        if seg[0] in ("M", "L"):
            cursor = (seg[1], seg[2])
            continue
        if seg[0] != "Q":
            continue
        p0, p1, p2 = cursor, (seg[1], seg[2]), (seg[3], seg[4])
        cursor = p2
        arc = next((a for a in p.arcs if a.seg_index == idx), None)
        if arc is None:
            continue

        depth, at = quad_max_depth(p0, p1, p2)
        ax, ay = ox + at[0] * s, oy + at[1] * s

        # Leader points away from the piece body.
        dx = 30 if arc.side == "right" else -30
        lx, ly = ax + dx, ay - 16
        c.line(ax, ay, lx, ly, C_ARC, 0.8)
        c.add(f'<circle cx="{ax:.2f}" cy="{ay:.2f}" r="1.9" fill="{C_ARC}"/>')

        anchor = "start" if dx > 0 else "end"
        tx = lx + (3 if dx > 0 else -3)
        txt = arc.label
        en = arc.en
        w = max(text_width(txt, 9), text_width(en, 7.4),
                text_width(arc.depth_label, 7.6)) + 7
        bx = tx if dx > 0 else tx - w
        rows = 1 + (1 if en else 0) + (1 if arc.depth_label else 0)
        c.rect(bx - 2, ly - 10, w, 10.5 * rows + 3, fill=C_BG, rx=2)
        c.text(tx, ly, txt, size=9, fill=C_ARC, anchor=anchor, weight="600")
        yy = ly
        if en:
            yy += 9
            c.text(tx, yy, en, size=7.4, fill=C_MUTED, anchor=anchor, style="italic")
        if arc.depth_label:
            yy += 9.5
            c.text(tx, yy, arc.depth_label + f"  {dim_english(arc.depth_label)}",
                   size=7.6, fill=C_ARC, anchor=anchor)
            # show the chord so the scoop depth is visually anchored
            c.line(ox + p0[0] * s, oy + p0[1] * s,
                   ox + p2[0] * s, oy + p2[1] * s, C_ARC, 0.5, dash="3,3")


def draw_grain(c: Canvas, p: Piece, ox: float, oy: float, s: float):
    """Grain arrow — cutting off-grain makes a garment twist on the body."""
    x0, y0, x1, y1 = p.bbox()
    cx = ox + (x0 + x1) / 2 * s
    cy = oy + (y0 + y1) / 2 * s
    if p.grain == "vertical":
        # Vertical dimension labels are centred on the midpoint of their span,
        # so the grain caption has to avoid those midpoints rather than sit at a
        # fixed fraction of the height. Pick the vertical position furthest from
        # every existing label midpoint — this generalises to new pieces instead
        # of needing a hand-tuned offset per drafter.
        # Same collision test as the fold caption, with the fold caption itself
        # added to the blocked set. Placing by a "looks empty" fraction is what
        # kept moving this label off one dimension and onto another.
        blocked = dim_label_rects(p, ox, oy, s)
        if p.fold_edge == "left":
            fx, fy = fold_caption_pos(p, ox, oy, s)
            fw, fh = FOLD_CAPTION
            blocked.append((fx - fh, fy - fw / 2, fh, fw))
        cands = [(ox + (x0 + (x1 - x0) * cf) * s, oy + (y0 + (y1 - y0) * rf) * s)
                 for rf in (0.5, 0.42, 0.58, 0.34, 0.66)
                 for cf in (0.5, 0.36, 0.64, 0.26, 0.74)]
        gw, gh = GRAIN_CAPTION
        free = [a for a in cands
                if not any(hit((a[0] - gh, a[1] - gw / 2, gh, gw), b)
                           for b in blocked)]
        # A small, heavily dimensioned piece (a short sleeve is ~54x64px with
        # five dimensions) has no room for the caption at any position. The
        # arrow alone is the standard grain marking and the legend names it, so
        # drop the text rather than print it on top of a measurement.
        show_caption = bool(free)
        gx, gy = (free[0] if free
                  else (ox + (x0 + x1) / 2 * s, oy + (y0 + y1) / 2 * s))
        gx += 9        # anchor is the caption; the arrow sits just right of it
        half = min((y1 - y0) * s * 0.11, 26)
        c.add(f'<line x1="{gx:.2f}" y1="{gy-half:.2f}" x2="{gx:.2f}" y2="{gy+half:.2f}" '
              f'stroke="{C_GRAIN}" stroke-width="1.1" marker-start="url(#gl)" '
              f'marker-end="url(#gr)"/>')
        if show_caption:
            c.add(f'<g transform="translate({gx-9:.2f},{gy:.2f}) rotate(-90)">'
                  f'<rect x="-26" y="-10" width="52" height="11" fill="{C_BG}" '
                  f'opacity="0.9" rx="2"/>'
                  f'<text x="0" y="-1.5" font-family="{FONT}" font-size="8.5" '
                  f'fill="{C_GRAIN}" text-anchor="middle">经向 Warp</text></g>')
    else:
        half = min((x1 - x0) * s * 0.3, 46)
        c.add(f'<line x1="{cx-half:.2f}" y1="{cy:.2f}" x2="{cx+half:.2f}" y2="{cy:.2f}" '
              f'stroke="{C_GRAIN}" stroke-width="1.1" marker-start="url(#gl)" '
              f'marker-end="url(#gr)"/>')
        c.text(cx, cy - 5, "纬向 Weft", size=8.5, fill=C_GRAIN, anchor="middle")


def draw_fold(c: Canvas, p: Piece, ox: float, oy: float, s: float):
    """Mark the fold edge. A cutter who misses this cuts two half-panels."""
    if p.fold_edge != "left":
        return
    x0, y0, _, y1 = p.bbox()
    x = ox + x0 * s
    c.line(x, oy + y0 * s, x, oy + y1 * s, C_FOLD, 1.8, dash="12,3,3,3")
    # Place the caption inside the panel at the first spot that clears every
    # dimension label. Outside-left, where this used to sit, is exactly where the
    # 衣长/腰节长 label runs.
    fx, fy = fold_caption_pos(p, ox, oy, s)
    c.add(f'<g transform="translate({fx:.2f},{fy:.2f}) rotate(-90)">'
          f'<rect x="-42" y="-10" width="84" height="12" fill="{C_BG}" '
          f'opacity="0.92" rx="2"/>'
          f'<text x="0" y="-1" font-family="{FONT}" font-size="8.5" fill="{C_FOLD}" '
          f'text-anchor="middle" font-weight="600">对折线 Cut on fold</text></g>')


Rect = Tuple[float, float, float, float]      # x, y, w, h in screen coords


def hit(a: Rect, b: Rect, pad: float = 2.0) -> bool:
    return not (a[0] + a[2] + pad <= b[0] or b[0] + b[2] + pad <= a[0]
                or a[1] + a[3] + pad <= b[1] or b[1] + b[3] + pad <= a[1])


def dim_label_rects(p: Piece, ox: float, oy: float, s: float) -> List[Rect]:
    """
    Screen-space boxes of every dimension label this piece will draw.

    Captions are positioned by testing against these rather than against a
    hand-picked offset. Guessing a "free" fraction of the panel is what produced
    the whack-a-mole: each nudge moved a caption off one label and onto another,
    because the labels sit at dimension midpoints, not at fixed fractions.
    """
    rects: List[Rect] = []
    for d in spread_vertical_dims(p.dims):
        x1, y1 = ox + d.p1[0] * s, oy + d.p1[1] * s
        x2, y2 = ox + d.p2[0] * s, oy + d.p2[1] * s
        off = d.offset * s
        en = d.en or dim_english(d.label)
        w = max(text_width(d.label, 9.5), text_width(en, 7.4)) + 6
        if d.kind == "h":
            ly = max(y1, y2) + off if off >= 0 else min(y1, y2) + off
            ty = ly - 5.0 if off >= 0 else ly + 12
            rects.append(((x1 + x2) / 2 - w / 2, ty - 9.5, w, 24 if en else 13))
        else:
            lx = max(x1, x2) + off if off >= 0 else min(x1, x2) + off
            my = (y1 + y2) / 2
            # rotate(-90): local x spans screen y, local y spans screen x
            rects.append((lx - 13, my - w / 2, 24 if en else 13, w))
    return rects


def place_rotated_caption(blocked: List[Rect], cands: List[Tuple[float, float]],
                          w: float, h: float) -> Tuple[float, float]:
    """
    First candidate anchor whose rotated caption box clears everything drawn.

    `w`/`h` are the caption's screen extents (a rotated caption is tall and
    narrow). Falls back to the candidate with the fewest collisions so a crowded
    piece still renders rather than throwing.
    """
    def box(a):
        return (a[0] - h, a[1] - w / 2, h, w)

    best, best_n = cands[0], 1 << 30
    for a in cands:
        n = sum(1 for b in blocked if hit(box(a), b))
        if n == 0:
            return a
        if n < best_n:
            best, best_n = a, n
    return best


FOLD_CAPTION = (84.0, 12.0)      # screen w x h of the rotated fold caption
GRAIN_CAPTION = (52.0, 11.0)


def fold_caption_pos(p: Piece, ox: float, oy: float,
                     s: float) -> Tuple[float, float]:
    """Anchor for the fold caption: inside the fold edge, clear of all labels."""
    x0, y0, x1, y1 = p.bbox()
    blocked = dim_label_rects(p, ox, oy, s)
    cands = [(ox + x0 * s + dx, oy + (y0 + (y1 - y0) * f) * s)
             for f in (0.80, 0.88, 0.70, 0.62, 0.50)
             for dx in (30, 44, 22)]
    return place_rotated_caption(blocked, cands, *FOLD_CAPTION)


def draw_cut_line(c: Canvas, p: Piece, ox: float, oy: float, s: float):
    """
    Dashed cutting line offset outside the net line.

    Drawn as a scaled expansion about the piece centre rather than a true
    parallel offset: an exact offset needs curve maths that buys nothing here,
    since the per-edge allowances are printed numerically in the piece's own
    table. The dashed line communicates "cut wider than you sew" — the exact
    amounts come from the text, not from measuring the drawing.
    """
    if p.path_allowances:
        points = build_cut_outline(p)
        d = [f"M {ox + points[0][0] * s:.2f} {oy + points[0][1] * s:.2f}"]
        d.extend(f"L {ox + x * s:.2f} {oy + y * s:.2f}" for x, y in points[1:])
        c.add(f'<path data-cut-method="true-offset" d="{" ".join(d)}" fill="none" '
              f'stroke="{C_CUT}" stroke-width="1.0" stroke-dasharray="7,4" '
              f'opacity="0.85"/>')
        return

    x0, y0, x1, y1 = p.bbox()
    w, h = (x1 - x0) or 1, (y1 - y0) or 1
    sa_x = p.seams.get("side", 1.0)
    sa_y = p.seams.get("hem", 2.0)
    fx, fy = (w + sa_x) / w, (h + sa_y) / h
    cx, cy = ox + (x0 + x1) / 2 * s, oy + (y0 + y1) / 2 * s
    d = piece_path_d(p, ox, oy, s, s)
    c.add(f'<g transform="translate({cx:.2f},{cy:.2f}) scale({fx:.4f},{fy:.4f}) '
          f'translate({-cx:.2f},{-cy:.2f})">'
          f'<path d="{d}" fill="none" stroke="{C_CUT}" stroke-width="1.0" '
          f'stroke-dasharray="7,4" opacity="0.85"/></g>')


def spread_vertical_dims(dims: List[Dim]) -> List[Dim]:
    """
    Push apart vertical dimensions that share an edge and a side.

    Two vertical dims measured on the same x with offsets of similar magnitude
    render their rotated label plates on top of each other. Rather than hand-tune
    an offset per drafter (which breaks the moment a new piece is added), fan out
    any group that would collide: same measurement line, same side, label
    midpoints within a label-height of each other.
    """
    out = list(dims)
    verticals = [(i, d) for i, d in enumerate(out) if d.kind == "v"]
    groups: Dict[Tuple[float, bool], List[int]] = {}
    for i, d in verticals:
        key = (round(max(d.p1[0], d.p2[0]), 2), d.offset >= 0)
        groups.setdefault(key, []).append(i)

    for (_, positive), idxs in groups.items():
        if len(idxs) < 2:
            continue
        # order by span midpoint so the fan-out follows the drawing
        idxs.sort(key=lambda i: (out[i].p1[1] + out[i].p2[1]) / 2)
        step = 4.6
        base = min(abs(out[i].offset) for i in idxs)
        for rank, i in enumerate(idxs):
            mag = base + rank * step
            d = out[i]
            out[i] = Dim(d.kind, d.p1, d.p2, d.label,
                         mag if positive else -mag, d.value, d.en)
    return out


CAPTION_TOP = 34          # gap between the piece's bottom edge and its caption
CAPTION_LINE = 12.5       # line height inside the caption block
CAPTION_MIN_W = 250       # captions narrower than this are unreadable


def caption_lines(p: Piece, cell_w: float) -> List[Tuple[str, float, str, str]]:
    """
    Build the caption as (text, size, colour, weight) rows, wrapped to cell_w.

    The seam-allowance list is the line that overflows: bilingual terms for a
    bodice run past 590px inside a 210px cell, which is what was colliding with
    the neighbouring piece. Wrapping it into as many rows as it needs — and
    reporting that height back to the layout — is what keeps the block inside
    its own column.
    """
    avail = max(cell_w - 8, CAPTION_MIN_W)
    nw, nh = p.net_size()
    cw, ch = p.cut_size()
    rows: List[Tuple[str, float, str, str]] = [
        (f"{p.name}  /  {p.name_en}  × {p.qty}", 11.5, C_TEXT, "700"),
    ]
    for ln in wrap_to_width(
        [f"净样 Net {nw}×{nh}cm", f"毛样 Cut {cw}×{ch}cm"], "    ", 9.5, avail
    ):
        rows.append((ln, 9.5, C_MUTED, "400"))

    seams = [f"{seam_label(k)} {v}" for k, v in p.seams.items() if v > 0]
    if seams:
        packed = wrap_to_width(seams, "   ", 8.5, avail - 60)
        for i, ln in enumerate(packed):
            prefix = "缝份 SA: " if i == 0 else "          "
            rows.append((prefix + ln + (" cm" if i == len(packed) - 1 else ""),
                         8.5, C_MUTED, "400"))
    if p.note:
        for i, ln in enumerate(wrap_to_width(p.note.split("；"), "；", 8.5, avail)):
            rows.append((("▸ " if i == 0 else "   ") + ln, 8.5, C_FOLD, "400"))
    return rows


def caption_height(p: Piece, cell_w: float) -> float:
    return CAPTION_TOP + len(caption_lines(p, cell_w)) * CAPTION_LINE + 6


def draw_caption(c: Canvas, p: Piece, ox: float, oy: float, s: float,
                 cell_w: float):
    x0, _, _, y1 = p.bbox()
    bx = ox + x0 * s
    by = oy + y1 * s + CAPTION_TOP
    for i, (txt, size, col, weight) in enumerate(caption_lines(p, cell_w)):
        c.text(bx, by + i * CAPTION_LINE, txt, size=size, fill=col, weight=weight)


def layout(pieces: List[Piece], scale: float, max_w: float
           ) -> Tuple[List[Tuple[Piece, float, float]], float, float]:
    """
    Shelf-pack pieces left to right, wrapping into rows.

    Padding per piece has to reserve room for dimension lines, which sit
    *outside* the outline — otherwise annotations from neighbouring pieces
    collide and the drawing becomes unreadable.
    """
    placed, x, y, row_h, used_w = [], MARGIN, TITLE_H, 0.0, 0.0
    widths: Dict[int, float] = {}
    for p in pieces:
        x0, y0, x1, y1 = p.bbox()
        w, h = (x1 - x0) * scale, (y1 - y0) * scale
        # Bilingual labels are two lines tall and the English term is often
        # wider than the Chinese, so the gutters have to be roomier than a
        # single-line layout would need — otherwise neighbouring annotations
        # overlap and the numbers become unreadable.
        # Arc callouts add a ~30px leader plus a text plate on whichever side
        # they point, so both gutters need room beyond what the straight
        # dimension lines alone would require.
        pad_l = 112         # left: rotated vertical dims + left-pointing arcs
        pad_r = 150         # right: vertical dims + right-pointing arc plates
        pad_t = 44          # top: neckline dims
        # The caption sits below the piece and its height depends on how many
        # lines the seam list wraps to, so reserve the measured height rather
        # than a fixed band — a short guess is what let captions run into the
        # row beneath.
        cell_w = max(w + pad_l + pad_r, CAPTION_MIN_W + pad_l)
        pad_b = caption_height(p, cell_w) + 14
        cell_h = h + pad_t + pad_b
        if x + cell_w > max_w - MARGIN and placed:
            x = MARGIN
            y += row_h + GAP
            row_h = 0.0
        placed.append((p, x + pad_l - x0 * scale, y + pad_t - y0 * scale))
        widths[id(p)] = cell_w - pad_l
        x += cell_w + GAP
        row_h = max(row_h, cell_h)
        used_w = max(used_w, x)
    return placed, used_w + MARGIN, y + row_h + FOOTER_H, widths


def render(garment: str, category: str, size: str, pieces: List[Piece],
           scale_label: str, fit: str, fabric_width: int) -> str:
    scale = PX_PER_CM
    target_w = 1680
    placed, total_w, total_h, cell_widths = layout(pieces, scale, target_w)
    total_w = max(total_w, 980)

    c = Canvas()
    c.rect(0, 0, total_w, total_h, fill=C_BG)
    c.rect(0, TITLE_H - 14, total_w, total_h - TITLE_H - FOOTER_H + 28, fill="url(#grid)")

    # ── Title block ──
    c.text(MARGIN, 34, f"{garment} 裁片分解图", size=20, weight="700")
    c.text(MARGIN, 52, "Pattern Cutting Diagram", size=11.5, fill=C_MUTED,
           style="italic")
    c.text(MARGIN, 66, f"尺码 Size {size}  ·  比例 Scale {scale_label}  ·  "
                       f"版型 Fit {fit}  ·  幅宽 Fabric width {fabric_width}cm",
           size=10, fill=C_MUTED)
    c.text(total_w - MARGIN, 34,
           f"{len(pieces)} 种裁片 / 共 {sum(p.qty for p in pieces)} 片",
           size=12, fill=C_MUTED, anchor="end")
    c.text(total_w - MARGIN, 50,
           f"{len(pieces)} piece types / {sum(p.qty for p in pieces)} pcs total",
           size=9.5, fill=C_MUTED, anchor="end", style="italic")
    c.text(total_w - MARGIN, 66, "单位 cm，标注为净样尺寸（不含缝份）"
                                 " · Net dimensions, excl. seam allowance",
           size=9, fill=C_MUTED, anchor="end")
    c.line(MARGIN, 68, total_w - MARGIN, 68, C_OUTLINE, 1.2)

    # ── Pieces ──
    for p, ox, oy in placed:
        draw_cut_line(c, p, ox, oy, scale)
        c.path(piece_path_d(p, ox, oy, scale, scale), C_OUTLINE, 1.7, fill="#ffffff")
        # redraw net line over the white fill so it reads on top
        c.path(piece_path_d(p, ox, oy, scale, scale), C_OUTLINE, 1.7, fill="none")
        draw_fold(c, p, ox, oy, scale)
        draw_grain(c, p, ox, oy, scale)
        draw_arcs(c, p, ox, oy, scale)
        for d in spread_vertical_dims(p.dims):
            draw_dim(c, d, ox, oy, scale)

        draw_caption(c, p, ox, oy, scale, cell_w=cell_widths[id(p)])

    # ── Legend + footer ──
    fy = total_h - FOOTER_H + 34
    c.line(MARGIN, fy - 20, total_w - MARGIN, fy - 20, C_OUTLINE, 1.0)
    items = [
        (C_OUTLINE, None, "净样线 Net / sewing line"),
        (C_CUT, "7,4", "毛样线 Cutting line (net + SA)"),
        (C_FOLD, "12,3,3,3", "对折线 Cut on fold (no SA)"),
        (C_DIM, None, "尺寸标注 Dimension"),
        (C_GRAIN, None, "布纹方向 Grain"),
        (C_ARC, None, "弧长/凹势 Arc length & scoop"),
    ]
    lx = MARGIN
    for col, dash, lab in items:
        c.line(lx, fy, lx + 24, fy, col, 1.6, dash=dash)
        c.text(lx + 30, fy + 3.5, lab, size=9, fill=C_MUTED)
        lx += 32 + len(lab) * 6.0

    c.text(MARGIN, fy + 26,
           "⚠ 本图为 1:N 示意图，用于核对裁片数量、结构与尺寸关系；实际裁剪需按标注尺寸出 1:1 实样纸样。",
           size=9.5, fill=C_DIM)
    c.text(MARGIN, fy + 40,
           "⚠ Scaled reference drawing — verify piece count, structure and dimensions here, "
           "then grade a full-size (1:1) pattern before cutting.",
           size=8.8, fill=C_DIM, style="italic")
    c.text(MARGIN, fy + 56,
           "所有尺寸由尺码表按比例分配法计算得出，与规格书同源 · "
           "All dimensions computed from the size chart; same source as the spec sheet.",
           size=8.8, fill=C_MUTED)
    c.text(MARGIN, fy + 70,
           "由 clothes-design-skill / draw_pattern.py 生成", size=8.2, fill=C_MUTED)

    return c.svg(total_w, total_h)


def main():
    ap = argparse.ArgumentParser(
        description="Render a dimensioned pattern cutting diagram as SVG")
    ap.add_argument("--type", required=True, choices=sorted(DRAFTERS),
                    help="Garment type")
    ap.add_argument("--size", default="M", choices=list(SIZE_ORDER),
                    help="Size to draft (default: M)")
    ap.add_argument("--fit", default="regular",
                    choices=sorted(EASE), help="Fit/ease preset (default: regular)")
    ap.add_argument("--fabric-width", type=int, default=140)
    ap.add_argument("--scale-label", default="1:10",
                    help="Scale annotation printed in the title block")
    ap.add_argument("--output", "-o", required=True,
                    help="Output scaled-reference .svg path")
    ap.add_argument("--title", help="Override the garment title")
    args = ap.parse_args()
    category, drafter = DRAFTERS[args.type]
    measurements = SIZE_CHART[category][args.size]
    pieces = drafter(measurements, fit=args.fit)

    # The title block prints the fabric width as if it were verified. A value
    # that cannot hold the pieces would send a pattern maker to buy fabric the
    # panels do not fit on, so reject it instead of printing it.
    width_problems = validate_fabric_width(args.fabric_width, pieces)
    if width_problems:
        print("❌ 幅宽无效，拒绝出图：", file=sys.stderr)
        for p in width_problems:
            print(f"   - {p}", file=sys.stderr)
        return 1

    # Never emit a drawing whose labels disagree with its geometry — that is
    # precisely the defect that makes a cutting diagram unusable.
    problems = validate_pieces(pieces)
    if problems:
        print("❌ 标注与几何不一致，拒绝出图：", file=sys.stderr)
        for p in problems:
            print(f"   - {p}", file=sys.stderr)
        return 1

    title = args.title or args.type
    svg = render(title, category, args.size, pieces,
                 args.scale_label, args.fit, args.fabric_width)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg, encoding="utf-8")
    print(f"✅ {out}  ({len(pieces)} 种裁片 / 共 {sum(p.qty for p in pieces)} 片, "
          f"{len(svg)//1024}KB)", file=sys.stderr)
    for p in pieces:
        nw, nh = p.net_size()
        print(f"   {p.name:<6} ×{p.qty}  净样 {nw}×{nh}cm  "
              f"({len(p.dims)} 处标注)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
