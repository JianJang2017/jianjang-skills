#!/usr/bin/env python3
"""Smoke test for clothes-design-skill calculate_garment.py"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "calculate_garment.py"

CASES = [
    ("t-shirt", "tops", "cotton"),
    ("shirt", "tops", "cotton"),
    ("blouse", "tops", "silk"),
    ("pants", "bottoms", "denim"),
    ("skirt", "bottoms", "linen"),
    ("dress", "dresses", "silk"),
    ("jacket", "tops", "blend"),
    ("coat", "tops", "wool"),
]

fails = []
print(f"{'type/cat/fabric':<28} {'total':>10} {'fabric':>9} {'pcs':>5} {'eff':>5} {'sizes':>6}")
print("-" * 70)

for gtype, cat, fab in CASES:
    label = f"{gtype}/{cat}/{fab}"
    try:
        out = subprocess.run(
            [sys.executable, SCRIPT, "--type", gtype, "--category", cat,
             "--fabric", fab, "--json"],
            capture_output=True, text=True, timeout=30, cwd=ROOT,
        )
        if out.returncode != 0:
            fails.append((label, f"exit {out.returncode}: {out.stderr.strip()[:80]}"))
            print(f"{label:<28} FAILED (exit {out.returncode})")
            continue
        d = json.loads(out.stdout)
        c = d["cost_breakdown"]
        f = d["fabric_consumption"]
        n = len(d["size_table"])
        print(f"{label:<28} {c['total_cost']:>10.2f} {f['fabric_length_m']:>8}m "
              f"{f['pattern_pieces']:>5} {f['efficiency_rate']:>5} {n:>6}")

        # sanity assertions
        if n != 7:
            fails.append((label, f"expected 7 sizes, got {n}"))
        if c["total_cost"] <= 0:
            fails.append((label, "non-positive total cost"))
        if f["fabric_length_m"] <= 0:
            fails.append((label, "non-positive fabric length"))
        # cost identity check
        direct = c["fabric_cost"] + c["notions_cost"] + c["labor_cost"]
        expect_total = round(direct + c["overhead"], 2)
        if abs(expect_total - c["total_cost"]) > 0.02:
            fails.append((label, f"cost mismatch: {expect_total} vs {c['total_cost']}"))
        # overhead should be 15% of direct
        if abs(c["overhead"] - round(direct * 0.15, 2)) > 0.02:
            fails.append((label, f"overhead not 15% of direct ({c['overhead']} vs {direct*0.15:.2f})"))
    except Exception as e:
        fails.append((label, repr(e)))
        print(f"{label:<28} EXCEPTION {e}")

print()
# monotonic grading check
print("=== size grading monotonic check ===")
for cat, key in [("tops", "bust"), ("bottoms", "waist"), ("dresses", "length")]:
    out = subprocess.run(
        [sys.executable, SCRIPT, "--type", "dress" if cat == "dresses" else "t-shirt" if cat == "tops" else "pants",
         "--category", cat, "--fabric", "cotton", "--json"],
        capture_output=True, text=True,
        cwd=ROOT,
    )
    d = json.loads(out.stdout)["size_table"]
    order = ["XS", "S", "M", "L", "XL", "XXL", "XXXL"]
    vals = [d[s][key] for s in order]
    ok = all(b > a for a, b in zip(vals, vals[1:]))
    print(f"{cat:<10} {key:<8} {vals}  {'OK' if ok else 'NOT MONOTONIC'}")
    if not ok:
        fails.append((cat, f"{key} not monotonic"))

print()
# fabric width effect
print("=== wider fabric should need less length ===")
lens = {}
for w in (110, 140, 150):
    out = subprocess.run(
        [sys.executable, SCRIPT, "--type", "shirt", "--category", "tops",
         "--fabric", "cotton", "--fabric-width", str(w), "--json"],
        capture_output=True, text=True,
        cwd=ROOT,
    )
    lens[w] = json.loads(out.stdout)["fabric_consumption"]["fabric_length_m"]
print(lens)
if not (lens[110] > lens[140] > lens[150]):
    fails.append(("fabric-width", f"not inversely related: {lens}"))

print()
if fails:
    print(f"❌ {len(fails)} FAILURES:")
    for label, msg in fails:
        print(f"  - {label}: {msg}")
    sys.exit(1)
print("✅ all smoke checks passed")
