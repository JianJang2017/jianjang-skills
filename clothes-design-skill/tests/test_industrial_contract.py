#!/usr/bin/env python3
"""Regression checks for the Industrial-A skill and delivery contract."""

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
CONTRACT = ROOT / "references" / "industrial-delivery-contract.md"


class IndustrialContractTest(unittest.TestCase):
    def test_entrypoint_defines_three_delivery_states(self):
        for state in ("PASS", "CONDITIONAL", "BLOCKED"):
            self.assertIn(state, SKILL)

    def test_entrypoint_routes_to_authoritative_contract(self):
        self.assertIn("references/industrial-delivery-contract.md", SKILL)
        self.assertTrue(CONTRACT.is_file())

    def test_boundary_is_consistent(self):
        combined = SKILL + "\n" + README
        self.assertIn("打版师复核", combined)
        self.assertIn("1:N", combined)
        self.assertIn("不可直接裁剪", combined)
        forbidden = (
            "可直接递交给面料采购和裁剪车间",
            "规格书可直接递交给制衣工厂使用",
            "可直接递交给裁剪车间",
            "可直接投产",
        )
        for phrase in forbidden:
            self.assertNotIn(phrase, combined)

    def test_delivery_contract_has_required_sections(self):
        text = CONTRACT.read_text(encoding="utf-8")
        for heading in (
            "输入预检",
            "能力矩阵",
            "交付状态",
            "打版师复核包",
            "降级与失败",
            "交付门禁",
        ):
            self.assertIsNotNone(
                re.search(rf"^##+\s+.*{re.escape(heading)}", text, re.MULTILINE),
                heading,
            )

    def test_eval_schema_is_machine_checkable(self):
        payload = json.loads((ROOT / "evals" / "evals.json").read_text(encoding="utf-8"))
        evals = payload["evals"]
        ids = [case["id"] for case in evals]
        self.assertEqual(len(ids), len(set(ids)))
        for case in evals:
            self.assertIsInstance(case["prompt"], str)
            self.assertTrue(case["prompt"].strip())
            self.assertIsInstance(case["required_behaviors"], list)
            self.assertTrue(case["required_behaviors"])
            self.assertIsInstance(case["forbidden_behaviors"], list)
            self.assertTrue(case["forbidden_behaviors"])
            serialized = json.dumps(case, ensure_ascii=False)
            self.assertNotIn("...", serialized)
            self.assertNotIn("…", serialized)

    def test_supporting_references_do_not_reopen_safety_boundary(self):
        garment = (ROOT / "references" / "garment-library.md").read_text(encoding="utf-8")
        prompt = (ROOT / "references" / "prompt-framework.md").read_text(encoding="utf-8")
        cost = (ROOT / "references" / "cost-model.md").read_text(encoding="utf-8")
        contract = CONTRACT.read_text(encoding="utf-8")
        self.assertNotIn("基于最接近的标准款式调整裁片结构", garment)
        self.assertIn("不得作为可量取比例", garment)
        self.assertIn("历史概念图提示词", prompt)
        self.assertIn("不得用于生成技术裁片", prompt)
        self.assertIn("只允许覆盖商业估算", cost)
        self.assertIn("状态评价用户请求的完整目标", contract)
        self.assertIn("默认值或市场均价时不得标记 `PASS`", contract)


if __name__ == "__main__":
    unittest.main(verbosity=2)
