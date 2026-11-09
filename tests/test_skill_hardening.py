"""闸门分级 / 高频 remap / benchmark / 标准句自检 / skills verify。"""
from __future__ import annotations

import os
import unittest
from pathlib import Path

from skills_kit.agent_router import plan_route
from skills_kit.benchmark_catalog import assert_refs_not_benchmark_pads, lookup
from skills_kit.gate_skip import resolve_skip_request
from skills_kit.route_bank import advise_route
from skills_kit.route_normalize import validate_canonical
from skills_kit.skills_verify import verify_skills


class GateSkipTests(unittest.TestCase):
    def test_bare_skip_denied_without_allow(self) -> None:
        old_allow = os.environ.pop("PMEM_ART_ALLOW_GATE_SKIP", None)
        old_under = os.environ.pop("PMEM_ART_UNDER_TEST", None)
        old_pytest = os.environ.pop("PYTEST_CURRENT_TEST", None)
        try:
            ok, msg = resolve_skip_request(flag=True, reason="debug", env_name="PMEM_ART_SKIP_ROUTE_GATE")
            self.assertFalse(ok)
            self.assertIn("拒绝", msg)
        finally:
            if old_allow is not None:
                os.environ["PMEM_ART_ALLOW_GATE_SKIP"] = old_allow
            if old_under is not None:
                os.environ["PMEM_ART_UNDER_TEST"] = old_under
            if old_pytest is not None:
                os.environ["PYTEST_CURRENT_TEST"] = old_pytest
            os.environ.setdefault("PMEM_ART_ALLOW_GATE_SKIP", "1")
            os.environ.setdefault("PMEM_ART_UNDER_TEST", "1")

    def test_skip_needs_reason_outside_test(self) -> None:
        old_allow = os.environ.pop("PMEM_ART_ALLOW_GATE_SKIP", None)
        old_under = os.environ.pop("PMEM_ART_UNDER_TEST", None)
        old_pytest = os.environ.pop("PYTEST_CURRENT_TEST", None)
        try:
            ok, msg = resolve_skip_request(flag=True, reason="", env_name="PMEM_ART_SKIP_ROUTE_GATE")
            self.assertFalse(ok)
            self.assertIn("skip-reason", msg)
        finally:
            if old_allow is not None:
                os.environ["PMEM_ART_ALLOW_GATE_SKIP"] = old_allow
            else:
                os.environ["PMEM_ART_ALLOW_GATE_SKIP"] = "1"
            if old_under is not None:
                os.environ["PMEM_ART_UNDER_TEST"] = old_under
            else:
                os.environ["PMEM_ART_UNDER_TEST"] = "1"
            if old_pytest is not None:
                os.environ["PYTEST_CURRENT_TEST"] = old_pytest

    def test_skip_ok_with_allow_and_reason(self) -> None:
        os.environ["PMEM_ART_ALLOW_GATE_SKIP"] = "1"
        ok, msg = resolve_skip_request(flag=True, reason="unit-test", env_name="PMEM_ART_SKIP_ROUTE_GATE")
        self.assertTrue(ok)
        self.assertIn("unit-test", msg)


class JobRemapTests(unittest.TestCase):
    def test_local_fix_remaps_ordinary(self) -> None:
        plan = plan_route("只修手指和接触阴影，机位别动")
        self.assertEqual(plan.route_ids, ["draw.ordinary"])
        self.assertEqual(plan.reason, "job_remap")
        self.assertIn("局部修", plan.announce)

    def test_arm_not_local_fix_false_friend(self) -> None:
        plan = plan_route("只修手臂姿态，画一张战士")
        self.assertNotEqual(plan.reason, "job_remap")

    def test_character_sheet_remaps_variant(self) -> None:
        plan = plan_route("给我做设定表，同一张脸")
        self.assertEqual(plan.route_ids, ["draw.variant"])
        self.assertEqual(plan.reason, "job_remap")

    def test_storyboard_asks(self) -> None:
        plan = plan_route("帮我做分镜，第0件")
        self.assertEqual(plan.mode, "stop")
        self.assertEqual(plan.reason, "job_ask")

    def test_storyboard_composition_feel_not_ask(self) -> None:
        plan = plan_route("分镜构图强一点的主视觉")
        self.assertNotEqual(plan.reason, "job_ask")

    def test_sequence_still_unrecognized(self) -> None:
        plan = plan_route("出一组序列帧动画")
        self.assertEqual(plan.reason, "unrecognized")


class CanonicalWarnTests(unittest.TestCase):
    def test_ordinary_self_poison_detected(self) -> None:
        warns = validate_canonical("要画一张图；有参考也不换题材；走普通图")
        self.assertTrue(any("self_poison" in w for w in warns))

    def test_good_ordinary_ok(self) -> None:
        warns = validate_canonical("要画一张图；有参考；题材不变；走普通图")
        self.assertEqual(warns, [])

    def test_advise_marks_conflict_on_poison(self) -> None:
        payload = advise_route(
            "画一张窗边女孩",
            canonical="要画一张图；有参考也不换题材；走普通图",
        )
        self.assertTrue(payload.get("plan_conflict"))
        self.assertFalse(payload.get("execute_ok"))


class BenchmarkTests(unittest.TestCase):
    def test_lookup_merge(self) -> None:
        root = Path(__file__).resolve().parents[1]
        result = lookup("merge", root=root)
        self.assertTrue(result.get("ok"), result)
        card = result["card"]
        self.assertEqual(card["id"], "merge.cabinet")
        surface = str(card.get("surface") or "")
        self.assertIn("Merge Mansion", surface)
        levels = card.get("ladder_levels") or []
        self.assertTrue(levels, levels)
        joined = " ".join(str(x) for x in levels)
        self.assertIn("朴素完整小件", joined)
        self.assertNotIn("原料/空壳", joined)

    def test_forbid_benchmark_pad(self) -> None:
        ok, why = assert_refs_not_benchmark_pads([".memory-art/benchmarks/x.png"])
        self.assertFalse(ok)
        self.assertIn("禁止", why)


class SkillsVerifyTests(unittest.TestCase):
    def test_verify_quick(self) -> None:
        root = Path(__file__).resolve().parents[1]
        report = verify_skills(root, quick=True)
        self.assertTrue(report["ok"], report)


if __name__ == "__main__":
    unittest.main()
