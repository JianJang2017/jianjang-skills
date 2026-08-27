#!/usr/bin/env python3
"""Regression tests for the three defects fixed in calculate_garment.py"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "calculate_garment.py"
PY = sys.executable
fails = []


def run(*args):
    return subprocess.run(
        [PY, SCRIPT, *args], capture_output=True, text=True, timeout=30, cwd=ROOT
    )


def check(name, cond, detail=""):
    print(f"{'✅' if cond else '❌'} {name}" + (f"  — {detail}" if detail and not cond else ""))
    if not cond:
        fails.append(name)


print("=== DEFECT 1: unknown fabric/type must be flagged, not silently priced ===")
r = run("--type", "hanfu", "--category", "tops", "--fabric", "bamboo", "--json")
d = json.loads(r.stdout)
notes = d["cost_breakdown"]["assumptions"]
check("unknown fabric+type produce assumptions", len(notes) == 3, f"got {notes}")
check("assumption names the fabric", any("bamboo" in n for n in notes), str(notes))
check("assumption names the garment type", any("hanfu" in n for n in notes), str(notes))

r = run("--type", "shirt", "--category", "tops", "--fabric", "cotton", "--json")
d = json.loads(r.stdout)
check("known fabric+type produce NO assumptions",
      d["cost_breakdown"]["assumptions"] == [], str(d["cost_breakdown"]["assumptions"]))

# assumptions must surface in the markdown too, not only JSON
r = run("--type", "hanfu", "--category", "tops", "--fabric", "bamboo")
check("markdown surfaces assumptions block", "估算假设" in r.stdout)
check("markdown names unknown fabric", "bamboo" in r.stdout)

print()
print("=== DEFECT 2: invalid size name must error, not silently vanish ===")
r = run("--type", "dress", "--category", "dresses", "--fabric", "silk", "--sizes", "BOGUS", "--json")
check("invalid size exits non-zero", r.returncode != 0, f"exit={r.returncode}")
check("invalid size prints error to stderr", "未知尺码" in r.stderr, r.stderr[:120])
check("invalid size emits no JSON on stdout", r.stdout.strip() == "", r.stdout[:80])

r = run("--type", "t-shirt", "--category", "tops", "--fabric", "cotton", "--sizes", "M", "BOGUS", "--json")
check("mixed valid+invalid still errors", r.returncode != 0, f"exit={r.returncode}")

r = run("--type", "t-shirt", "--category", "tops", "--fabric", "cotton", "--sizes", "S", "M", "L", "--json")
check("valid subset works", r.returncode == 0)
d = json.loads(r.stdout)
check("subset returns exactly requested sizes", list(d["size_table"]) == ["S", "M", "L"], str(list(d["size_table"])))

# order independence
r = run("--type", "t-shirt", "--category", "tops", "--fabric", "cotton", "--sizes", "XXL", "S", "M", "--json")
d = json.loads(r.stdout)
check("output order is canonical regardless of CLI order",
      list(d["size_table"]) == ["S", "M", "XXL"], str(list(d["size_table"])))

print()
print("=== DEFECT 3: reference size must not be hardcoded to M ===")
r = run("--type", "t-shirt", "--category", "tops", "--fabric", "cotton", "--sizes", "XXXL", "--json")
check("XXXL-only does not crash", r.returncode == 0, r.stderr[:150])
d = json.loads(r.stdout)
check("reference_size is XXXL, not M", d["reference_size"] == "XXXL", d.get("reference_size"))
xxxl_len = d["fabric_consumption"]["fabric_length_m"]

r = run("--type", "t-shirt", "--category", "tops", "--fabric", "cotton", "--sizes", "M", "--json")
m_len = json.loads(r.stdout)["fabric_consumption"]["fabric_length_m"]
check("XXXL needs more fabric than M", xxxl_len > m_len, f"XXXL={xxxl_len} M={m_len}")

r = run("--type", "t-shirt", "--category", "tops", "--fabric", "cotton", "--sizes", "XXXL")
check("markdown does not claim '参考 M 码' when M absent", "参考 M 码" not in r.stdout)
check("markdown labels XXXL as reference", "参考 XXXL 码" in r.stdout)

# default still uses M
r = run("--type", "t-shirt", "--category", "tops", "--fabric", "cotton", "--json")
d = json.loads(r.stdout)
check("full range still references M", d["reference_size"] == "M", d.get("reference_size"))
check("full range has 7 sizes", len(d["size_table"]) == 7)

# middle-of-range fallback
r = run("--type", "t-shirt", "--category", "tops", "--fabric", "cotton", "--sizes", "XS", "S", "L", "XL", "--json")
d = json.loads(r.stdout)
check("no-M range picks a middle size", d["reference_size"] in ("S", "L"), d.get("reference_size"))

print()
print("=== cost transparency fields ===")
r = run("--type", "shirt", "--category", "tops", "--fabric", "silk", "--json")
c = json.loads(r.stdout)["cost_breakdown"]
for k in ("fabric_price_per_meter", "labor_rate_per_hour", "overhead_rate", "assumptions"):
    check(f"cost_breakdown exposes {k}", k in c)
check("silk price is 120/m", c["fabric_price_per_meter"] == 120, str(c.get("fabric_price_per_meter")))

r = run("--type", "shirt", "--category", "tops", "--fabric", "silk")
check("markdown shows unit price derivation", "¥120/米" in r.stdout)
check("markdown shows labor rate", "¥30/小时" in r.stdout)
check("markdown carries estimate caveat", "排料" in r.stdout)

print()
print("=== bad category ===")
r = run("--type", "shirt", "--category", "hats", "--fabric", "cotton", "--json")
check("argparse rejects bad category", r.returncode != 0)

print()
print("=== DEFECT 4: invalid fabric width must stop, not divide ===")
# Width is a divisor: 0 raised ZeroDivisionError, and negatives silently
# produced negative yardage and a negative total cost that still read as a quote.
for w in ("0", "-50"):
    r = run("--type", "t-shirt", "--category", "tops", "--fabric", "cotton",
            "--fabric-width", w, "--sizes", "M", "--json")
    check(f"width={w} exits non-zero", r.returncode != 0, f"exit {r.returncode}")
    check(f"width={w} names the fault", "幅宽" in r.stderr, r.stderr[-120:])
    check(f"width={w} emits no JSON", r.stdout.strip() == "", r.stdout[:80])
    check(f"width={w} does not traceback", "Traceback" not in r.stderr, r.stderr[-120:])

r = run("--type", "t-shirt", "--category", "tops", "--fabric", "cotton",
        "--fabric-width", "5", "--sizes", "M", "--json")
check("implausibly narrow width is rejected", r.returncode != 0, f"exit {r.returncode}")

r = run("--type", "t-shirt", "--category", "tops", "--fabric", "cotton",
        "--fabric-width", "140", "--sizes", "M", "--json")
d = json.loads(r.stdout)
check("standard width still works", r.returncode == 0)
check("standard width yields positive yardage",
      d["fabric_consumption"]["fabric_length_m"] > 0,
      str(d["fabric_consumption"]["fabric_length_m"]))
check("standard width yields positive cost",
      d["cost_breakdown"]["total_cost"] > 0, str(d["cost_breakdown"]["total_cost"]))

print()
print("=== DEFECT 5: every drafted type needs real cost data ===")
# The cutting engine drafts 7 types but the cost tables only covered 5, so
# crossover-blouse and jeans were quoted on generic fallbacks. Worse, the
# marker-efficiency fallback recorded nothing at all, so the yardage read as if
# it had been looked up. Any type draw_pattern.py can draft must price from real
# data — otherwise a complete-looking spec rests on guesses.
sys.path.insert(0, str(ROOT / "scripts"))
from pattern_drafting import DRAFTERS  # noqa: E402

CATEGORY_OF = {gt: cat for gt, (cat, _) in DRAFTERS.items()}

for gt, cat in sorted(CATEGORY_OF.items()):
    r = run("--type", gt, "--category", cat, "--fabric", "cotton",
            "--sizes", "M", "--json")
    check(f"{gt}: spec generates", r.returncode == 0, r.stderr[-120:])
    if r.returncode != 0:
        continue
    d = json.loads(r.stdout)
    fab_asm = d["fabric_consumption"]["assumptions"]
    cost_asm = d["cost_breakdown"]["assumptions"]
    check(f"{gt}: no yardage fallback", fab_asm == [], str(fab_asm))
    check(f"{gt}: no cost fallback", cost_asm == [], str(cost_asm))

# crossover-blouse has 7 pieces incl. an asymmetric overlap and a 190cm sash;
# quoting it as a plain blouse understated both labour and fabric.
r = run("--type", "crossover-blouse", "--category", "tops", "--fabric", "linen",
        "--sizes", "M", "--json")
xb = json.loads(r.stdout)
r = run("--type", "blouse", "--category", "tops", "--fabric", "linen",
        "--sizes", "M", "--json")
pb = json.loads(r.stdout)
check("crossover-blouse costs more labour than plain blouse",
      xb["cost_breakdown"]["labor_hours"] > pb["cost_breakdown"]["labor_hours"],
      f'{xb["cost_breakdown"]["labor_hours"]} vs {pb["cost_breakdown"]["labor_hours"]}')
check("crossover-blouse markers less efficiently than plain blouse",
      xb["fabric_consumption"]["efficiency_rate"] < pb["fabric_consumption"]["efficiency_rate"],
      f'{xb["fabric_consumption"]["efficiency_rate"]} vs {pb["fabric_consumption"]["efficiency_rate"]}')

# jeans need rivets, heavier thread and topstitching that plain pants do not.
r = run("--type", "jeans", "--category", "bottoms", "--fabric", "denim",
        "--sizes", "M", "--json")
jn = json.loads(r.stdout)
r = run("--type", "pants", "--category", "bottoms", "--fabric", "denim",
        "--sizes", "M", "--json")
pt = json.loads(r.stdout)
check("jeans notions exceed plain pants",
      jn["cost_breakdown"]["notions_cost"] > pt["cost_breakdown"]["notions_cost"],
      f'{jn["cost_breakdown"]["notions_cost"]} vs {pt["cost_breakdown"]["notions_cost"]}')

# The efficiency fallback must still fire — and be disclosed — for a type the
# engine genuinely does not know.
r = run("--type", "hanfu", "--category", "tops", "--fabric", "bamboo", "--json")
d = json.loads(r.stdout)
check("unknown type discloses yardage fallback",
      any("排料效率" in n for n in d["fabric_consumption"]["assumptions"]),
      str(d["fabric_consumption"]["assumptions"]))

r = run("--type", "hanfu", "--category", "tops", "--fabric", "bamboo")
check("markdown merges yardage and cost assumptions",
      "排料效率" in r.stdout and "bamboo" in r.stdout)

print()
if fails:
    print(f"❌ {len(fails)} FAILED: {fails}")
    sys.exit(1)
print(f"✅ all regression checks passed")
