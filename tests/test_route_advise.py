"""本地路由建议：规则 + 蒸馏话术库检索，不执行技能。"""
from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from skills_kit.agent_router import plan_route  # noqa: E402
from skills_kit.route_bank import (  # noqa: E402
    BankEntry,
    advise_route,
    append_user_case,
    banner_for,
    distill_entries,
    format_advise_text,
    load_bank,
    match_confusion,
    rebuild_packaged_bank,
    retrieve,
    sync_project_bank,
)
from skills_kit.route_normalize import (  # noqa: E402
    build_canonical_brief,
    expand_colloquial,
)


class RouteAdviseTests(unittest.TestCase):
    def test_distill_is_smaller_than_full_cases_but_keeps_hard(self) -> None:
        entries = distill_entries()
        self.assertGreaterEqual(len(entries), 200)
        self.assertLess(len(entries), 2000)
        self.assertTrue(any(e.hard for e in entries))
        self.assertTrue(any(e.bucket == "heldout" for e in entries))

    def test_rebuild_writes_packaged_jsonl(self) -> None:
        path = rebuild_packaged_bank()
        self.assertTrue(path.is_file())
        lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        self.assertGreaterEqual(len(lines), 200)
        row = json.loads(lines[0])
        self.assertIn("text", row)
        self.assertIn("mode", row)

    def test_retrieve_clone_neighbors(self) -> None:
        hits = retrieve("参考这张画风，别画原来的人，换成一只猫", top_k=5)
        self.assertTrue(hits)
        self.assertTrue(
            any("draw.clone" in (h.get("route_ids") or []) or h.get("mode") == "skill" for h in hits)
        )

    def test_default_banner(self) -> None:
        plan = plan_route("画一张水彩半身的窗边女孩")
        self.assertIn("【走默认路径】", banner_for(plan))
        payload = advise_route("画一张水彩半身的窗边女孩")
        self.assertTrue(payload["banner"].startswith("【走默认路径】"))
        self.assertEqual(payload["route_ids"], ["draw.ordinary"])
        self.assertTrue(payload["would_execute"])

    def test_skill_banner_and_plan_align(self) -> None:
        text = "参考这张的画风，别画原来的人，换成修车的男孩"
        payload = advise_route(text, images=["ref/style.png"])
        self.assertEqual(payload["route_ids"], ["draw.clone"])
        self.assertTrue(payload["banner"].startswith("【按 "))
        self.assertIn("克隆", payload["banner"])

    def test_stop_banner(self) -> None:
        payload = advise_route("到底是整套界面还是一张插画")
        self.assertEqual(payload["mode"], "stop")
        self.assertTrue(payload["banner"].startswith("【路由停】"))
        self.assertFalse(payload["would_execute"])

    def test_llm_hints_are_capped(self) -> None:
        payload = advise_route("做一整套主菜单 HUD")
        hints = payload["llm_hints"]
        self.assertLessEqual(len(hints["neighbors"]), 5)
        for n in hints["neighbors"]:
            self.assertLessEqual(len(n["text"]), 80)

    def test_confusion_cards_fire(self) -> None:
        hits = match_confusion("参考这张，还是画这个女孩，不要换题材")
        self.assertTrue(any(h["id"] == "ref_no_new_subject" for h in hits))

    def test_sync_project_bank_keeps_user_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rebuild_packaged_bank()
            dest = sync_project_bank(root)
            self.assertTrue(dest.is_file())
            user = root / ".memory-art" / "route_bank" / "user.jsonl"
            self.assertTrue(user.is_file())
            bank = load_bank(root)
            self.assertGreaterEqual(len(bank), 200)

    def test_format_text_starts_with_banner(self) -> None:
        payload = advise_route("画一张水彩半身的窗边女孩")
        text = format_advise_text(payload)
        self.assertIn("【走默认路径】", text)
        from skills_kit.route_bank import format_artist_text

        brief = format_artist_text(payload)
        self.assertTrue(brief.startswith("【走默认路径】"))
        self.assertTrue(payload["execute_ok"])

    def test_plain_draw_girl_not_blocked(self) -> None:
        payload = advise_route("画一张窗边女孩")
        self.assertTrue(payload["execute_ok"])
        self.assertEqual(payload["route_ids"], ["draw.ordinary"])

    def test_format_honors_top_k_neighbors(self) -> None:
        payload = advise_route("画一张水彩半身", top_k=8)
        text = format_advise_text(payload)
        self.assertRegex(text, r"k=\d+")
        self.assertEqual(len(payload["neighbors"]), 8)
        # 只统计 top neighbors 段里的条目行
        block = text.split("top neighbors", 1)[-1]
        if "confusion:" in block:
            block = block.split("confusion:", 1)[0]
        shown = [ln for ln in block.splitlines() if re.match(r"\s*·\s+\d", ln)]
        self.assertEqual(len(shown), 8)

    def test_user_jsonl_enters_retrieve(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rebuild_packaged_bank()
            sync_project_bank(root)
            marker = "紫水晶路由探针句XYZ唯一标记勿撞库"
            append_user_case(
                root,
                BankEntry(
                    text=marker,
                    mode="skill",
                    route_ids=["draw.key"],
                    bucket="user",
                    hard=True,
                    source="user",
                ),
            )
            hits = retrieve(marker, root=root, top_k=3)
            self.assertTrue(hits)
            self.assertEqual(hits[0].get("source"), "user")
            self.assertEqual(hits[0].get("route_ids"), ["draw.key"])

    def test_colloquial_expand_adds_style_words(self) -> None:
        expanded = expand_colloquial("照着这张的味道画")
        self.assertIn("画风", expanded)
        self.assertIn("参考", expanded)

    def test_local_canonical_guesses_clone(self) -> None:
        brief = build_canonical_brief("参考这张，别画原来的人，换成一只猫", images=["a.png"])
        self.assertEqual(brief["guess_route_id"], "draw.clone")
        self.assertIn("克隆", brief["canonical"])

    def test_agent_canonical_conflict_lowers_confidence(self) -> None:
        # 原话是普通图；Agent 错写成克隆标准句 → 冲突降 low
        payload = advise_route(
            "画一张水彩半身的窗边女孩",
            canonical="有参考图；换新题材；锁画风；走克隆",
        )
        self.assertTrue(payload["plan_conflict"])
        self.assertEqual(payload["confidence"], "low")
        self.assertFalse(payload["execute_ok"])
        self.assertEqual(payload["route_ids"], ["draw.ordinary"])

    def test_matching_colloquial_via_canonical_keeps_clone(self) -> None:
        payload = advise_route(
            "照着这张的味道，主体改成一只喵",
            images=["ref.png"],
            canonical="有参考图；换新题材；锁画风；走克隆",
        )
        self.assertEqual(payload["route_ids"], ["draw.clone"])
        self.assertFalse(payload["plan_conflict"])
        self.assertTrue(payload["execute_ok"])
        self.assertIn("lexical", payload["match_kind"])

    def test_vague_icon_asks_not_silent_ordinary(self) -> None:
        payload = advise_route("那个图标弄下")
        self.assertEqual(payload["mode"], "stop")
        self.assertEqual(payload["confidence"], "ask")
        self.assertFalse(payload["execute_ok"])
        self.assertIn("图标", payload["artist_say"])

    def test_vague_deixis_asks_without_image(self) -> None:
        payload = advise_route("按昨天那张感觉再来一张")
        self.assertEqual(payload["mode"], "stop")
        self.assertIn("那张", payload["artist_ask"] + payload["artist_say"])

    def test_vague_merge_continue_asks(self) -> None:
        payload = advise_route("甜品合成那条继续")
        self.assertEqual(payload["mode"], "stop")
        self.assertTrue("合成" in payload["artist_say"] or "合成梯" in payload["artist_say"])

    def test_route_gate_blocks_then_allows(self) -> None:
        from skills_kit.route_gate import check_route_gate, save_route_advise

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ok, _ = check_route_gate(root, goal="画一张")
            self.assertFalse(ok)
            payload = advise_route("画一张水彩半身的窗边女孩")
            self.assertTrue(payload["execute_ok"])
            save_route_advise(root, payload, text="画一张水彩半身的窗边女孩")
            ok2, msg = check_route_gate(root, goal="画一张水彩半身的窗边女孩")
            self.assertTrue(ok2)
            self.assertIn("默认路径", msg)


if __name__ == "__main__":
    unittest.main()
