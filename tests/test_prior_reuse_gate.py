"""未点名接续禁止引用旧任务交付路径；merge 写实病触发不垫上轮。"""
from __future__ import annotations

import unittest

from skills_kit.prior_reuse_gate import (
    assert_no_silent_prior_asset_reuse,
    prior_rounds_show_style_drift,
)
from skills_kit.converge import _merge_no_ref_forbid_prev_plate, _resolve_pad_auto
from pathlib import Path


class TestPriorReuseGate(unittest.TestCase):
    def test_blocks_skill_asset_without_continue(self) -> None:
        ok, why = assert_no_silent_prior_asset_reuse(
            "水果合成梯整表一组八档",
            ["assets/skill_20261111_fruit/merge_orange/sheet_session_r1.jpg"],
        )
        self.assertFalse(ok)
        self.assertIn("未点名接续", why)

    def test_allows_with_continue_words(self) -> None:
        ok, why = assert_no_silent_prior_asset_reuse(
            "接着上次水果关系稿继续改",
            ["assets/skill_20261111_fruit/merge_orange/merge_phase1.yaml"],
        )
        self.assertTrue(ok)
        self.assertEqual(why, "")

    def test_allows_refs_layout_pads(self) -> None:
        ok, why = assert_no_silent_prior_asset_reuse(
            "水果合成梯整表",
            ["assets/refs/gossip_harbor/gh_merge__ar_9x16.png"],
        )
        self.assertTrue(ok)
        self.assertEqual(why, "")

    def test_allows_suite_refs_and_downloads_pads(self) -> None:
        ok, why = assert_no_silent_prior_asset_reuse(
            "GH 垫风格跑图标",
            [
                "assets/skill_20261112_suite/refs/gh_ui.png",
                "downloads/gossip_harbor/gh_appicon.png",
            ],
        )
        self.assertTrue(ok)
        self.assertEqual(why, "")
        ok2, why2 = assert_no_silent_prior_asset_reuse(
            "用 assets/skill_20261112_suite/refs/gh_merge.png 垫风格",
            [],
        )
        self.assertTrue(ok2)
        self.assertEqual(why2, "")

    def test_still_blocks_suite_out_deliverables(self) -> None:
        ok, why = assert_no_silent_prior_asset_reuse(
            "接着上次合成梯继续改",
            ["assets/skill_20261112_suite/out/merge.ladder/sheet_r1.png"],
        )
        self.assertTrue(ok)
        ok2, why2 = assert_no_silent_prior_asset_reuse(
            "海鲜合成梯整表",
            ["assets/skill_20261112_suite/out/merge.ladder/sheet_r1.png"],
        )
        self.assertFalse(ok2)
        self.assertIn("未点名接续", why2)

    def test_blocks_goal_embedded_phase1(self) -> None:
        ok, why = assert_no_silent_prior_asset_reuse(
            "用 assets/skill_20261111_fruit/merge_orange/merge_phase1.yaml 出图",
            [],
        )
        self.assertFalse(ok)

    def test_blocks_memory_art_converge_and_sheet_r(self) -> None:
        ok, why = assert_no_silent_prior_asset_reuse(
            "水果合成梯",
            [".memory-art/converge/merge_cocoa_flat_20261111_report.md"],
        )
        self.assertFalse(ok)
        self.assertIn("未点名接续", why)
        ok2, _ = assert_no_silent_prior_asset_reuse(
            "接着上次继续改 sheet",
            ["assets/skill_20261111_drink/merge_cocoa_v2/sheet_r4.jpg"],
        )
        self.assertTrue(ok2)


class TestMergePadStyleDrift(unittest.TestCase):
    def test_merge_no_ref_flag(self) -> None:
        self.assertTrue(_merge_no_ref_forbid_prev_plate("merge.HarborOrange", ""))
        self.assertFalse(_merge_no_ref_forbid_prev_plate("merge.HarborOrange", "ref.png"))
        self.assertFalse(_merge_no_ref_forbid_prev_plate("ui.MainMenu", ""))

    def test_style_drift_detector(self) -> None:
        rounds = [
            {"round": 1, "defects": "表面偏写实产品静物", "next_fix": "改回糖釉"},
        ]
        self.assertTrue(prior_rounds_show_style_drift(rounds, 2))
        self.assertFalse(prior_rounds_show_style_drift(rounds, 1))
        legacy = [
            {"round": 1, "defects": "又落回光泽卡通 3D 硬塑", "next_fix": "改软立体糖釉"},
        ]
        self.assertTrue(prior_rounds_show_style_drift(legacy, 2))

    def test_resolve_pad_blocks_previous_on_merge_no_ref(self) -> None:
        root = Path(__file__).resolve().parents[1]
        rounds = [
            {
                "round": 1,
                "image": str(root / "assets" / "skill_20261111_fruit" / "merge_orange" / "sheet_session_r1.jpg"),
                "score": 8.2,
                "defects": "偏写实产品静物",
                "next_fix": "改糖釉",
                "judged": True,
            }
        ]
        # Only runs if the plate file exists; otherwise still assert reason path.
        pad, _fix, _rnd, cont, reason = _resolve_pad_auto(
            rounds,
            2,
            root,
            style_ref="",
            pad_mode="previous",
            module="merge.HarborOrange",
            goal="水果合成梯",
        )
        self.assertEqual(pad, "")
        self.assertFalse(cont)
        self.assertTrue("merge无参考" in reason or "禁止 pad=previous" in reason)


if __name__ == "__main__":
    unittest.main()
