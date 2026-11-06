"""重路径：出图一轮交件 + 检测收窄 + 关系最多 2。"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from skills_kit.converge import (  # noqa: E402
    ICON_KEY_MAX_ROUNDS,
    MERGE_OVERVIEW_MAX_DISCUSS,
    MERGE_OVERVIEW_MAX_ROUNDS,
    MERGE_PER_CELL_MAX_ROUNDS,
    SPLIT_MAX_ROUNDS,
    UI_CONCEPT_MAX_ROUNDS,
    _apply_skill_speed_caps,
    _icon_speed_requested,
    _merge_overview_requested,
    _merge_per_cell_requested,
    _session_file,
    _split_speed_requested,
    _ui_speed_requested,
    cmd_converge,
)
from skills_kit.skill_specs import SKILL_SPECS  # noqa: E402


def _body(name: str) -> str:
    return next(s for s in SKILL_SPECS if s["name"] == name)["body"]


class SkillSpeedCapsTests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(MERGE_OVERVIEW_MAX_ROUNDS, 1)
        self.assertEqual(MERGE_OVERVIEW_MAX_DISCUSS, 2)
        self.assertEqual(MERGE_PER_CELL_MAX_ROUNDS, 1)
        self.assertEqual(UI_CONCEPT_MAX_ROUNDS, 1)
        self.assertEqual(ICON_KEY_MAX_ROUNDS, 1)
        self.assertEqual(SPLIT_MAX_ROUNDS, 1)

    def test_detection_narrow(self) -> None:
        self.assertEqual(
            _ui_speed_requested(goal="UI概念稿：主菜单", expect_route="ui.kit"),
            "concept",
        )
        self.assertEqual(
            _ui_speed_requested(goal="只是一张含 hud 字样的插画", expect_route=""),
            "",
        )
        self.assertFalse(
            _merge_overview_requested(goal="合成一张风景海报", expect_route="")
        )
        self.assertTrue(
            _merge_overview_requested(
                goal="合成梯整表一组", expect_route="merge.ladder"
            )
        )
        self.assertTrue(
            _merge_per_cell_requested(
                goal="合成梯 per_cell 一档一张", expect_route="merge.ladder"
            )
        )
        self.assertFalse(_icon_speed_requested(goal="画个道具格气氛图", expect_route=""))
        self.assertTrue(_icon_speed_requested(expect_route="icon.c", goal="道具格：药水"))
        self.assertTrue(_split_speed_requested(goal="多图分工", contract="split"))
        self.assertTrue(_split_speed_requested(route_ids=["draw.multi"]))
        self.assertTrue(_split_speed_requested(expect_route="draw.multi"))
        self.assertFalse(_split_speed_requested(goal="", route_ids=["draw.ordinary"]))

    def test_apply_caps(self) -> None:
        ov: dict = {"route_ids": ["merge.ladder"], "max_rounds": 4}
        self.assertEqual(
            _apply_skill_speed_caps(
                ov, goal="整表一组合成梯", expect_route="merge.ladder", max_rounds=4
            ),
            1,
        )
        self.assertEqual(ov.get("merge_discuss_cap"), 2)

        multi: dict = {"route_ids": ["draw.multi"], "max_rounds": 4}
        self.assertEqual(
            _apply_skill_speed_caps(multi, goal="", expect_route="", max_rounds=4),
            1,
        )
        self.assertEqual(multi.get("split_round_cap"), 1)

        cell: dict = {"route_ids": ["merge.ladder"], "max_rounds": 4}
        self.assertEqual(
            _apply_skill_speed_caps(
                cell,
                goal="merge per_cell 一档一张 L3",
                expect_route="merge.ladder",
                max_rounds=4,
            ),
            1,
        )

    def test_generate_blocks_round_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data: dict = {"config": {"converge": {}}}
            sf = _session_file(root, "cell_cap_test")
            sf.parent.mkdir(parents=True, exist_ok=True)
            sess = {
                "session_id": "cell_cap_test",
                "goal": "merge per_cell L2",
                "module": "prop.Test",
                "status": "running",
                "threshold": 9.5,
                "accept_threshold": 9.5,
                "max_rounds": 1,
                "merge_delivery": "per_cell",
                "single_judge": True,
                "route_ids": ["merge.ladder"],
                "rounds": [{"round": 1, "image": "a.png", "score": 8.0, "judged": True}],
                "reasonableness": {
                    "passed": True,
                    "skill": "merge",
                    "skill_raw": "merge",
                    "revised": "单档修订句",
                },
                "scale": "medium",
                "pad_mode": "ref",
            }
            sf.write_text(json.dumps(sess, ensure_ascii=False, indent=2), encoding="utf-8")
            rc = cmd_converge(
                root,
                data,
                "generate",
                session_id="cell_cap_test",
                round_num=2,
                image="c.png",
                prompt="next",
                skip_route_gate=True,
                skip_reasonableness_gate=True,
            )
            self.assertEqual(rc, 1)

    def test_skill_text(self) -> None:
        ui = _body("pmem-ui")
        self.assertIn("出图一轮交件", ui)
        self.assertIn("过线/未过线", ui)
        icon = _body("pmem-icon")
        self.assertIn("未点名勿写已齐套", icon)
        self.assertIn("Dark/Tinted 已派生齐", icon)
        merge = _body("pmem-merge-ladder")
        self.assertIn("最多 2 稿", merge)
        self.assertIn("禁止垫上一张成图", merge)
        self.assertNotIn("才垫上一张成图", merge)
        draw = _body("pmem-draw")
        self.assertIn("到线即停", draw)
        self.assertNotIn("绝不能只生一张图就草草交差", draw)


if __name__ == "__main__":
    unittest.main()
