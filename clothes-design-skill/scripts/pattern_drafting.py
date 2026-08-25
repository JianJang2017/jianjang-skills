#!/usr/bin/env python3
"""
Pattern drafting engine — turns a size-chart row into real pattern geometry.

Why this exists: a diffusion model cannot render dimension text reliably, and
the numbers it invents bear no arithmetic relation to the size chart, so an
AI-generated "cutting diagram" can never be worked from. Pattern geometry is
deterministic arithmetic, so it belongs in code. Every dimension this module
emits is computed from the same SIZE_CHART that drives the cost sheet.

Formulas follow proportional flat drafting (比例分配法) as used in Chinese
industry practice. Each constant is named and commented so a pattern maker can
retune the block to their house fit without reverse-engineering the code.

Coordinates are centimetres, x rightward, y downward. Pieces are drafted as
half-panels where the garment is symmetric (cut on fold or mirrored), which is
how a real marker is laid out.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any

# ─── Seam allowances (缝份, cm) ──────────────────────────────────────────────
# Industry defaults. Curves get less than straight edges because a wide
# allowance on a tight curve cannot be pressed flat.
SEAM_ALLOWANCE = {
    "shoulder": 1.0,   # 肩缝
    "side": 1.0,       # 侧缝
    "armhole": 1.0,    # 袖窿
    "neckline": 0.8,   # 领口（曲线，放小）
    "hem": 2.5,        # 下摆（折边需要量）
    "sleeve_hem": 2.0,  # 袖口折边
    "waist": 1.0,      # 腰缝
    "crotch": 1.0,     # 裆缝
    "center": 1.0,     # 前后中缝
    "fold": 0.0,       # 对折线不加缝份
}

# Seam names printed on the drawing. The factory reading this may not read
# Chinese, and "armhole 1.0" is unambiguous where a bare key is not.
SEAM_LABELS = {
    "shoulder": ("肩缝", "shoulder"),
    "side": ("侧缝", "side"),
    "armhole": ("袖窿", "armhole"),
    "neckline": ("领口", "neckline"),
    "hem": ("下摆", "hem"),
    "sleeve_hem": ("袖口", "sleeve hem"),
    "waist": ("腰缝", "waist"),
    "crotch": ("裆缝", "crotch"),
    "center": ("中缝", "centre"),
    "fold": ("对折", "fold"),
}


def seam_label(key: str) -> str:
    zh, en = SEAM_LABELS.get(key, (key, key))
    return f"{zh} {en}"


# Dimension-term glossary, resolved at render time by matching the Chinese term
# at the start of a Dim label. Kept as one table rather than an `en=` argument on
# every Dim so the ~70 call sites stay readable and the translations stay
# consistent — the same term can't end up rendered two different ways.
DIM_TERMS = {
    "1/4胸围+放松量": "1/4 bust + ease",
    "1/4胸围": "1/4 bust",
    "1/4腰围": "1/4 waist",
    "1/4臀围": "1/4 hip",
    "衣长": "Body length",
    "领宽": "Neck width",
    "前领深": "Front neck drop",
    "后领深": "Back neck drop",
    "领深": "Neck drop",
    "V领深": "V-neck drop",
    "袖窿深": "Armhole depth",
    "袖肥": "Sleeve width",
    "袖山高": "Cap height",
    "袖长": "Sleeve length",
    "袖底缝": "Underarm seam",
    "袖口": "Cuff width",
    "罗纹长": "Rib length",
    "对折宽": "Folded width",
    "前腰宽": "Front waist",
    "后腰宽": "Back waist",
    "前横裆宽": "Front thigh width",
    "后横裆宽": "Back thigh width",
    "前臀宽": "Front hip",
    "后臀宽": "Back hip",
    "立裆深": "Crotch depth",
    "裤外长": "Outseam",
    "下裆长": "Inseam",
    "前膝宽": "Front knee",
    "后膝宽": "Back knee",
    "前脚口": "Front leg opening",
    "后脚口": "Back leg opening",
    "腰头长": "Waistband length",
    "袋口宽": "Pocket opening",
    "袋深": "Pocket depth",
    "腰节长": "Waist height",
    "裙长": "Skirt length",
    "下摆宽": "Hem width",
    "大襟宽": "Overlap panel width",
    "小襟宽": "Under panel width",
    "搭门": "Overlap",
    "开叉高": "Side slit height",
    "领长": "Collar length",
    "带长": "Sash length",
}


ARC_TERMS = {
    "袖窿弧长": "Armhole arc",
    "前领口弧长": "Front neckline arc",
    "后领口弧长": "Back neckline arc",
    "领口弧长": "Neckline arc",
    "袖山前弧": "Front cap arc",
    "袖山后弧": "Back cap arc",
    "袖山弧长": "Sleeve cap arc",
    "前裆弧长": "Front crotch arc",
    "后裆弧长": "Back crotch arc",
    "臀弧长": "Hip curve arc",
    "袋底弧长": "Pocket base arc",
    "下摆弧长": "Hem curve arc",
    "凹势": "Scoop depth",
    "凸势": "Bow depth",
}


def path_arc_lengths(p: Piece) -> List[float]:
    """Arc length of every Q segment in a piece, in path order."""
    out, cur = [], None
    for seg in p.path:
        if seg[0] in ("M", "L"):
            cur = (seg[1], seg[2])
        elif seg[0] == "Q":
            out.append(quad_arc_length(cur, (seg[1], seg[2]), (seg[3], seg[4])))
            cur = (seg[3], seg[4])
    return out


def arc_length_by_label(p: Piece, zh_name: str) -> float:
    """
    Look up a computed arc length by its callout name.

    Safer than indexing `path_arc_lengths()` positionally: pieces differ in how
    many curves they have (a front bodice with a straight V neck has one, the
    back has two), so a fixed index reads a different curve on different pieces.
    """
    for a in p.arcs:
        if a.label.startswith(zh_name):
            return a.length
    return 0.0


def solve_sleeve_width(target_cap: float, cap_height: float,
                       front_ctrl: float, back_ctrl: float,
                       ctrl_y: float = 0.0,
                       lo: float = 4.0, hi: float = 120.0) -> float:
    """
    Find the half-sleeve width whose drawn cap arcs total `target_cap`.

    Why solve instead of using a ratio: the cap is drawn as two Bezier curves,
    so its true arc length depends on the control points, not just the width.
    Sizing the sleeve from a formula and then drawing a different curve is how
    a sleeve ends up 67% longer than the armhole it must sew into — the pattern
    looks plausible on paper and is unsewable in the factory. Measuring the
    curve we actually draw, then bisecting for the width that matches the
    armhole, keeps the two in agreement by construction.
    """
    def cap_len(sw: float) -> float:
        # ctrl_y lets a puff cap bow above the shoulder line (negative y).
        # Omitting it made the solver measure a flatter curve than the one
        # actually drawn, so the gather ratio came out ~5% high.
        p0 = (0.0, cap_height)
        a = quad_arc_length(p0, (sw * front_ctrl, ctrl_y), (sw, 0.0))
        b = quad_arc_length((sw, 0.0), (sw * back_ctrl, ctrl_y),
                            (sw * 2, cap_height))
        return a + b

    for _ in range(80):
        mid = (lo + hi) / 2
        if cap_len(mid) < target_cap:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def curve_callouts(p: Piece, names: Dict[int, Tuple[str, str]]) -> List[Arc]:
    """
    Build Arc callouts for the named path segments, computing arc length and
    scoop depth from the geometry so the printed numbers cannot drift from the
    drawn curve.

    `names` maps a path-segment index to (中文名, 'right'|'left') for the
    leader direction.
    """
    out: List[Arc] = []
    cursor = None
    for idx, seg in enumerate(p.path):
        if seg[0] == "M":
            cursor = (seg[1], seg[2])
        elif seg[0] == "L":
            cursor = (seg[1], seg[2])
        elif seg[0] == "Q":
            p0 = cursor
            p1, p2 = (seg[1], seg[2]), (seg[3], seg[4])
            if idx in names and p0 is not None:
                zh, side = names[idx]
                ln = quad_arc_length(p0, p1, p2)
                depth, _ = quad_max_depth(p0, p1, p2)
                out.append(Arc(
                    seg_index=idx,
                    label=f"{zh} {ln:.1f}",
                    length=ln,
                    en=ARC_TERMS.get(zh, ""),
                    depth_label=f"凹势 {depth:.1f}" if depth >= 0.35 else "",
                    side=side,
                ))
            cursor = p2
    return out


def dim_english(label: str) -> str:
    """
    Resolve the English term for a dimension label like "袖长 20".

    Matches longest-first so "1/4胸围+放松量" wins over "1/4胸围", and
    "前横裆宽" over any shorter prefix — otherwise a label would pick up the
    wrong translation and the drawing would contradict itself in English while
    reading correctly in Chinese.
    """
    for zh in sorted({**DIM_TERMS, **ARC_TERMS}, key=len, reverse=True):
        if label.startswith(zh):
            return {**DIM_TERMS, **ARC_TERMS}[zh]
    return ""


@dataclass
class Dim:
    """
    One dimension annotation: a measured span with its computed value.

    `label` holds the Chinese term plus the number, e.g. "袖长 20". `en` holds
    the English term alone, e.g. "Sleeve length" — the renderer stacks it under
    the Chinese so the same drawing serves a domestic pattern maker and an
    overseas factory. Keeping the number only in `label` means validate_pieces()
    has exactly one number to check per annotation.
    """
    kind: str                  # 'h' horizontal | 'v' vertical
    p1: Tuple[float, float]
    p2: Tuple[float, float]
    label: str
    offset: float = 2.0        # how far the dimension line sits off the piece
    value: Optional[float] = None   # None → derived from p1/p2 distance
    en: str = ""               # English term, rendered beneath the label

    def measured(self) -> float:
        if self.value is not None:
            return self.value
        if self.kind == "h":
            return abs(self.p2[0] - self.p1[0])
        return abs(self.p2[1] - self.p1[1])


@dataclass
class Arc:
    """
    A curve callout: arc length plus the offset from its chord ("凹势"/scoop).

    Endpoints alone do not define a curve. Two armholes with identical start and
    end points but different scoop depths sew into sleeves of different lengths,
    so a drawing that dimensions only the straight spans is not reproducible.
    Each Arc names the curve, states its true arc length, and gives the
    perpendicular depth at the deepest point — the two numbers a pattern maker
    actually uses to draw it with a curve ruler.

    `length` keeps the unrounded value. Downstream maths (matching a sleeve cap
    to an armhole) must use it rather than re-parsing the rounded number out of
    `label`, or the rounding error shows up as a wrong ease figure.
    """
    seg_index: int             # which path segment (index into Piece.path)
    label: str                 # 中文名 + 弧长, e.g. "袖窿弧长 21.4"
    length: float = 0.0        # exact arc length, unrounded
    en: str = ""
    depth_label: str = ""      # e.g. "凹势 1.8"
    side: str = "right"        # which way the callout leader points


def quad_points(p0, p1, p2, n: int = 64):
    """Sample a quadratic Bezier."""
    pts = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        pts.append((u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
                    u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]))
    return pts


def quad_arc_length(p0, p1, p2) -> float:
    pts = quad_points(p0, p1, p2)
    return sum(((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
               for a, b in zip(pts, pts[1:]))


def quad_max_depth(p0, p1, p2) -> Tuple[float, Tuple[float, float]]:
    """Greatest perpendicular distance from the chord, and where it occurs."""
    cx, cy = p2[0] - p0[0], p2[1] - p0[1]
    chord = (cx * cx + cy * cy) ** 0.5
    if chord < 1e-9:
        return 0.0, p0
    best, at = 0.0, p0
    for pt in quad_points(p0, p1, p2):
        d = abs(cx * (pt[1] - p0[1]) - cy * (pt[0] - p0[0])) / chord
        if d > best:
            best, at = d, pt
    return best, at


@dataclass
class Piece:
    """A pattern piece: outline, dimensions, and cutting metadata."""
    name: str                    # 中文名
    name_en: str
    qty: int
    path: List[Tuple]            # [('M',x,y), ('L',x,y), ('Q',cx,cy,x,y), ('Z',)]
    dims: List[Dim] = field(default_factory=list)
    arcs: List[Arc] = field(default_factory=list)
    grain: str = "vertical"      # 布纹方向: vertical 经向 | horizontal 纬向
    fold_edge: Optional[str] = None   # 'left' 对折边在左 | None
    seams: Dict[str, float] = field(default_factory=dict)  # edge → allowance
    note: str = ""

    def bbox(self) -> Tuple[float, float, float, float]:
        xs, ys = [], []
        for seg in self.path:
            if seg[0] == "M" or seg[0] == "L":
                xs.append(seg[1]); ys.append(seg[2])
            elif seg[0] == "Q":
                xs += [seg[1], seg[3]]; ys += [seg[2], seg[4]]
        return min(xs), min(ys), max(xs), max(ys)

    def net_size(self) -> Tuple[float, float]:
        x0, y0, x1, y1 = self.bbox()
        return round(x1 - x0, 1), round(y1 - y0, 1)

    def cut_size(self) -> Tuple[float, float]:
        """Net size plus the allowances that fall on each axis."""
        w, h = self.net_size()
        side = self.seams.get("side", SEAM_ALLOWANCE["side"])
        centre = 0.0 if self.fold_edge else self.seams.get("center", 0.0)
        top = self.seams.get("shoulder", self.seams.get("waist", 1.0))
        bottom = self.seams.get("hem", SEAM_ALLOWANCE["hem"])
        return round(w + side + centre, 1), round(h + top + bottom, 1)


def validate_pieces(pieces: List[Piece]) -> List[str]:
    """
    Check that every annotation agrees with the geometry it points at.

    This is the guard against the failure mode that makes a cutting diagram
    worthless: a label reading "袖长 20" on a span that actually measures 9.2cm.
    A pattern maker who trusts that number cuts the wrong piece. Because every
    label embeds its own number, we can re-measure the span and compare.
    """
    problems = []
    for p in pieces:
        for d in p.dims:
            # pull the trailing number out of the label, e.g. "袖长 20" → 20.0
            tokens = d.label.replace("+", " ").split()
            nums = []
            for t in tokens:
                try:
                    nums.append(float(t))
                except ValueError:
                    pass
            if not nums:
                continue
            stated = nums[-1]
            actual = d.measured()
            if abs(stated - actual) > 0.15:
                problems.append(
                    f"{p.name}/{d.label!r}: 标注 {stated:.1f} 但几何实测 {actual:.1f}"
                )
        # a piece with no dimensions cannot be cut from
        if not p.dims:
            problems.append(f"{p.name}: 没有任何尺寸标注")
        w, h = p.net_size()
        if w <= 0 or h <= 0:
            problems.append(f"{p.name}: 尺寸非正 ({w}×{h})")
    return problems


# ─── Ease (放松量, cm) ───────────────────────────────────────────────────────
# SIZE_CHART holds *body* measurements. A garment needs ease on top, and how
# much depends on fit intent. Without this the pattern would be skin-tight.
EASE = {
    "fitted":  {"bust": 6, "waist": 4, "hip": 4},    # 修身
    "regular": {"bust": 10, "waist": 8, "hip": 8},   # 常规
    "loose":   {"bust": 16, "waist": 14, "hip": 12},  # 宽松
}

# Knits stretch, so they need less ease than wovens — a knit tee drafted with
# woven ease hangs like a sack.
KNIT_EASE_FACTOR = 0.5


def _bust_quarter(bust: float, ease: float, knit: bool) -> float:
    """Quarter bust with ease — the working width of a half front/back panel."""
    e = ease * (KNIT_EASE_FACTOR if knit else 1.0)
    return (bust + e) / 4


def draft_tshirt(m: Dict[str, float], fit: str = "regular") -> List[Piece]:
    """
    T-shirt block: front, back, sleeve, neck rib.

    Drafting rules used here:
      armhole depth = bust/8 + 6.5   (袖窿深，比例分配法常用式)
      front neck drop = neck_width + 1  (前领深比领宽多 1cm)
      back neck drop = 2.0             (后领深固定浅量)
      neck width = bust/12 + 2.5
      shoulder slope = 4.0 cm over the shoulder span
    """
    bust, shoulder = m["bust"], m["shoulder"]
    length, sleeve_len = m["length"], m["sleeve"]

    ease = EASE[fit]["bust"]
    quarter = _bust_quarter(bust, ease, knit=True)

    armhole_depth = bust / 8 + 6.5
    neck_w = bust / 12 + 2.5
    front_neck_drop = neck_w + 1.0
    back_neck_drop = 2.0
    shoulder_slope = 4.0
    half_shoulder = shoulder / 2

    # Sleeve cap height ≈ 5/6 of armhole depth is the classic set-in ratio;
    # a tee uses a shallower cap for a relaxed, slightly dropped look.
    cap_height = armhole_depth * 0.62
    tee_sleeve_len = 20.0  # 短袖长（成品）

    pieces: List[Piece] = []

    # ── Front (cut on fold at centre front) ──
    front = Piece(
        name="前片", name_en="Front", qty=1,
        fold_edge="left", grain="vertical",
        seams={"shoulder": SEAM_ALLOWANCE["shoulder"], "side": SEAM_ALLOWANCE["side"],
               "armhole": SEAM_ALLOWANCE["armhole"], "neckline": SEAM_ALLOWANCE["neckline"],
               "hem": SEAM_ALLOWANCE["hem"]},
        note="连折裁，折边为前中线",
        path=[
            ("M", 0, front_neck_drop),
            ("Q", neck_w * 0.55, front_neck_drop, neck_w, 0),   # 前领口弧线
            ("L", half_shoulder, shoulder_slope),                # 肩线
            ("Q", half_shoulder + 1.2, armhole_depth * 0.55,
             quarter, armhole_depth),                            # 袖窿弧线
            ("L", quarter, length),                              # 侧缝
            ("L", 0, length),                                    # 下摆
            ("Z",),
        ],
    )
    front.dims = [
        Dim("h", (0, length), (quarter, length), f"1/4胸围+放松量 {quarter:.1f}", offset=3.5),
        Dim("v", (0, 0), (0, length), f"衣长 {length:.0f}", offset=-3.5),
        Dim("h", (0, 0), (neck_w, 0), f"领宽 {neck_w:.1f}", offset=-2.2),
        Dim("v", (0, 0), (0, front_neck_drop), f"前领深 {front_neck_drop:.1f}", offset=2.0),
        Dim("v", (quarter, 0), (quarter, armhole_depth), f"袖窿深 {armhole_depth:.1f}", offset=2.5),
    ]
    # Segment 1 is the neckline curve, segment 3 the armhole. Both need arc
    # length and scoop depth: the sleeve cap has to match the armhole arc, and
    # the rib has to match the neckline arc.
    front.arcs = curve_callouts(front, {1: ("前领口弧长", "left"),
                                        3: ("袖窿弧长", "right")})
    pieces.append(front)

    # ── Back (same block, shallower neckline) ──
    back = Piece(
        name="后片", name_en="Back", qty=1,
        fold_edge="left", grain="vertical",
        seams=dict(front.seams),
        note="连折裁，折边为后中线",
        path=[
            ("M", 0, back_neck_drop),
            ("Q", neck_w * 0.55, back_neck_drop, neck_w, 0),
            ("L", half_shoulder, shoulder_slope),
            ("Q", half_shoulder + 1.2, armhole_depth * 0.55, quarter, armhole_depth),
            ("L", quarter, length),
            ("L", 0, length),
            ("Z",),
        ],
    )
    back.dims = [
        Dim("h", (0, length), (quarter, length), f"1/4胸围+放松量 {quarter:.1f}", offset=3.5),
        Dim("v", (0, 0), (0, length), f"衣长 {length:.0f}", offset=-3.5),
        Dim("v", (0, 0), (0, back_neck_drop), f"后领深 {back_neck_drop:.1f}", offset=2.0),
        Dim("v", (quarter, 0), (quarter, armhole_depth), f"袖窿深 {armhole_depth:.1f}", offset=2.5),
    ]
    back.arcs = curve_callouts(back, {1: ("后领口弧长", "left"),
                                      3: ("袖窿弧长", "right")})
    pieces.append(back)

    # ── Sleeve (mirrored pair, drafted as a full sleeve) ──
    # Size the cap to the armholes we just drew, not to a formula. Ease of
    # +1.5cm total is the 吃势 that makes the sleeve head sit full.
    armhole_total = path_arc_lengths(front)[1] + path_arc_lengths(back)[1]
    cap_ease = 1.5
    sw = solve_sleeve_width(armhole_total + cap_ease, cap_height, 0.28, 1.72)
    cuff_width = sw * 0.86
    cap_len = sum(path_arc_lengths(Piece(
        name="_", name_en="_", qty=1,
        path=[("M", 0, cap_height), ("Q", sw * 0.28, 0, sw, 0),
              ("Q", sw * 1.72, 0, sw * 2, cap_height)])))

    sleeve = Piece(
        name="袖子", name_en="Sleeve", qty=2,
        grain="vertical",
        seams={"armhole": SEAM_ALLOWANCE["armhole"], "side": SEAM_ALLOWANCE["side"],
               "hem": SEAM_ALLOWANCE["sleeve_hem"]},
        note=f"左右对称各 1 片；袖山弧长 {cap_len:.1f}cm = 袖窿周长 "
             f"{armhole_total:.1f}cm + 吃势 {cap_ease:.1f}cm",
        path=[
            ("M", 0, cap_height),
            ("Q", sw * 0.28, 0, sw, 0),                    # 袖山前弧
            ("Q", sw * 1.72, 0, sw * 2, cap_height),       # 袖山后弧
            ("L", sw * 2 - (sw - cuff_width), tee_sleeve_len),   # 袖底缝
            ("L", sw - cuff_width, tee_sleeve_len),
            ("Z",),
        ],
    )
    sleeve.dims = [
        Dim("h", (0, cap_height), (sw * 2, cap_height), f"袖肥 {sw*2:.1f}", offset=3.0),
        Dim("v", (sw, 0), (sw, cap_height), f"袖山高 {cap_height:.1f}", offset=2.5),
        # 袖长 is measured from the cap top straight down to the hem, so the
        # span must start at y=0 — not at the underarm point, which is
        # cap_height lower and yields a different (shorter) number.
        Dim("v", (sw, 0), (sw, tee_sleeve_len), f"袖长 {tee_sleeve_len:.0f}", offset=-3.0),
        Dim("v", (0, cap_height), (0, tee_sleeve_len),
            f"袖底缝 {tee_sleeve_len - cap_height:.1f}", offset=-1.5),
        Dim("h", (sw - cuff_width, tee_sleeve_len),
            (sw * 2 - (sw - cuff_width), tee_sleeve_len), f"袖口 {cuff_width*2:.1f}", offset=3.0),
    ]
    sleeve.arcs = curve_callouts(sleeve, {1: ("袖山前弧", "left"),
                                          2: ("袖山后弧", "right")})
    pieces.append(sleeve)

    # ── Neck rib: length is the *stretched* neckline minus draw-in ──
    neck_circ = (neck_w * 2 * 1.06) + (front_neck_drop * 1.12) + (back_neck_drop * 1.12)
    rib_len = neck_circ * 0.88   # 罗纹拉伸缝合，需比领口短 12%
    rib_h = 2.0
    rib = Piece(
        name="领圈罗纹", name_en="Neck rib", qty=1,
        grain="horizontal",
        seams={"neckline": SEAM_ALLOWANCE["neckline"], "side": SEAM_ALLOWANCE["side"],
               "hem": 0.0, "shoulder": SEAM_ALLOWANCE["neckline"]},
        note=f"罗纹布，横纹裁（弹性沿长度方向）；成品领口周长 {neck_circ:.1f}cm",
        path=[("M", 0, 0), ("L", rib_len, 0), ("L", rib_len, rib_h * 2), ("L", 0, rib_h * 2), ("Z",)],
    )
    rib.dims = [
        Dim("h", (0, rib_h * 2), (rib_len, rib_h * 2), f"罗纹长 {rib_len:.1f}", offset=2.5),
        Dim("v", (0, 0), (0, rib_h * 2), f"对折宽 {rib_h*2:.1f}", offset=-2.5),
    ]
    pieces.append(rib)

    return pieces


def draft_pants(m: Dict[str, float], fit: str = "regular") -> List[Piece]:
    """
    Trouser block: front leg, back leg, waistband, pocket bag.

    Drafting rules:
      crotch depth = hip/4 + 2      (立裆深)
      front hip width = hip/4 - 1   (前片比后片窄 1cm，后片需包臀)
      back hip width = hip/4 + 1
      front crotch extension = hip/20   (前裆宽)
      back crotch extension = hip/10    (后裆宽，比前片大一倍)
      knee position = crotch_depth + (inseam * 0.48)
    """
    waist, hip = m["waist"], m["hip"]
    inseam, outseam = m["inseam"], m["outseam"]
    thigh, knee_c, hem_c = m["thigh"], m["knee"], m["hem"]

    e = EASE[fit]
    hip_w = hip + e["hip"]
    waist_w = waist + e["waist"]

    crotch_depth = hip_w / 4 + 2
    front_hip = hip_w / 4 - 1
    back_hip = hip_w / 4 + 1
    front_waist = waist_w / 4 - 1
    back_waist = waist_w / 4 + 1
    front_crotch_ext = hip_w / 20
    back_crotch_ext = hip_w / 10
    knee_y = crotch_depth + inseam * 0.48

    front_knee = knee_c / 2 - 0.5
    back_knee = knee_c / 2 + 0.5
    front_hem = hem_c / 2 - 0.5
    back_hem = hem_c / 2 + 0.5

    wb_h = 4.0
    seams_leg = {"waist": SEAM_ALLOWANCE["waist"], "side": SEAM_ALLOWANCE["side"],
                 "crotch": SEAM_ALLOWANCE["crotch"], "hem": SEAM_ALLOWANCE["hem"]}

    pieces: List[Piece] = []

    # ── Front leg ──
    fl = Piece(
        name="前片", name_en="Front leg", qty=2,
        grain="vertical", seams=dict(seams_leg),
        note="左右各 1 片；含前门襟位，烫迹线为经向基准",
        path=[
            ("M", 0, 0),                                    # 前中腰点
            ("L", front_waist, 0),                          # 腰口 → 侧缝
            ("Q", front_hip, crotch_depth * 0.5, front_hip, crotch_depth),  # 臀弧
            ("L", front_knee, knee_y),                      # 侧缝 → 膝
            ("L", front_hem, outseam),                      # 膝 → 脚口
            ("L", 0, outseam),                              # 脚口
            ("L", 0, knee_y),                               # 内缝 → 膝
            ("L", -front_crotch_ext, crotch_depth),         # 内缝 → 裆点
            ("Q", -front_crotch_ext * 0.4, crotch_depth * 0.62, 0, 0),  # 前裆弧
            ("Z",),
        ],
    )
    # Segment 2 is the hip curve down the side seam, segment 8 the crotch curve.
    # The crotch arc is the one a pattern maker cannot guess: front and back
    # crotch arcs must sum correctly or the rise binds when seated.
    fl.arcs = curve_callouts(fl, {2: ("臀弧长", "right"), 8: ("前裆弧长", "left")})
    fl.dims = [
        Dim("h", (0, 0), (front_waist, 0), f"前腰宽 {front_waist:.1f}", offset=-2.5),
        # This span sits at crotch level and includes the crotch extension, so
        # it is the thigh/横裆 width — NOT the hip width. The hip line lies
        # above the crotch line; labelling this "臀宽" would send a pattern
        # maker looking for hip/4 and finding a number ~5cm larger.
        Dim("h", (-front_crotch_ext, crotch_depth), (front_hip, crotch_depth),
            f"前横裆宽 {front_hip + front_crotch_ext:.1f}", offset=2.5),
        Dim("h", (0, crotch_depth * 0.66), (front_hip, crotch_depth * 0.66),
            f"前臀宽 {front_hip:.1f}", offset=-1.5, value=front_hip),
        Dim("v", (front_hip, 0), (front_hip, crotch_depth), f"立裆深 {crotch_depth:.1f}", offset=3.0),
        Dim("v", (front_hem, 0), (front_hem, outseam), f"裤外长 {outseam:.0f}", offset=6.0),
        Dim("v", (0, crotch_depth), (0, outseam), f"下裆长 {outseam - crotch_depth:.1f}", offset=-3.0),
        Dim("h", (0, knee_y), (front_knee, knee_y), f"前膝宽 {front_knee:.1f}", offset=2.0),
        Dim("h", (0, outseam), (front_hem, outseam), f"前脚口 {front_hem:.1f}", offset=2.5),
    ]
    pieces.append(fl)

    # ── Back leg (wider seat, deeper crotch curve) ──
    bl = Piece(
        name="后片", name_en="Back leg", qty=2,
        grain="vertical", seams=dict(seams_leg),
        note="左右各 1 片；后裆弧更深，后腰需起翘 1.5cm 以贴合坐姿",
        path=[
            ("M", 0, -1.5),                                 # 后中起翘
            ("L", back_waist, 0),
            ("Q", back_hip, crotch_depth * 0.5, back_hip, crotch_depth),
            ("L", back_knee, knee_y),
            ("L", back_hem, outseam),
            ("L", 0, outseam),
            ("L", 0, knee_y),
            ("L", -back_crotch_ext, crotch_depth),
            ("Q", -back_crotch_ext * 0.55, crotch_depth * 0.55, 0, -1.5),
            ("Z",),
        ],
    )
    bl.arcs = curve_callouts(bl, {2: ("臀弧长", "right"), 8: ("后裆弧长", "left")})
    bl.dims = [
        Dim("h", (0, 0), (back_waist, 0), f"后腰宽 {back_waist:.1f}", offset=-3.0),
        Dim("h", (-back_crotch_ext, crotch_depth), (back_hip, crotch_depth),
            f"后横裆宽 {back_hip + back_crotch_ext:.1f}", offset=2.5),
        Dim("h", (0, crotch_depth * 0.66), (back_hip, crotch_depth * 0.66),
            f"后臀宽 {back_hip:.1f}", offset=-1.5, value=back_hip),
        Dim("v", (back_hip, 0), (back_hip, crotch_depth), f"立裆深 {crotch_depth:.1f}", offset=3.0),
        Dim("v", (back_hem, 0), (back_hem, outseam), f"裤外长 {outseam:.0f}", offset=6.0),
        Dim("h", (0, knee_y), (back_knee, knee_y), f"后膝宽 {back_knee:.1f}", offset=2.0),
        Dim("h", (0, outseam), (back_hem, outseam), f"后脚口 {back_hem:.1f}", offset=2.5),
    ]
    pieces.append(bl)

    # ── Waistband ──
    wb_len = waist_w + 5.0   # +搭门余量
    wb = Piece(
        name="腰头", name_en="Waistband", qty=1,
        grain="horizontal",
        seams={"waist": SEAM_ALLOWANCE["waist"], "side": SEAM_ALLOWANCE["side"],
               "hem": SEAM_ALLOWANCE["waist"], "shoulder": SEAM_ALLOWANCE["waist"]},
        note=f"横纹裁，需粘衬；含搭门 5cm（成品腰围 {waist_w:.0f}cm）",
        path=[("M", 0, 0), ("L", wb_len, 0), ("L", wb_len, wb_h * 2), ("L", 0, wb_h * 2), ("Z",)],
    )
    wb.dims = [
        Dim("h", (0, wb_h * 2), (wb_len, wb_h * 2), f"腰头长 {wb_len:.1f}", offset=2.5),
        Dim("v", (0, 0), (0, wb_h * 2), f"对折宽 {wb_h*2:.1f}", offset=-2.5),
    ]
    pieces.append(wb)

    # ── Pocket bag ──
    pk_w, pk_h = 16.0, 30.0
    pk = Piece(
        name="口袋布", name_en="Pocket bag", qty=2,
        grain="vertical",
        seams={"side": 1.0, "hem": 1.0, "waist": 1.0, "shoulder": 1.0},
        note="袋布用薄棉；左右各 1 片",
        path=[("M", 0, 0), ("L", pk_w, 0), ("L", pk_w, pk_h - 4),
              ("Q", pk_w * 0.5, pk_h, 0, pk_h - 6), ("Z",)],
    )
    pk.dims = [
        Dim("h", (0, 0), (pk_w, 0), f"袋口宽 {pk_w:.1f}", offset=-2.2),
        Dim("v", (pk_w, 0), (pk_w, pk_h - 4), f"袋深 {pk_h-4:.1f}", offset=2.5),
    ]
    pk.arcs = curve_callouts(pk, {4: ("袋底弧长", "right")})
    pieces.append(pk)

    return pieces


def draft_dress(m: Dict[str, float], fit: str = "regular",
                waist_seam: bool = True) -> List[Piece]:
    """
    Dress block: front/back bodice, front/back skirt, sleeve.

    Drafted as a waist-seamed dress (分割式), which is how most dresses are cut —
    it lets the bodice fit the torso while the skirt flares independently.

    Rules:
      bodice length = waist_height ≈ length * 0.40   (腰节长占总长四成)
      bust dart intake = (bust - waist) / 8          (胸腰差的八分之一收为省)
      skirt flare = +8cm per panel at hem            (A字摆)
    """
    bust, waist, hip = m["bust"], m["waist"], m["hip"]
    shoulder, length = m["shoulder"], m["length"]

    e = EASE[fit]
    bust_q = (bust + e["bust"]) / 4
    waist_q = (waist + e["waist"]) / 4
    hip_q = (hip + e["hip"]) / 4

    bodice_len = length * 0.40
    skirt_len = length - bodice_len
    armhole_depth = bust / 8 + 6.5
    neck_w = bust / 12 + 2.5
    v_neck_drop = neck_w + 6.0     # V领比圆领深
    back_neck_drop = 2.0
    shoulder_slope = 4.0
    half_shoulder = shoulder / 2
    dart = (bust - waist) / 8
    hem_flare = 8.0

    pieces: List[Piece] = []

    bodice_seams = {"shoulder": SEAM_ALLOWANCE["shoulder"], "side": SEAM_ALLOWANCE["side"],
                    "armhole": SEAM_ALLOWANCE["armhole"], "neckline": SEAM_ALLOWANCE["neckline"],
                    "waist": SEAM_ALLOWANCE["waist"], "hem": SEAM_ALLOWANCE["waist"]}

    # ── Front bodice (V neck, cut on fold) ──
    fb = Piece(
        name="前上身", name_en="Front bodice", qty=1,
        fold_edge="left", grain="vertical", seams=dict(bodice_seams),
        note=f"连折裁；腰省收量 {dart:.1f}cm（省尖距 BP 点 2cm）",
        path=[
            ("M", 0, v_neck_drop),
            ("L", neck_w, 0),                                   # V 领直线
            ("L", half_shoulder, shoulder_slope),
            ("Q", half_shoulder + 1.2, armhole_depth * 0.55, bust_q, armhole_depth),
            ("L", waist_q, bodice_len),                          # 侧缝收腰
            ("L", 0, bodice_len),
            ("Z",),
        ],
    )
    fb.dims = [
        Dim("h", (0, armhole_depth), (bust_q, armhole_depth), f"1/4胸围 {bust_q:.1f}", offset=2.5),
        Dim("h", (0, bodice_len), (waist_q, bodice_len), f"1/4腰围 {waist_q:.1f}", offset=3.5),
        Dim("v", (0, 0), (0, bodice_len), f"腰节长 {bodice_len:.1f}", offset=-3.5),
        Dim("v", (0, 0), (0, v_neck_drop), f"V领深 {v_neck_drop:.1f}", offset=2.0),
        Dim("h", (0, 0), (neck_w, 0), f"领宽 {neck_w:.1f}", offset=-2.2),
        Dim("v", (bust_q, 0), (bust_q, armhole_depth), f"袖窿深 {armhole_depth:.1f}", offset=2.5),
    ]
    # V neck is drawn straight, so only the armhole (segment 3) is a curve here.
    fb.arcs = curve_callouts(fb, {3: ("袖窿弧长", "right")})
    pieces.append(fb)

    # ── Back bodice ──
    bb = Piece(
        name="后上身", name_en="Back bodice", qty=1,
        fold_edge="left", grain="vertical", seams=dict(bodice_seams),
        note="连折裁；后中装隐形拉链时改为断开、加缝份 1.5cm",
        path=[
            ("M", 0, back_neck_drop),
            ("Q", neck_w * 0.55, back_neck_drop, neck_w, 0),
            ("L", half_shoulder, shoulder_slope),
            ("Q", half_shoulder + 1.2, armhole_depth * 0.55, bust_q, armhole_depth),
            ("L", waist_q, bodice_len),
            ("L", 0, bodice_len),
            ("Z",),
        ],
    )
    bb.dims = [
        Dim("h", (0, armhole_depth), (bust_q, armhole_depth), f"1/4胸围 {bust_q:.1f}", offset=2.5),
        Dim("h", (0, bodice_len), (waist_q, bodice_len), f"1/4腰围 {waist_q:.1f}", offset=3.5),
        Dim("v", (0, 0), (0, bodice_len), f"腰节长 {bodice_len:.1f}", offset=-3.5),
        Dim("v", (0, 0), (0, back_neck_drop), f"后领深 {back_neck_drop:.1f}", offset=2.0),
    ]
    bb.arcs = curve_callouts(bb, {1: ("后领口弧长", "left"),
                                  3: ("袖窿弧长", "right")})
    pieces.append(bb)

    skirt_seams = {"waist": SEAM_ALLOWANCE["waist"], "side": SEAM_ALLOWANCE["side"],
                   "hem": SEAM_ALLOWANCE["hem"], "shoulder": SEAM_ALLOWANCE["waist"]}

    # ── Front / back skirt (A-line) ──
    for label, label_en in (("前裙片", "Front skirt"), ("后裙片", "Back skirt")):
        sk = Piece(
            name=label, name_en=label_en, qty=1,
            fold_edge="left", grain="vertical", seams=dict(skirt_seams),
            note=f"连折裁；下摆每片放摆 {hem_flare:.0f}cm 形成 A 字廓形",
            path=[
                ("M", 0, 0),
                ("L", waist_q, 0),                               # 腰口
                ("Q", hip_q, skirt_len * 0.22, hip_q, skirt_len * 0.34),  # 臀弧
                ("L", hip_q + hem_flare, skirt_len),             # 侧缝放摆
                ("L", 0, skirt_len),
                ("Z",),
            ],
        )
        sk.arcs = curve_callouts(sk, {2: ("臀弧长", "right")})
        sk.dims = [
            Dim("h", (0, 0), (waist_q, 0), f"1/4腰围 {waist_q:.1f}", offset=-2.5),
            Dim("h", (0, skirt_len * 0.34), (hip_q, skirt_len * 0.34),
                f"1/4臀围 {hip_q:.1f}", offset=-1.5, value=hip_q),
            Dim("h", (0, skirt_len), (hip_q + hem_flare, skirt_len),
                f"下摆宽 {hip_q + hem_flare:.1f}", offset=3.0),
            Dim("v", (0, 0), (0, skirt_len), f"裙长 {skirt_len:.1f}", offset=-3.5),
        ]
        pieces.append(sk)

    # ── Puff sleeve ──
    # A puff sleeve is deliberately longer than its armhole — the excess is
    # gathered. But the excess has to be a stated multiple of the *drawn*
    # armhole, not of a formula, or the gathers come out wrong.
    cap_height = armhole_depth * 0.72
    # Read the armhole off the labelled callouts rather than by list position:
    # the front bodice has one curve and the back has two, so a positional
    # index silently picks up the back neckline instead of its armhole.
    armhole_total = sum(arc_length_by_label(pc, "袖窿弧长") for pc in (fb, bb))
    puff_extra = 1.18            # 泡泡袖袖山抽褶量
    sw = solve_sleeve_width(armhole_total * puff_extra, cap_height,
                            0.22, 1.78, ctrl_y=-cap_height * 0.18)
    sleeve_len = 18.0
    cuff_w = sw * 0.78
    cap_len = sum(path_arc_lengths(Piece(
        name="_", name_en="_", qty=1,
        path=[("M", 0, cap_height),
              ("Q", sw * 0.22, -cap_height * 0.18, sw, 0),
              ("Q", sw * 1.78, -cap_height * 0.18, sw * 2, cap_height)])))

    sl = Piece(
        name="泡泡袖", name_en="Puff sleeve", qty=2,
        grain="vertical",
        seams={"armhole": SEAM_ALLOWANCE["armhole"], "side": SEAM_ALLOWANCE["side"],
               "hem": SEAM_ALLOWANCE["sleeve_hem"]},
        note=f"左右各 1 片；袖山弧长 {cap_len:.1f}cm = 袖窿 {armhole_total:.1f}cm "
             f"× {puff_extra:.2f}，多出 {cap_len - armhole_total:.1f}cm 抽褶",
        path=[
            ("M", 0, cap_height),
            ("Q", sw * 0.22, -cap_height * 0.18, sw, 0),
            ("Q", sw * 1.78, -cap_height * 0.18, sw * 2, cap_height),
            ("L", sw * 2 - (sw - cuff_w), sleeve_len),
            ("L", sw - cuff_w, sleeve_len),
            ("Z",),
        ],
    )
    sl.dims = [
        Dim("h", (0, cap_height), (sw * 2, cap_height), f"袖肥 {sw*2:.1f}", offset=3.0),
        Dim("v", (sw, 0), (sw, cap_height), f"袖山高 {cap_height:.1f}", offset=2.5),
        Dim("v", (sw, 0), (sw, sleeve_len), f"袖长 {sleeve_len:.0f}", offset=-3.5),
        Dim("h", (sw - cuff_w, sleeve_len), (sw * 2 - (sw - cuff_w), sleeve_len),
            f"袖口 {cuff_w*2:.1f}", offset=3.0),
    ]
    sl.arcs = curve_callouts(sl, {1: ("袖山前弧", "left"),
                                  2: ("袖山后弧", "right")})
    pieces.append(sl)

    return pieces


def draft_crossover_blouse(m: Dict[str, float], fit: str = "loose") -> List[Piece]:
    """
    交领上衣 (crossover / 交领) block: asymmetric left & right fronts, back,
    wide sleeve, collar band, sash.

    Structurally different from a tee, which is why it gets its own drafter:
    the two front panels are NOT mirror images — the 大襟 (left, worn on top)
    carries the full overlap while the 小襟 (right, underneath) is cut narrower.
    Cutting two identical fronts is the classic mistake here, so each is a
    separate piece with its own width.

    Rules:
      overlap (搭门) = bust/12      — how far the upper front crosses past centre
      collar band length = neckline run × 1.04
      sleeve is wide and straight (琵琶/宽袖), not a fitted set-in cap
    """
    bust, shoulder = m["bust"], m["shoulder"]
    length, sleeve_len = m["length"], m["sleeve"]

    ease = EASE[fit]["bust"]
    quarter = (bust + ease) / 4
    overlap = bust / 12

    armhole_depth = bust / 8 + 7.5     # 古风袖窿更深（宽松廓形）
    neck_w = bust / 12 + 2.5
    neck_drop = neck_w + 3.0
    shoulder_slope = 3.2               # 平肩，古风肩线更平
    half_shoulder = shoulder / 2 + 1.5  # 落肩量
    side_slit = length * 0.28          # 下摆开叉高度

    seams_body = {"shoulder": SEAM_ALLOWANCE["shoulder"], "side": SEAM_ALLOWANCE["side"],
                  "armhole": SEAM_ALLOWANCE["armhole"], "neckline": SEAM_ALLOWANCE["neckline"],
                  "hem": SEAM_ALLOWANCE["hem"], "center": SEAM_ALLOWANCE["center"]}

    pieces: List[Piece] = []

    # ── 大襟 front (upper layer, carries the overlap) ──
    w_big = quarter + overlap
    big = Piece(
        name="前襟左片(大襟)", name_en="Front L (overlap)", qty=1,
        grain="vertical", seams=dict(seams_body),
        note=f"压在上层；含搭门 {overlap:.1f}cm，斜襟自领口斜向右腋下；不可与小襟互换",
        path=[
            ("M", 0, neck_drop),                       # 领口起点（前中）
            ("L", neck_w, 0),                          # 斜领口
            ("L", half_shoulder, shoulder_slope),      # 肩线
            ("Q", half_shoulder + 1.5, armhole_depth * 0.55, quarter, armhole_depth),
            ("L", quarter, length),                    # 侧缝
            ("L", w_big, length),                      # 下摆（含搭门）
            ("L", w_big, neck_drop + 6),               # 搭门内边
            ("Z",),
        ],
    )
    big.arcs = curve_callouts(big, {3: ("袖窿弧长", "right")})
    big.dims = [
        Dim("h", (0, length), (w_big, length), f"大襟宽 {w_big:.1f}", offset=3.5),
        Dim("h", (quarter, length - 6), (w_big, length - 6), f"搭门 {overlap:.1f}", offset=-1.8,
            value=overlap),
        Dim("v", (0, 0), (0, length), f"衣长 {length:.0f}", offset=-3.5),
        Dim("v", (0, 0), (0, neck_drop), f"领深 {neck_drop:.1f}", offset=2.0),
        Dim("v", (quarter, 0), (quarter, armhole_depth), f"袖窿深 {armhole_depth:.1f}", offset=6.0),
        Dim("h", (0, 0), (neck_w, 0), f"领宽 {neck_w:.1f}", offset=-2.2),
    ]
    pieces.append(big)

    # ── 小襟 front (under layer, narrower) ──
    w_small = quarter - overlap * 0.4
    small = Piece(
        name="前襟右片(小襟)", name_en="Front R (under)", qty=1,
        grain="vertical", seams=dict(seams_body),
        note=f"搭在下层，比大襟窄 {w_big - w_small:.1f}cm；内侧缝系带固定",
        path=[
            ("M", 0, neck_drop * 0.62),
            ("L", neck_w * 0.8, 0),
            ("L", half_shoulder, shoulder_slope),
            ("Q", half_shoulder + 1.5, armhole_depth * 0.55, quarter, armhole_depth),
            ("L", quarter, length),
            ("L", 0, length),
            ("Z",),
        ],
    )
    small.arcs = curve_callouts(small, {3: ("袖窿弧长", "right")})
    small.dims = [
        Dim("h", (0, length), (quarter, length), f"小襟宽 {quarter:.1f}", offset=3.5),
        Dim("v", (0, 0), (0, length), f"衣长 {length:.0f}", offset=-3.5),
        Dim("v", (0, 0), (0, neck_drop * 0.62), f"领深 {neck_drop*0.62:.1f}", offset=2.0),
    ]
    pieces.append(small)

    # ── Back (cut on fold) ──
    back = Piece(
        name="后片", name_en="Back", qty=1,
        fold_edge="left", grain="vertical", seams=dict(seams_body),
        note=f"连折裁，折边为后中线；侧缝下摆开叉 {side_slit:.1f}cm",
        path=[
            ("M", 0, 2.0),
            ("Q", neck_w * 0.55, 2.0, neck_w, 0),
            ("L", half_shoulder, shoulder_slope),
            ("Q", half_shoulder + 1.5, armhole_depth * 0.55, quarter, armhole_depth),
            ("L", quarter, length),
            ("L", 0, length),
            ("Z",),
        ],
    )
    back.arcs = curve_callouts(back, {1: ("后领口弧长", "left"),
                                      3: ("袖窿弧长", "right")})
    back.dims = [
        Dim("h", (0, length), (quarter, length), f"1/4胸围+放松量 {quarter:.1f}", offset=3.5),
        Dim("v", (0, 0), (0, length), f"衣长 {length:.0f}", offset=-3.5),
        Dim("v", (quarter, length - side_slit), (quarter, length),
            f"开叉高 {side_slit:.1f}", offset=2.5),
        Dim("v", (0, 0), (0, 2.0), f"后领深 2.0", offset=2.0),
    ]
    pieces.append(back)

    # ── Wide sleeve (straight, not a fitted cap) ──
    cap = armhole_depth * 0.5
    # 宽袖同样要与实测袖窿吻合。古风宽袖吃势略大（+2.0cm），袖头更饱满。
    armhole_total = (arc_length_by_label(big, "袖窿弧长")
                     + arc_length_by_label(back, "袖窿弧长"))
    cap_ease_gf = 2.0
    sleeve_w = solve_sleeve_width(armhole_total + cap_ease_gf, cap, 0.45, 1.55)
    cuff = sleeve_w * 0.95             # 袖口略收，仍宽大
    sl_len = sleeve_len * 0.72
    sleeve = Piece(
        name="袖子", name_en="Wide sleeve", qty=2,
        grain="vertical",
        seams={"armhole": SEAM_ALLOWANCE["armhole"], "side": SEAM_ALLOWANCE["side"],
               "hem": SEAM_ALLOWANCE["sleeve_hem"]},
        note=f"左右各 1 片；宽袖直筒，袖山平缓（古风廓形）；"
             f"袖山弧长 = 袖窿 {armhole_total:.1f}cm + 吃势 {cap_ease_gf:.1f}cm",
        path=[
            ("M", 0, cap),
            ("Q", sleeve_w * 0.45, 0, sleeve_w, 0),
            ("Q", sleeve_w * 1.55, 0, sleeve_w * 2, cap),
            ("L", sleeve_w * 2 - (sleeve_w - cuff), sl_len),
            ("L", sleeve_w - cuff, sl_len),
            ("Z",),
        ],
    )
    sleeve.dims = [
        Dim("h", (0, cap), (sleeve_w * 2, cap), f"袖肥 {sleeve_w*2:.1f}", offset=3.0),
        Dim("v", (sleeve_w, 0), (sleeve_w, cap), f"袖山高 {cap:.1f}", offset=2.5),
        Dim("v", (sleeve_w, 0), (sleeve_w, sl_len), f"袖长 {sl_len:.1f}", offset=-3.5),
        Dim("h", (sleeve_w - cuff, sl_len), (sleeve_w * 2 - (sleeve_w - cuff), sl_len),
            f"袖口 {cuff*2:.1f}", offset=3.0),
    ]
    sleeve.arcs = curve_callouts(sleeve, {1: ("袖山前弧", "left"),
                                          2: ("袖山后弧", "right")})
    pieces.append(sleeve)

    # ── Collar band ──
    neck_run = (neck_w * 2 * 1.08) + neck_drop * 1.15 + 2.0 * 1.1
    collar_len = neck_run * 1.04 + overlap * 2
    collar_h = 3.0
    collar = Piece(
        name="领子", name_en="Collar band", qty=1,
        grain="horizontal",
        seams={"neckline": SEAM_ALLOWANCE["neckline"], "side": SEAM_ALLOWANCE["side"],
               "hem": SEAM_ALLOWANCE["neckline"], "shoulder": SEAM_ALLOWANCE["neckline"]},
        note=f"横纹裁，需粘衬；绕颈一周并延伸至搭门，成品领口弧长 {neck_run:.1f}cm",
        path=[("M", 0, 0), ("L", collar_len, 0), ("L", collar_len, collar_h * 2),
              ("L", 0, collar_h * 2), ("Z",)],
    )
    collar.dims = [
        Dim("h", (0, collar_h * 2), (collar_len, collar_h * 2), f"领长 {collar_len:.1f}", offset=2.5),
        Dim("v", (0, 0), (0, collar_h * 2), f"对折宽 {collar_h*2:.1f}", offset=-2.5),
    ]
    pieces.append(collar)

    # ── Sash ──
    sash_len, sash_h = 190.0, 4.0
    sash = Piece(
        name="腰带", name_en="Sash", qty=1,
        grain="vertical",
        seams={"side": 1.0, "hem": 1.0, "waist": 1.0, "shoulder": 1.0},
        note="可拼接裁；对折缝合后翻正，两端收尖",
        path=[("M", 0, 0), ("L", sash_len, 0), ("L", sash_len, sash_h * 2),
              ("L", 0, sash_h * 2), ("Z",)],
    )
    sash.dims = [
        Dim("h", (0, sash_h * 2), (sash_len, sash_h * 2), f"带长 {sash_len:.0f}", offset=2.5),
        Dim("v", (0, 0), (0, sash_h * 2), f"对折宽 {sash_h*2:.1f}", offset=-2.5),
    ]
    pieces.append(sash)

    return pieces


DRAFTERS = {
    "t-shirt": ("tops", draft_tshirt),
    "shirt": ("tops", draft_tshirt),
    "blouse": ("tops", draft_tshirt),
    "crossover-blouse": ("tops", draft_crossover_blouse),
    "pants": ("bottoms", draft_pants),
    "jeans": ("bottoms", draft_pants),
    "dress": ("dresses", draft_dress),
}
