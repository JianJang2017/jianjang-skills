#!/usr/bin/env python3
"""
Garment specification calculator for clothes-design-skill

Given a garment spec (type, fabric, target size), outputs:
- Size grading table (XS through 3XL with measurements)
- Fabric consumption calculation (based on pattern layout)
- Cost breakdown (fabric, notions, labor, overhead)
- Pattern piece layout diagram specs

All calculations are deterministic — no guesswork on measurements or costs.
"""

import json
import sys
import argparse
from typing import Dict, List, Any

# ─── Size Standards ─────────────────────────────────────────────────────────
# International sizing with grading increments
# Base measurements in cm

SIZE_CHART = {
    "tops": {
        "XS": {"bust": 80, "waist": 62, "hip": 86, "shoulder": 36, "sleeve": 58, "length": 60},
        "S":  {"bust": 84, "waist": 66, "hip": 90, "shoulder": 37, "sleeve": 59, "length": 62},
        "M":  {"bust": 88, "waist": 70, "hip": 94, "shoulder": 38, "sleeve": 60, "length": 64},
        "L":  {"bust": 92, "waist": 74, "hip": 98, "shoulder": 39, "sleeve": 61, "length": 66},
        "XL": {"bust": 96, "waist": 78, "hip": 102, "shoulder": 40, "sleeve": 62, "length": 68},
        "XXL": {"bust": 100, "waist": 82, "hip": 106, "shoulder": 41, "sleeve": 63, "length": 70},
        "XXXL": {"bust": 104, "waist": 86, "hip": 110, "shoulder": 42, "sleeve": 64, "length": 72},
    },
    "bottoms": {
        "XS": {"waist": 62, "hip": 86, "inseam": 74, "outseam": 98, "thigh": 52, "knee": 36, "hem": 32},
        "S":  {"waist": 66, "hip": 90, "inseam": 76, "outseam": 100, "thigh": 54, "knee": 37, "hem": 33},
        "M":  {"waist": 70, "hip": 94, "inseam": 78, "outseam": 102, "thigh": 56, "knee": 38, "hem": 34},
        "L":  {"waist": 74, "hip": 98, "inseam": 80, "outseam": 104, "thigh": 58, "knee": 39, "hem": 35},
        "XL": {"waist": 78, "hip": 102, "inseam": 82, "outseam": 106, "thigh": 60, "knee": 40, "hem": 36},
        "XXL": {"waist": 82, "hip": 106, "inseam": 84, "outseam": 108, "thigh": 62, "knee": 41, "hem": 37},
        "XXXL": {"waist": 86, "hip": 110, "inseam": 86, "outseam": 110, "thigh": 64, "knee": 42, "hem": 38},
    },
    "dresses": {
        "XS": {"bust": 80, "waist": 62, "hip": 86, "shoulder": 36, "sleeve": 58, "length": 95},
        "S":  {"bust": 84, "waist": 66, "hip": 90, "shoulder": 37, "sleeve": 59, "length": 97},
        "M":  {"bust": 88, "waist": 70, "hip": 94, "shoulder": 38, "sleeve": 60, "length": 99},
        "L":  {"bust": 92, "waist": 74, "hip": 98, "shoulder": 39, "sleeve": 61, "length": 101},
        "XL": {"bust": 96, "waist": 78, "hip": 102, "shoulder": 40, "sleeve": 62, "length": 103},
        "XXL": {"bust": 100, "waist": 82, "hip": 106, "shoulder": 41, "sleeve": 63, "length": 105},
        "XXXL": {"bust": 104, "waist": 86, "hip": 110, "shoulder": 42, "sleeve": 64, "length": 107},
    },
}

# Canonical smallest-to-largest order, used to keep output ordering stable and
# to pick a middle reference size when M is not among the requested sizes.
SIZE_ORDER = ("XS", "S", "M", "L", "XL", "XXL", "XXXL")

# Measurement-point labels. A spec sheet gets read by a domestic pattern maker
# and by an overseas factory off the same PDF, so each column carries both the
# Chinese term and the English one. Bare keys like "inseam" or "hem" are the
# ambiguous ones — "hem" can mean hem width or hem allowance, and 下摆围 vs
# 脚口 differ by garment, so the pairing removes the guesswork.
MEASUREMENT_LABELS = {
    "bust":     ("胸围", "Bust"),
    "waist":    ("腰围", "Waist"),
    "hip":      ("臀围", "Hip"),
    "shoulder": ("肩宽", "Shoulder"),
    "sleeve":   ("袖长", "Sleeve length"),
    "length":   ("衣长", "Body length"),
    "inseam":   ("下裆长", "Inseam"),
    "outseam":  ("裤外长", "Outseam"),
    "thigh":    ("大腿围", "Thigh"),
    "knee":     ("膝围", "Knee"),
    "hem":      ("脚口围", "Leg opening"),
}


def label_for(key: str, style: str = "both") -> str:
    """Render a measurement key as a table heading."""
    zh, en = MEASUREMENT_LABELS.get(key, (key, key))
    if style == "zh":
        return zh
    if style == "en":
        return en
    if style == "key":
        return key
    return f"{zh}<br>{en}"

# ─── Fabric Consumption ─────────────────────────────────────────────────────
# Pattern efficiency by garment type (fabric utilization %)
# Formula: total_fabric = (pattern_area / efficiency) + seam_allowance + shrinkage_buffer

PATTERN_EFFICIENCY = {
    "t-shirt": 0.75,
    "shirt": 0.72,
    "blouse": 0.70,
    "crossover-blouse": 0.66,   # 大襟/小襟不对称，且需裁长腰带，排料更零碎
    "dress": 0.68,
    "skirt": 0.80,
    "pants": 0.65,
    "jeans": 0.65,
    "jacket": 0.60,
    "coat": 0.58,
}

# Standard fabric widths (cm)
FABRIC_WIDTHS = {
    "narrow": 110,   # 窄幅：衬衫、棉麻
    "medium": 140,   # 中幅：针织、梭织
    "wide": 150,     # 宽幅：外套、裙装
}

# Narrowest width a garment panel can realistically be cut from. Anything
# below this is an input error (typo, or metres entered instead of cm), not a
# fabric to be quoted on.
MIN_PLAUSIBLE_FABRIC_WIDTH = 60

def calculate_fabric_consumption(garment_type: str, size: str, category: str, fabric_width: int = 140) -> Dict[str, Any]:
    """Calculate fabric yardage needed for one garment"""

    measurements = SIZE_CHART[category][size]

    # A missing efficiency entry silently reshapes the yardage number, so the
    # fallback has to be reported the same way the cost fallbacks are. Without
    # this, an unsupported style quotes fabric as if it had been measured.
    assumptions = []
    if garment_type in PATTERN_EFFICIENCY:
        efficiency = PATTERN_EFFICIENCY[garment_type]
    else:
        efficiency = 0.70
        assumptions.append(
            f"款式 '{garment_type}' 不在排料效率库中，按通用值 70% 估算"
        )

    # Estimate pattern area (simplified: length × max(bust/hip/waist) × 2 for front+back)
    if category == "tops":
        pattern_length = measurements["length"] + measurements["sleeve"]
        pattern_width = max(measurements["bust"], measurements["hip"]) * 2
    elif category == "bottoms":
        pattern_length = measurements["outseam"]
        pattern_width = measurements["hip"] * 2
    else:  # dresses
        pattern_length = measurements["length"] + measurements["sleeve"]
        pattern_width = max(measurements["bust"], measurements["hip"]) * 2

    # Raw pattern area
    pattern_area_cm2 = pattern_length * pattern_width

    # Account for efficiency, seam allowance (10% extra), shrinkage (5% extra)
    total_area_cm2 = pattern_area_cm2 / efficiency * 1.15

    # Convert to fabric length given width
    fabric_length_cm = total_area_cm2 / fabric_width
    fabric_length_m = fabric_length_cm / 100

    # Pattern pieces count (estimate)
    pieces = {
        "t-shirt": 4,   # front, back, 2 sleeves
        "shirt": 8,     # front x2, back, collar, 2 sleeves, 2 cuffs
        "blouse": 7,
        "crossover-blouse": 7,   # 大襟, 小襟, 后片, 袖x2, 领, 腰带
        "dress": 6,
        "skirt": 4,
        "pants": 6,     # front x2, back x2, waistband, pockets
        "jeans": 7,     # front x2, back x2, waistband, pockets x2
        "jacket": 12,
        "coat": 14,
    }

    return {
        "fabric_length_m": round(fabric_length_m, 2),
        "fabric_width_cm": fabric_width,
        "pattern_pieces": pieces.get(garment_type, 6),
        "efficiency_rate": efficiency,
        "total_area_cm2": int(total_area_cm2),
        "assumptions": assumptions,
    }

# ─── Cost Breakdown ─────────────────────────────────────────────────────────

FABRIC_PRICES_PER_METER = {
    "cotton": 25,        # 纯棉
    "linen": 40,         # 亚麻
    "silk": 120,         # 真丝
    "wool": 80,          # 羊毛
    "polyester": 18,     # 涤纶
    "blend": 30,         # 混纺
    "knit": 22,          # 针织
    "denim": 35,         # 牛仔
}

NOTIONS_BASE_COST = {
    "t-shirt": 5,        # thread, labels
    "shirt": 15,         # buttons, thread, interfacing, labels
    "blouse": 12,
    "crossover-blouse": 16,   # 系带/暗扣、滚边、腰带用料
    "dress": 20,         # zipper, thread, lining, labels
    "skirt": 15,
    "pants": 18,         # zipper, button, thread, labels
    "jeans": 26,         # 铆钉、金属钮、拉链、双色线、皮标
    "jacket": 35,        # lining, zipper, buttons, shoulder pads
    "coat": 50,
}

# Labor hours by complexity
LABOR_HOURS = {
    "t-shirt": 2.5,
    "shirt": 4.0,
    "blouse": 3.5,
    "crossover-blouse": 4.5,   # 交领对位、滚边、腰带
    "dress": 5.0,
    "skirt": 3.0,
    "pants": 4.5,
    "jeans": 5.5,        # 双线明缝、打枣、铆钉
    "jacket": 8.0,
    "coat": 10.0,
}

LABOR_RATE_PER_HOUR = 30  # CNY

def calculate_cost(garment_type: str, fabric_type: str, fabric_length_m: float) -> Dict[str, Any]:
    """Calculate total garment cost breakdown.

    Unknown fabric/garment types fall back to mid-range defaults rather than
    failing, so an unusual style ("hanfu", "bamboo") still produces a usable
    estimate. The fallback is recorded in `assumptions` so the caller can tell
    the user which numbers are real lookups and which are guesses.
    """

    assumptions = []

    if fabric_type in FABRIC_PRICES_PER_METER:
        fabric_price = FABRIC_PRICES_PER_METER[fabric_type]
    else:
        fabric_price = 30
        assumptions.append(
            f"面料 '{fabric_type}' 不在价格库中，按中档 ¥30/米 估算"
        )

    fabric_cost = fabric_price * fabric_length_m

    if garment_type in NOTIONS_BASE_COST:
        notions_cost = NOTIONS_BASE_COST[garment_type]
    else:
        notions_cost = 15
        assumptions.append(f"款式 '{garment_type}' 辅料成本按通用值 ¥15 估算")

    if garment_type in LABOR_HOURS:
        labor_hours = LABOR_HOURS[garment_type]
    else:
        labor_hours = 4.0
        assumptions.append(f"款式 '{garment_type}' 工时按通用值 4.0 小时估算")

    labor_cost = labor_hours * LABOR_RATE_PER_HOUR

    # Overhead (pattern-making, QC, packaging: 15% of direct costs)
    direct_cost = fabric_cost + notions_cost + labor_cost
    overhead = direct_cost * 0.15

    total_cost = direct_cost + overhead

    return {
        "fabric_cost": round(fabric_cost, 2),
        "fabric_price_per_meter": fabric_price,
        "notions_cost": notions_cost,
        "labor_cost": round(labor_cost, 2),
        "labor_hours": labor_hours,
        "labor_rate_per_hour": LABOR_RATE_PER_HOUR,
        "overhead": round(overhead, 2),
        "overhead_rate": 0.15,
        "total_cost": round(total_cost, 2),
        "assumptions": assumptions,
    }

# ─── Main Interface ─────────────────────────────────────────────────────────

def generate_garment_spec(
    garment_type: str,
    category: str,
    fabric_type: str,
    fabric_width: int = 140,
    sizes: List[str] = None
) -> Dict[str, Any]:
    """Generate complete garment specification"""

    if category not in SIZE_CHART:
        raise ValueError(
            f"未知品类 '{category}'，可选：{', '.join(SIZE_CHART)}"
        )

    # Fabric width is a divisor. A non-positive value either crashes on the
    # division or silently flips yardage and every cost line negative, which
    # reads as an authoritative quote for fabric that cannot exist.
    if fabric_width <= 0:
        raise ValueError(
            f"幅宽必须为正数，收到 {fabric_width}cm"
        )
    if fabric_width < MIN_PLAUSIBLE_FABRIC_WIDTH:
        raise ValueError(
            f"幅宽 {fabric_width}cm 小于最窄可用门幅 "
            f"{MIN_PLAUSIBLE_FABRIC_WIDTH}cm，无法排料；请确认输入"
        )

    available = SIZE_CHART[category]

    if sizes is None:
        sizes = list(SIZE_ORDER)

    # A typo in a size name must not pass silently — the caller would get a
    # spec whose size table is missing rows (or empty) while the fabric and
    # cost figures still look authoritative.
    unknown = [s for s in sizes if s not in available]
    if unknown:
        raise ValueError(
            f"未知尺码 {unknown}，可选：{', '.join(SIZE_ORDER)}"
        )

    # Keep the canonical XS→XXXL order regardless of the order given on the CLI.
    ordered = [s for s in SIZE_ORDER if s in sizes]
    size_table = {s: available[s] for s in ordered}

    # Fabric and cost are quoted for one representative size. Default to M, but
    # when M was not requested fall back to the middle of the requested range —
    # quoting M's yardage for an XXXL-only order would understate both.
    reference_size = "M" if "M" in size_table else ordered[len(ordered) // 2]

    fabric_calc = calculate_fabric_consumption(
        garment_type, reference_size, category, fabric_width
    )
    cost_calc = calculate_cost(
        garment_type, fabric_type, fabric_calc["fabric_length_m"]
    )

    return {
        "garment_type": garment_type,
        "category": category,
        "fabric_type": fabric_type,
        "reference_size": reference_size,
        "size_table": size_table,
        "fabric_consumption": fabric_calc,
        "cost_breakdown": cost_calc,
    }

def format_markdown_output(spec: Dict[str, Any]) -> str:
    """Format spec as readable markdown"""

    ref = spec['reference_size']
    size_table = spec['size_table']

    # Column headers come from any row — take the first, since every size in a
    # category shares the same measurement points.
    columns = list(next(iter(size_table.values())).keys())

    heads = [label_for(c, "both") for c in columns]

    md = f"""# {spec['garment_type'].title()} 设计规格书 / Spec Sheet

## 基本信息 / Overview
- **款式类型 Garment**: {spec['garment_type']}
- **面料 Fabric**: {spec['fabric_type']}
- **类别 Category**: {spec['category']}
- **参考尺码 Reference size**: {ref}（用量与成本以此码计算 / yardage & cost quoted for this size）

## 尺码表 / Size chart（单位 cm / all measurements in cm）

| 尺码<br>Size | {" | ".join(heads)} |
|------|{"|".join(["---"] * len(columns))}|
"""

    for size, measurements in size_table.items():
        values = " | ".join(str(measurements[c]) for c in columns)
        marker = " ←参考" if size == ref else ""
        md += f"| **{size}**{marker} | {values} |\n"

    # Spell the columns out once in plain text too. The <br> in the headers
    # renders as a line break in HTML but shows as literal markup in a plain
    # text viewer, so this list is what stays readable everywhere.
    md += "\n**测量点说明 / Measurement points:**\n\n"
    for c in columns:
        zh, en = MEASUREMENT_LABELS.get(c, (c, c))
        md += f"- `{c}` — {zh} / {en}\n"

    fc = spec['fabric_consumption']
    md += f"""
## 面料用量 / Fabric consumption（参考 {ref} 码 / for size {ref}）

| 项目 / Item | 数值 / Value |
|------|------|
| 总用量 Total length | {fc['fabric_length_m']} 米 / m |
| 面料幅宽 Fabric width | {fc['fabric_width_cm']} cm |
| 裁片数量 Pattern pieces | {fc['pattern_pieces']} 片 / pcs |
| 排料效率 Marker efficiency | {fc['efficiency_rate'] * 100:.0f}% |
| 总面积 Total area | {fc['total_area_cm2']} cm² |

"""

    cc = spec['cost_breakdown']
    md += f"""## 成本核算 / Cost breakdown（参考 {ref} 码 / for size {ref}）

| 项目 / Item | 金额 / Amount (CNY) | 说明 / Basis |
|------|-----------|------|
| 面料 Fabric | ¥{cc['fabric_cost']:.2f} | ¥{cc['fabric_price_per_meter']}/米 × {fc['fabric_length_m']} 米 |
| 辅料 Notions | ¥{cc['notions_cost']:.2f} | 拉链/纽扣/织唛/吊牌 zipper, buttons, labels |
| 人工 Labour | ¥{cc['labor_cost']:.2f} | {cc['labor_hours']} 小时 h × ¥{cc['labor_rate_per_hour']}/小时 h |
| 管理费 Overhead | ¥{cc['overhead']:.2f} | 直接成本的 {cc['overhead_rate'] * 100:.0f}% / {cc['overhead_rate'] * 100:.0f}% of direct cost |
| **合计 Total** | **¥{cc['total_cost']:.2f}** | 单件出厂成本，不含利润与物流 / ex-works, excl. margin & freight |
"""

    # Yardage and cost each carry their own fallbacks. Rendering only the cost
    # ones would drop a marker-efficiency guess from the deliverable while the
    # yardage table still reads as measured.
    all_assumptions = fc.get('assumptions', []) + cc['assumptions']
    if all_assumptions:
        md += "\n### ⚠️ 估算假设 / Estimation assumptions\n\n"
        for note in all_assumptions:
            md += f"- {note}\n"

    md += """
> 用量基于标准版型和排料效率估算，实际采购前建议让打版师核一次排料。
> 成本按市场均价计算，受批量、地域、工艺影响，详见 `references/cost-model.md`。
>
> Yardage is estimated from a standard block and marker efficiency — have a
> pattern maker verify the marker before purchasing. Costs use average market
> rates and vary with order quantity, region, and construction.

---

*本规格书由 clothes-design-skill 自动生成 / Generated by clothes-design-skill*
"""

    return md

def main():
    parser = argparse.ArgumentParser(description="Calculate garment specifications")
    parser.add_argument("--type", required=True, help="Garment type (t-shirt, dress, pants, etc.)")
    parser.add_argument("--category", required=True, choices=["tops", "bottoms", "dresses"],
                        help="Garment category")
    parser.add_argument("--fabric", required=True, help="Fabric type (cotton, silk, denim, etc.)")
    parser.add_argument("--fabric-width", type=int, default=140, help="Fabric width in cm")
    parser.add_argument("--sizes", nargs="+", default=None, help="Sizes to include (default: all)")
    parser.add_argument("--output", "-o", help="Output markdown file")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of markdown")

    args = parser.parse_args()

    try:
        spec = generate_garment_spec(
            garment_type=args.type,
            category=args.category,
            fabric_type=args.fabric,
            fabric_width=args.fabric_width,
            sizes=args.sizes,
        )
    except ValueError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 1

    if args.json:
        output = json.dumps(spec, indent=2, ensure_ascii=False)
    else:
        output = format_markdown_output(spec)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"✅ Specification written to {args.output}", file=sys.stderr)
    else:
        print(output)

    return 0

if __name__ == "__main__":
    sys.exit(main())
