#!/usr/bin/env python3
"""
Test that examples/ matches what the current scripts produce.

The examples exist to show actual output, so they are only useful while they
stay in sync with the code. Both generators are deterministic, which means
drift is detectable: regenerate to a temp directory and diff.
"""

import difflib
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
REGEN = EXAMPLES / "regenerate.sh"

fails = []


def check(name, cond, detail=""):
    print(f"{'✅' if cond else '❌'} {name}" + (f"  — {detail}" if detail and not cond else ""))
    if not cond:
        fails.append(name)


def main():
    if not REGEN.exists():
        print(f"❌ {REGEN} not found; cannot verify freshness")
        return 1

    # Regenerate into a temp directory rather than over examples/ — a freshness
    # test that overwrites the thing it is checking can never fail.
    tmp = EXAMPLES.parent / "examples-temp"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir()

    script_text = REGEN.read_text()
    if 'OUT="$ROOT/examples"' not in script_text:
        print("❌ regenerate.sh structure changed; test needs update")
        return 1

    tmp_script = tmp / "regenerate.sh"
    tmp_script.write_text(script_text.replace(
        'OUT="$ROOT/examples"',
        f'OUT="{tmp}"'
    ))
    tmp_script.chmod(0o755)

    result = subprocess.run(
        ["bash", str(tmp_script)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    check("regenerate.sh exits 0", result.returncode == 0,
          result.stderr[-200:] if result.returncode else "")

    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        shutil.rmtree(tmp)
        return 1

    # Compare each file
    mismatches = []
    for path in (sorted(EXAMPLES.glob("*.svg"))
                 + sorted(EXAMPLES.glob("*.pdf"))
                 + sorted(EXAMPLES.glob("*.md"))):
        if path.name == "README.md":
            continue
        regenerated = tmp / path.name
        if not regenerated.exists():
            check(f"{path.name} was regenerated", False, "missing in temp")
            mismatches.append(path.name)
            continue

        if path.suffix == ".pdf":
            original = path.read_bytes()
            new = regenerated.read_bytes()
        else:
            original = path.read_text(encoding="utf-8")
            new = regenerated.read_text(encoding="utf-8")

        if original == new:
            check(f"{path.name} is current", True)
        else:
            check(f"{path.name} is current", False, "content differs")
            mismatches.append(path.name)
            # Show a unified diff snippet so the failure is actionable
            diff = [] if path.suffix == ".pdf" else list(difflib.unified_diff(
                original.splitlines(keepends=True), new.splitlines(keepends=True),
                fromfile=f"examples/{path.name}", tofile=f"regenerated/{path.name}",
                lineterm="", n=2,
            ))
            if diff:
                print("\n" + "".join(diff[:40]))
                if len(diff) > 40:
                    print(f"... ({len(diff) - 40} more lines)")

    shutil.rmtree(tmp)

    if mismatches:
        print()
        print(f"❌ {len(mismatches)} example(s) out of sync:")
        for name in mismatches:
            print(f"   - {name}")
        print()
        print("Run:  bash examples/regenerate.sh")
        return 1

    if fails:
        print()
        print(f"❌ {len(fails)} checks failed")
        return 1

    print()
    print("✅ all examples are current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
