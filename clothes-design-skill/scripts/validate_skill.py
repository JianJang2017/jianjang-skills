#!/usr/bin/env python3
"""Dependency-free release gate for clothes-design-skill."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"


def validate_structure() -> tuple[bool, str]:
    skill_path = ROOT / "SKILL.md"
    text = skill_path.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        return False, "SKILL.md has no valid opening frontmatter block"

    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    if fields.get("name") != ROOT.name:
        return False, f"frontmatter name {fields.get('name')!r} != folder {ROOT.name!r}"
    if not fields.get("description"):
        return False, "frontmatter description is empty"

    for target in re.findall(r"\[[^]]+\]\(([^)]+\.md)\)", text):
        if target.startswith(("http://", "https://")):
            continue
        if not (ROOT / target).is_file():
            return False, f"missing referenced file: {target}"
    return True, "frontmatter, folder name, and local references are valid"


def run_script(path: Path) -> tuple[bool, str]:
    result = subprocess.run(
        [sys.executable, str(path)], cwd=ROOT,
        capture_output=True, text=True, timeout=180,
    )
    detail = (result.stdout + result.stderr).strip()
    return result.returncode == 0, detail


def main() -> int:
    gates = [
        ("structure", validate_structure),
        ("industrial-contract", lambda: run_script(TESTS / "test_industrial_contract.py")),
        ("calculation", lambda: run_script(TESTS / "test_calculate_garment.py")),
        ("regressions", lambda: run_script(TESTS / "test_regressions.py")),
        ("pattern-drafting", lambda: run_script(TESTS / "test_pattern_drafting.py")),
        ("pattern-geometry", lambda: run_script(TESTS / "test_pattern_geometry.py")),
        ("pattern-pdf", lambda: run_script(TESTS / "test_pattern_pdf.py")),
        ("svg-text-overlap", lambda: run_script(TESTS / "test_no_text_overlap.py")),
        ("examples-current", lambda: run_script(TESTS / "test_examples_current.py")),
    ]
    injected = os.environ.get("CLOTHES_VALIDATION_FAIL_GATE", "")
    failures = 0

    print(f"Validating {ROOT.name} with {len(gates)} gates")
    for name, check in gates:
        if name == injected:
            ok, detail = False, "failure injected by CLOTHES_VALIDATION_FAIL_GATE"
        else:
            try:
                ok, detail = check()
            except Exception as exc:  # gate must turn infrastructure errors into failure
                ok, detail = False, f"{type(exc).__name__}: {exc}"
        print(f"[{'PASS' if ok else 'FAILED'}] {name}")
        if not ok:
            failures += 1
            if detail:
                print(detail)

    if failures:
        print(f"VALIDATION FAILED: {failures}/{len(gates)} gates failed")
        return 1
    print(f"ALL GATES PASSED: {len(gates)}/{len(gates)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
