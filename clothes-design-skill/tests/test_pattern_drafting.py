#!/usr/bin/env python3
"""
Tests for the pattern drafting engine.

The defect these guard against: a cutting diagram whose printed dimensions do
not follow from the size chart, or whose labels contradict the geometry they
annotate. Either makes the drawing impossible to work from, and both are
invisible unless checked arithmetically.
"""

import re
import subprocess
import sys
import xml.dom.minidom
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from calculate_garment import SIZE_CHART, SIZE_ORDER          # noqa: E402
from pattern_drafting import (                                 # noqa: E402
    DRAFTERS, EASE, KNIT_EASE_FACTOR, validate_pieces, Dim,
)

fails = []


def check(name, cond, detail=""):
    print(f"{'✅' if cond else '❌'} {name}" + (f"  — {detail}" if detail and not cond else ""))
    if not cond:
        fails.append(name)


print("=== every garment × every size: labels agree with geometry ===")
total = 0
for gt, (cat, fn) in sorted(DRAFTERS.items()):
    bad = []
    for s in SIZE_ORDER:
        probs = validate_pieces(fn(SIZE_CHART[cat][s]))
        total += 1
        if probs:
            bad += [f"{s}: {p}" for p in probs]
    check(f"{gt} ({len(SIZE_ORDER)} sizes)", not bad, "; ".join(bad[:3]))
print(f"   {total} garment/size combinations checked")

print()
print("=== dimensions close back to the size chart ===")
m = SIZE_CHART["tops"]["M"]
tee = DRAFTERS["t-shirt"][1](m)
q = [d for d in tee[0].dims if "1/4胸围" in d.label][0].measured()
knit_ease = EASE["regular"]["bust"] * KNIT_EASE_FACTOR
check("tee quarter-bust ×4 == body bust + knit ease",
      abs(q * 4 - (m["bust"] + knit_ease)) < 0.1,
      f"{q*4:.1f} vs {m['bust']+knit_ease:.1f}")

mb = SIZE_CHART["bottoms"]["M"]
pants = DRAFTERS["pants"][1](mb)
fh = [d for d in pants[0].dims if d.label.startswith("前臀宽")][0].measured()
bh = [d for d in pants[1].dims if d.label.startswith("后臀宽")][0].measured()
check("pants (front+back hip) ×2 == body hip + ease",
      abs((fh + bh) * 2 - (mb["hip"] + EASE["regular"]["hip"])) < 0.1,
      f"{(fh+bh)*2:.1f} vs {mb['hip']+EASE['regular']['hip']}")

md = SIZE_CHART["dresses"]["M"]
dress = DRAFTERS["dress"][1](md)
w = [d for d in dress[0].dims if "1/4腰围" in d.label][0].measured()
check("dress quarter-waist ×4 == body waist + ease",
      abs(w * 4 - (md["waist"] + EASE["regular"]["waist"])) < 0.1,
      f"{w*4:.1f} vs {md['waist']+EASE['regular']['waist']}")

print()
print("=== thigh line is not mislabelled as hip line ===")
# 横裆宽 (at crotch level, includes crotch extension) must be strictly wider
# than 臀宽 (at hip level). Conflating them was a real bug.
for side, piece in (("front", pants[0]), ("back", pants[1])):
    tl = [d for d in piece.dims if "横裆宽" in d.label]
    hl = [d for d in piece.dims if d.label.startswith(("前臀宽", "后臀宽"))]
    check(f"{side}: has both 横裆宽 and 臀宽 labels", len(tl) == 1 and len(hl) == 1)
    if tl and hl:
        check(f"{side}: 横裆宽 > 臀宽", tl[0].measured() > hl[0].measured(),
              f"{tl[0].measured():.1f} vs {hl[0].measured():.1f}")

print()
print("=== ease presets order correctly ===")
widths = {}
for fit in ("fitted", "regular", "loose"):
    widths[fit] = DRAFTERS["dress"][1](md, fit=fit)[0].net_size()[0]
check("fitted < regular < loose",
      widths["fitted"] < widths["regular"] < widths["loose"], str(widths))

print()
print("=== grading: every size step grows ===")
for gt, (cat, fn) in sorted(DRAFTERS.items()):
    ws = [fn(SIZE_CHART[cat][s])[0].net_size()[0] for s in SIZE_ORDER]
    check(f"{gt} front panel widens monotonically",
          all(b > a for a, b in zip(ws, ws[1:])),
          str([round(x, 1) for x in ws]))

print()
print("=== crossover blouse: the two fronts must differ ===")
cb = DRAFTERS["crossover-blouse"][1](SIZE_CHART["tops"]["M"])
big, small = cb[0], cb[1]
check("大襟 is wider than 小襟", big.net_size()[0] > small.net_size()[0],
      f"{big.net_size()[0]} vs {small.net_size()[0]}")
check("大襟 documents the overlap", "搭门" in big.note or
      any("搭门" in d.label for d in big.dims))

print()
print("=== cut size always exceeds net size (seam allowance applied) ===")
for gt, (cat, fn) in sorted(DRAFTERS.items()):
    ok = True
    for p in fn(SIZE_CHART[cat]["M"]):
        nw, nh = p.net_size()
        cw, ch = p.cut_size()
        if cw < nw or ch < nh:
            ok = False
    check(f"{gt}: 毛样 >= 净样 for all pieces", ok)

print()
print("=== fold-edge pieces carry no centre seam allowance ===")
for gt, (cat, fn) in sorted(DRAFTERS.items()):
    ok = True
    for p in fn(SIZE_CHART[cat]["M"]):
        if p.fold_edge == "left" and p.seams.get("center", 0) > 0:
            nw = p.net_size()[0]
            if abs(p.cut_size()[0] - nw - p.seams.get("side", 0)) > 0.01:
                ok = False
    check(f"{gt}: fold edge adds no allowance", ok)

print()
print("=== validator actually catches an injected error ===")
ps = DRAFTERS["t-shirt"][1](m)
ps[0].dims[0] = Dim("h", (0, 0), (10, 0), "假标注 999.9")
probs = validate_pieces(ps)
check("mismatched label is detected", any("999.9" in p for p in probs), str(probs))

ps2 = DRAFTERS["t-shirt"][1](m)
ps2[0].dims = []
check("piece with no dimensions is flagged",
      any("没有任何尺寸标注" in p for p in validate_pieces(ps2)))

print()
print("=== renderer produces valid, populated SVG ===")
out_dir = Path("/tmp/cds_pattern_test")
out_dir.mkdir(exist_ok=True)
for gt in sorted(DRAFTERS):
    dest = out_dir / f"{gt}.svg"
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "draw_pattern.py"),
         "--type", gt, "--size", "M", "-o", str(dest)],
        capture_output=True, text=True, cwd=ROOT,
    )
    if r.returncode != 0:
        check(f"{gt}: renders", False, r.stderr.strip()[:120])
        continue
    t = dest.read_text()
    try:
        xml.dom.minidom.parseString(t)
        wellformed = True
    except Exception as e:
        wellformed = False
        detail = str(e)
    check(f"{gt}: SVG is well-formed XML", wellformed,
          detail if not wellformed else "")
    n_pieces = len(DRAFTERS[gt][1](SIZE_CHART[DRAFTERS[gt][0]]["M"]))
    # every piece needs its name rendered, plus legend and the 1:1 caveat
    labels = re.findall(r"<text[^>]*>([^<]+)</text>", t)
    check(f"{gt}: all {n_pieces} piece names appear",
          all(any(p.name in l for l in labels)
              for p in DRAFTERS[gt][1](SIZE_CHART[DRAFTERS[gt][0]]["M"])))
    check(f"{gt}: legend + 1:1 caveat present",
          "净样线 Net / sewing line" in t and "1:1 实样纸样" in t)
    check(f"{gt}: has dimension annotations", len([l for l in labels if re.search(r"\d", l)]) >= 5)

print()
print("=== renderer refuses to emit a self-contradicting drawing ===")
bad_mod = out_dir / "inject.py"
bad_mod.write_text(
    "import sys; sys.path.insert(0, %r)\n"
    "import pattern_drafting as pd\n"
    "from calculate_garment import SIZE_CHART\n"
    "ps = pd.draft_tshirt(SIZE_CHART['tops']['M'])\n"
    "ps[0].dims[0] = pd.Dim('h', (0,0), (5,0), 'bogus 123.4')\n"
    "print(len(pd.validate_pieces(ps)))\n" % str(ROOT / "scripts")
)
r = subprocess.run([sys.executable, str(bad_mod)], capture_output=True, text=True)
check("validate_pieces reports the injected mismatch",
      r.stdout.strip() == "1", f"stdout={r.stdout!r} stderr={r.stderr[:80]}")

print()
print("=== every dimension label resolves to an English term ===")
from pattern_drafting import dim_english, seam_label, DIM_TERMS   # noqa: E402

untranslated = set()
n_labels = 0
for gt, (cat, fn) in DRAFTERS.items():
    for s in SIZE_ORDER:
        for p in fn(SIZE_CHART[cat][s]):
            for d in p.dims:
                n_labels += 1
                if not (d.en or dim_english(d.label)):
                    untranslated.add(d.label.rsplit(" ", 1)[0])
check(f"all {n_labels} dimension labels have an English term",
      not untranslated, f"missing: {sorted(untranslated)}")

# Longest-prefix matching matters: a shorter key must not shadow a longer one.
check("1/4胸围+放松量 resolves to the ease variant, not plain 1/4 bust",
      dim_english("1/4胸围+放松量 23.2") == "1/4 bust + ease",
      dim_english("1/4胸围+放松量 23.2"))
check("前横裆宽 does not resolve as 前臀宽",
      dim_english("前横裆宽 29.6") == "Front thigh width",
      dim_english("前横裆宽 29.6"))
check("袖长 vs 袖底缝 distinguished",
      dim_english("袖长 20") == "Sleeve length"
      and dim_english("袖底缝 9.2") == "Underarm seam")

check("seam_label renders bilingual", seam_label("armhole") == "袖窿 armhole",
      seam_label("armhole"))

print()
print("=== rendered SVG carries both languages ===")
for gt in ("t-shirt", "pants", "dress", "crossover-blouse"):
    dest = out_dir / f"{gt}.svg"
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "draw_pattern.py"),
         "--type", gt, "--size", "M", "-o", str(dest)],
        capture_output=True, text=True, cwd=ROOT,
    )
    t = dest.read_text()
    check(f"{gt}: English title present", "Pattern Cutting Diagram" in t)
    check(f"{gt}: bilingual net/cut caption", "净样 Net" in t and "毛样 Cut" in t)
    # The seam list wraps to as many lines as the cell allows, so the label is
    # abbreviated to "缝份 SA:" and each entry carries its own English term.
    check(f"{gt}: bilingual seam allowance line", "缝份 SA:" in t)
    check(f"{gt}: seam terms glossed in English",
          sum(k in t for k in ("shoulder", "side", "armhole", "hem", "waist")) >= 3)
    check(f"{gt}: bilingual grain label", "经向 Warp" in t or "纬向 Weft" in t)
    check(f"{gt}: bilingual legend", "净样线 Net / sewing line" in t)
    check(f"{gt}: English caveat present", "grade a full-size (1:1) pattern" in t)
    # at least a few English dimension terms rendered
    en_terms = sum(1 for term in set(DIM_TERMS.values()) if term in t)
    check(f"{gt}: >=3 English dimension terms rendered", en_terms >= 3,
          f"found {en_terms}")

print()
print("=== spec sheet is bilingual ===")
r = subprocess.run(
    [sys.executable, str(ROOT / "scripts" / "calculate_garment.py"),
     "--type", "pants", "--category", "bottoms", "--fabric", "denim"],
    capture_output=True, text=True, cwd=ROOT,
)
spec = r.stdout
check("spec: bilingual heading", "Spec Sheet" in spec)
check("spec: size chart bilingual header", "尺码<br>Size" in spec)
check("spec: measurement glossary present", "测量点说明 / Measurement points" in spec)
for key, zh, en in [("inseam", "下裆长", "Inseam"), ("outseam", "裤外长", "Outseam"),
                    ("hem", "脚口围", "Leg opening"), ("thigh", "大腿围", "Thigh")]:
    check(f"spec: {key} glossed as {zh}/{en}", f"`{key}` — {zh} / {en}" in spec)
check("spec: fabric section bilingual", "面料用量 / Fabric consumption" in spec)
check("spec: cost section bilingual", "成本核算 / Cost breakdown" in spec)
check("spec: English caveat present", "have a" in spec and "pattern maker verify" in spec)

# tops use a different measurement set — make sure those are glossed too
r2 = subprocess.run(
    [sys.executable, str(ROOT / "scripts" / "calculate_garment.py"),
     "--type", "t-shirt", "--category", "tops", "--fabric", "cotton"],
    capture_output=True, text=True, cwd=ROOT,
)
for key, zh, en in [("bust", "胸围", "Bust"), ("shoulder", "肩宽", "Shoulder"),
                    ("sleeve", "袖长", "Sleeve length"), ("length", "衣长", "Body length")]:
    check(f"spec(tops): {key} glossed as {zh}/{en}", f"`{key}` — {zh} / {en}" in r2.stdout)

print()
print("=== curves are dimensioned, not just endpoints ===")
# A curve given only endpoints is not reproducible: the scoop depth is what a
# pattern maker sets with a curve ruler. Every Q segment on a main panel must
# carry an arc callout.
from pattern_drafting import (                                    # noqa: E402
    path_arc_lengths, arc_length_by_label, quad_arc_length,
)

for gt in ("t-shirt", "pants", "dress", "crossover-blouse"):
    cat, fn = DRAFTERS[gt]
    for p in fn(SIZE_CHART[cat]["M"]):
        n_curves = len(path_arc_lengths(p))
        if n_curves == 0:
            continue
        check(f"{gt}/{p.name}: curves have arc callouts", len(p.arcs) >= 1)
        for a in p.arcs:
            check(f"{gt}/{p.name}: arc '{a.label}' has exact length",
                  a.length > 0 and abs(a.length - float(a.label.split()[-1])) < 0.06)
            check(f"{gt}/{p.name}: arc '{a.label}' glossed in English",
                  bool(dim_english(a.label)))

print()
print("=== sleeve cap matches the armhole it sews into ===")
# The defect this guards: sizing a sleeve from a formula while drawing a
# different curve produced a 47cm cap for a 28cm armhole — unsewable.
CAP_RULES = {
    # garment: (bodice piece indices, sleeve index, expected relation)
    "t-shirt": ((0, 1), 2, ("ease", 1.5)),
    "dress": ((0, 1), 4, ("ratio", 1.18)),
    "crossover-blouse": ((0, 2), 3, ("ease", 2.0)),
}
for gt, (bodices, sl_idx, (kind, target)) in CAP_RULES.items():
    cat, fn = DRAFTERS[gt]
    for size in SIZE_ORDER:
        ps = fn(SIZE_CHART[cat][size])
        armhole = sum(arc_length_by_label(ps[i], "袖窿弧长") for i in bodices)
        cap = sum(path_arc_lengths(ps[sl_idx]))
        check(f"{gt}/{size}: armhole is dimensioned", armhole > 1.0)
        if kind == "ease":
            check(f"{gt}/{size}: cap ease = +{target}cm",
                  abs((cap - armhole) - target) < 0.06)
        else:
            check(f"{gt}/{size}: cap gather ratio = {target}",
                  abs(cap / armhole - target) < 0.012)

print()
print("=== rendered SVG shows arc lengths ===")
for gt in ("t-shirt", "dress"):
    dest = out_dir / f"arc-{gt}.svg"
    subprocess.run([sys.executable, str(ROOT / "scripts" / "draw_pattern.py"),
                    "--type", gt, "--size", "M", "-o", str(dest)],
                   capture_output=True, text=True, cwd=ROOT)
    t = dest.read_text()
    check(f"{gt}: SVG has 袖窿弧长 callout", "袖窿弧长" in t)
    check(f"{gt}: SVG has scoop depth", "凹势" in t)
    check(f"{gt}: SVG glosses arc terms", "Armhole arc" in t and "Scoop depth" in t)
    check(f"{gt}: legend documents arc colour", "弧长/凹势" in t)

print()
if fails:
    print(f"❌ {len(fails)} FAILED:")
    for f in fails:
        print(f"  - {f}")
    sys.exit(1)
print("✅ all pattern drafting checks passed")
