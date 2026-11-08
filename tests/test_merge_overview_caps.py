"""merge overview：最多4轮·到线即停 + 关系稿上限 2。"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from skills_kit.converge import (  # noqa: E402
    MERGE_OVERVIEW_MAX_DISCUSS,
    MERGE_OVERVIEW_MAX_ROUNDS,
    MERGE_OVERVIEW_PAD_PREV_MIN_SCORE,
    _apply_merge_overview_caps,
    _merge_overview_pad_decision,
    _merge_overview_requested,
    _session_file,
    cmd_converge,
)


class MergeOverviewCapsTests(unittest.TestCase):
    def test_detect_overview_not_per_cell(self) -> None:
        self.assertTrue(
            _merge_overview_requested(
                goal="merge overview_sheet：鸡八档",
                expect_route="merge.ladder",
            )
        )
        self.assertFalse(
            _merge_overview_requested(
                goal="merge per_cell 一档一张",
                expect_route="merge.ladder",
            )
        )

    def test_apply_caps_sets_max_rounds_4(self) -> None:
        sess: dict = {"route_ids": ["merge.ladder"], "max_rounds": 4}
        got = _apply_merge_overview_caps(
            sess, goal="整表一组合成梯", expect_route="merge.ladder", max_rounds=4
        )
        self.assertEqual(got, MERGE_OVERVIEW_MAX_ROUNDS)
        self.assertEqual(sess["max_rounds"], 4)
        self.assertEqual(sess["merge_delivery"], "overview_sheet")
        self.assertEqual(sess["merge_discuss_cap"], 2)
        self.assertEqual(MERGE_OVERVIEW_MAX_DISCUSS, 2)
        self.assertFalse(sess.get("single_judge"))

    def test_pad_previous_only_when_high_score_local(self) -> None:
        high = [{"round": 1, "image": "a.png", "score": 8.7, "defects": "L3 冠尖轻微超框"}]
        ok, why, img, sc = _merge_overview_pad_decision(high, rebuild=False, next_fix="只收回 L3 冠尖")
        self.assertTrue(ok, why)
        self.assertEqual(img, "a.png")
        self.assertGreaterEqual(sc, MERGE_OVERVIEW_PAD_PREV_MIN_SCORE)

        low = [{"round": 1, "image": "a.png", "score": 7.2, "defects": "邻档不可分"}]
        ok2, why2, _, _ = _merge_overview_pad_decision(low, rebuild=False)
        self.assertFalse(ok2)
        self.assertIn("score_below", why2)

        bad = [{"round": 1, "image": "a.png", "score": 9.0, "defects": "末档回退成低档棚屋"}]
        ok3, why3, _, _ = _merge_overview_pad_decision(bad, rebuild=False)
        self.assertFalse(ok3)
        self.assertEqual(why3, "structural_or_relation_fail")

    def test_generate_allows_round_2_discuss_blocks_3(self) -> None:
        from PIL import Image

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data: dict = {"config": {"converge": {}}}
            sf = _session_file(root, "merge_cap_test")
            sf.parent.mkdir(parents=True, exist_ok=True)
            img2 = root / "b.png"
            Image.new("RGB", (64, 64), (20, 30, 40)).save(img2)
            sess = {
                "session_id": "merge_cap_test",
                "goal": "merge overview_sheet：测试",
                "module": "prop.Test",
                "status": "running",
                "threshold": 9.5,
                "accept_threshold": 9.5,
                "max_rounds": 4,
                "merge_delivery": "overview_sheet",
                "merge_sheet_cap": 4,
                "merge_discuss_cap": 2,
                "single_judge": False,
                "route_ids": ["merge.ladder"],
                "rounds": [
                    {"round": 1, "image": "a.png", "score": 8.0, "judged": True},
                ],
                "discussions": [
                    {"round": 1, "prompt": "稿1"},
                    {"round": 2, "prompt": "稿2"},
                ],
                "reasonableness": {
                    "passed": True,
                    "skill": "merge",
                    "skill_raw": "merge",
                    "revised": "整表修订句",
                },
                "scale": "medium",
                "pad_mode": "ref",
            }
            sf.write_text(json.dumps(sess, ensure_ascii=False, indent=2), encoding="utf-8")

            rc2 = cmd_converge(
                root,
                data,
                "generate",
                session_id="merge_cap_test",
                round_num=2,
                image=str(img2),
                prompt="next",
                skip_route_gate=True,
                skip_reasonableness_gate=True,
            )
            self.assertEqual(rc2, 0)

            sess2 = json.loads(sf.read_text(encoding="utf-8"))
            sess2["rounds"] = [
                {"round": i, "image": f"r{i}.png", "score": 8.0, "judged": True}
                for i in range(1, 5)
            ]
            sf.write_text(json.dumps(sess2, ensure_ascii=False, indent=2), encoding="utf-8")
            overflow = root / "too_many.png"
            Image.new("RGB", (64, 64), (20, 30, 40)).save(overflow)
            rc5 = cmd_converge(
                root,
                data,
                "generate",
                session_id="merge_cap_test",
                round_num=5,
                image=str(overflow),
                prompt="overflow",
                skip_route_gate=True,
                skip_reasonableness_gate=True,
            )
            self.assertEqual(rc5, 1)

            rc_d = cmd_converge(
                root,
                data,
                "discuss",
                session_id="merge_cap_test",
                round_num=3,
                prompt="第三稿不该写入",
            )
            self.assertEqual(rc_d, 1)


if __name__ == "__main__":
    unittest.main()
