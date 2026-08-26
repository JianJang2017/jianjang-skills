#!/usr/bin/env python3
"""Behavior tests for the dependency-free validation entrypoint."""

import os
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
RUNNER = ROOT / "scripts" / "validate_skill.py"


class ValidateSkillRunnerTest(unittest.TestCase):
    def run_runner(self, cwd: Path, fail_gate: str = ""):
        env = os.environ.copy()
        if fail_gate:
            env["CLOTHES_VALIDATION_FAIL_GATE"] = fail_gate
        return subprocess.run(
            [sys.executable, str(RUNNER)], cwd=cwd, env=env,
            capture_output=True, text=True, timeout=120,
        )

    def test_runner_succeeds_from_skill_directory(self):
        result = self.run_runner(ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("ALL GATES PASSED", result.stdout)

    def test_runner_succeeds_from_repository_root(self):
        result = self.run_runner(REPO)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_runner_propagates_gate_failure(self):
        result = self.run_runner(ROOT, "industrial-contract")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("industrial-contract", result.stdout)
        self.assertIn("FAILED", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
