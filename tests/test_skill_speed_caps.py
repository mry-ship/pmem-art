"""重路径：最多4轮·到线即停 + 检测收窄 + 关系最多 2。"""
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
        self.assertEqual(MERGE_OVERVIEW_MAX_ROUNDS, 4)
        self.assertEqual(MERGE_OVERVIEW_MAX_DISCUSS, 2)
        self.assertEqual(MERGE_PER_CELL_MAX_ROUNDS, 4)
        self.assertEqual(UI_CONCEPT_MAX_ROUNDS, 4)
        self.assertEqual(ICON_KEY_MAX_ROUNDS, 4)
        self.assertEqual(SPLIT_MAX_ROUNDS, 4)

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
            4,
        )
        self.assertEqual(ov.get("merge_discuss_cap"), 2)
        self.assertFalse(ov.get("single_judge"))

        multi: dict = {"route_ids": ["draw.multi"], "max_rounds": 4}
        self.assertEqual(
            _apply_skill_speed_caps(multi, goal="", expect_route="", max_rounds=4),
            4,
        )
        self.assertEqual(multi.get("split_round_cap"), 4)
        self.assertFalse(multi.get("single_judge"))

        cell: dict = {"route_ids": ["merge.ladder"], "max_rounds": 4}
        self.assertEqual(
            _apply_skill_speed_caps(
                cell,
                goal="merge per_cell 一档一张 L3",
                expect_route="merge.ladder",
                max_rounds=4,
            ),
            4,
        )
        self.assertFalse(cell.get("single_judge"))

        ui: dict = {"route_ids": ["ui.kit"], "max_rounds": 8}
        self.assertEqual(
            _apply_skill_speed_caps(
                ui, goal="UI概念稿：主菜单", expect_route="ui.kit", max_rounds=8
            ),
            4,
        )
        self.assertEqual(ui.get("ui_delivery"), "concept")
        self.assertFalse(ui.get("single_judge"))

        sheet: dict = {"route_ids": ["ui.kit"], "max_rounds": 8}
        self.assertEqual(
            _apply_skill_speed_caps(
                sheet, goal="UI组件表：按钮态", expect_route="ui.kit", max_rounds=8
            ),
            4,
        )
        self.assertEqual(sheet.get("ui_delivery"), "sheet")
        self.assertEqual(sheet.get("ui_round_cap"), 4)
        self.assertFalse(sheet.get("single_judge"))

        icon: dict = {"route_ids": ["icon.c"], "max_rounds": 8}
        self.assertEqual(
            _apply_skill_speed_caps(
                icon, goal="道具格：药水", expect_route="icon.c", max_rounds=8
            ),
            4,
        )
        self.assertEqual(icon.get("icon_key_cap"), 4)
        self.assertFalse(icon.get("single_judge"))

    def test_generate_allows_round_2_blocks_past_cap(self) -> None:
        from PIL import Image

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data: dict = {"config": {"converge": {}}}
            sf = _session_file(root, "cell_cap_test")
            sf.parent.mkdir(parents=True, exist_ok=True)
            img2 = root / "c.png"
            Image.new("RGB", (64, 64), (20, 30, 40)).save(img2)
            overflow = root / "too_many.png"
            Image.new("RGB", (64, 64), (20, 30, 40)).save(overflow)
            sess = {
                "session_id": "cell_cap_test",
                "goal": "merge per_cell L2",
                "module": "prop.Test",
                "status": "running",
                "threshold": 9.5,
                "accept_threshold": 9.5,
                "max_rounds": 4,
                "merge_delivery": "per_cell",
                "single_judge": False,
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
            rc2 = cmd_converge(
                root,
                data,
                "generate",
                session_id="cell_cap_test",
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
            sess2["max_rounds"] = 4
            sf.write_text(json.dumps(sess2, ensure_ascii=False, indent=2), encoding="utf-8")
            rc5 = cmd_converge(
                root,
                data,
                "generate",
                session_id="cell_cap_test",
                round_num=5,
                image=str(overflow),
                prompt="overflow",
                skip_route_gate=True,
                skip_reasonableness_gate=True,
            )
            self.assertEqual(rc5, 1)

    def test_skill_text(self) -> None:
        for name in ("pmem-ui", "pmem-icon", "pmem-merge-ladder", "pmem-draw"):
            body = _body(name)
            self.assertNotIn("出图一轮交件", body, name)
            self.assertIn("到线即停", body, name)
        ui = _body("pmem-ui")
        self.assertIn("最多4轮", ui)
        icon = _body("pmem-icon")
        self.assertIn("未点名勿写已齐套", icon)
        self.assertIn("Dark/Tinted 已派生齐", icon)
        merge = _body("pmem-merge-ladder")
        self.assertIn("最多 2 稿", merge)
        self.assertIn("并行", merge)
        self.assertIn("禁止串行", merge)
        draw = _body("pmem-draw")
        self.assertNotIn("绝不能只生一张图就草草交差", draw)


if __name__ == "__main__":
    unittest.main()
