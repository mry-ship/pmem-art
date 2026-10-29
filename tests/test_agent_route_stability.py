"""总控路由稳定性：只判断走技能、走默认，还是停。不执行技能。"""
from __future__ import annotations

import sys
import unittest
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from skills_kit.agent_route_cases import Case, build_cases  # noqa: E402
from skills_kit.agent_router import execute_assigned_skill, plan_route  # noqa: E402
from skills_kit.skill_registry import build_registry  # noqa: E402
from skills_kit.skill_specs import SKILL_SPECS  # noqa: E402


def _check(case: Case) -> str:
    plan = plan_route(case.text, images=case.images, image_roles=case.roles)
    if plan.execute:
        return "execute 必须为 false"
    if plan.parallel:
        return "不允许并联"
    if plan.would_execute != (case.mode != "stop"):
        return f"would_execute={plan.would_execute} mode={plan.mode} reason={plan.reason}"
    if plan.mode != case.mode:
        return f"mode {plan.mode} != {case.mode} got={plan.route_ids} reason={plan.reason}"
    if case.mode == "stop":
        if plan.steps:
            return "停了还带着步骤"
        if case.reason and plan.reason != case.reason:
            return f"reason {plan.reason} != {case.reason}"
        return ""
    if plan.route_ids != case.route_ids:
        return f"routes {plan.route_ids} != {case.route_ids}"
    if plan.serial != (len(plan.steps) > 1):
        return "串联标记和步数不一致"
    if len(plan.steps) != len(case.route_ids):
        return "步数和路由条数不一致"
    for step in plan.steps:
        if not step.complete():
            return "六样不齐"
        if "--scale medium" in step.note and "不要写 --scale medium" not in step.note:
            return "split 写了 --scale medium"
    if case.two_state:
        if len(plan.steps) != 2:
            return "关开应该是前后两行"
        if "--contract split" not in plan.steps[0].note:
            return "第一行没有 --contract split"
        if plan.steps[1].pad != ["上一步通过的那张"]:
            return "第二行没有只垫通过的那张"
    if case.route_ids == ["draw.ordinary"]:
        note = plan.steps[0].note
        if "9.60" not in note or "多图分工" not in note:
            return f"普通图交接不完整: {note}"
        if "多图分工" in plan.announce and "不" not in plan.announce:
            return "普通图被说成多图分工"
    try:
        execute_assigned_skill(plan)
    except RuntimeError:
        return ""
    return "执行入口没有拦住"


class AgentRouteStabilityTests(unittest.TestCase):
    def test_registry_puts_ordinary_last(self) -> None:
        reg = build_registry(SKILL_SPECS)
        ids = [route["id"] for route in reg["routes"]]
        self.assertEqual(ids[-1], "draw.ordinary")
        phases = {route["id"]: route["phase"] for route in reg["routes"]}
        self.assertLess(phases["icon.a"], phases["draw.ordinary"])
        self.assertLess(phases["style.lock"], phases["draw.ordinary"])
        self.assertLess(phases["ui.kit"], phases["icon.a"])

    def test_two_thousand_artist_phrasings_stay_on_the_route(self) -> None:
        cases = build_cases()
        self.assertGreaterEqual(len(cases), 2000)
        shards = [cases[i::4] for i in range(4)]
        misses: list[str] = []
        with ProcessPoolExecutor(max_workers=4) as pool:
            batches = pool.map(_run_shard, shards)
        for batch in batches:
            misses.extend(batch)
        if misses:
            counts = Counter(item.split(" | ", 1)[0] for item in misses)
            sample = "\n".join(misses[:30])
            self.fail(f"{len(misses)}/{len(cases)} 路由偏离\n{counts}\n{sample}")

    def test_stale_heading_stops_without_ordinary(self) -> None:
        reg = build_registry(SKILL_SPECS)
        for route in reg["routes"]:
            if route["id"] == "draw.ordinary":
                route["heading"] = "## 这条标题已经不在文件里"
        plan = plan_route("画一张水彩半身", registry=reg)
        self.assertEqual(plan.mode, "stop")
        self.assertEqual(plan.reason, "stale_registry")
        self.assertFalse(plan.would_execute)
        self.assertEqual(plan.steps, [])

    def test_skill_entry_cannot_be_called(self) -> None:
        plan = plan_route("画一张水彩半身")
        with self.assertRaises(RuntimeError):
            execute_assigned_skill(plan)


def _run_shard(cases: list[Case]) -> list[str]:
    bad: list[str] = []
    for case in cases:
        msg = _check(case)
        if msg:
            bad.append(f"{case.bucket} | {msg} | {case.text}")
    return bad


if __name__ == "__main__":
    unittest.main()
