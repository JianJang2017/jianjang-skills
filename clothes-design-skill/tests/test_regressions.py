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
if fails:
    print(f"❌ {len(fails)} FAILED: {fails}")
    sys.exit(1)
print(f"✅ all regression checks passed")
