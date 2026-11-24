"""Delivery-speed gates that must not lower the 9.5 bar."""
from __future__ import annotations

import io
import json
import os
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("PMEM_ART_ALLOW_GATE_SKIP", "1")

import sys

sys.path.insert(0, str(ROOT))

from improve.warm_start import (  # noqa: E402
    filter_composition_prefs,
    filter_keeps_with_audit,
    habit_relevant_for_task,
)
from skills_kit.agent_router import _icon_modes  # noqa: E402
from skills_kit.icon_geometry import (  # noqa: E402
    cap_dims_for_icon_geometry,
    icon_geometry_skip_reason,
)
from skills_kit.parallel_slots import assert_can_start, list_active_sessions  # noqa: E402
from skills_kit.route_normalize import build_canonical_brief  # noqa: E402
from skills_kit.scoring import parse_5d_dims  # noqa: E402


def _solid(path: Path, size: int, bg: tuple[int, int, int], fg: tuple[int, int, int], span: int) -> None:
    from PIL import Image

    img = Image.new("RGB", (size, size), bg)
    if span > 0:
        x0 = (size - span) // 2
        img.paste(fg, (x0, x0, x0 + span, x0 + span))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


class TestStaleSlots(unittest.TestCase):
    def test_old_running_session_does_not_hold_a_slot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / ".memory-art" / "converge"
            d.mkdir(parents=True)
            data = {"config": {"agent": {"max_parallel": 1, "slot_stale_hours": 36}}}
            stale = d / "old.json"
            stale.write_text(
                json.dumps({"session_id": "old", "status": "running"}),
                encoding="utf-8",
            )
            old_ts = time.time() - 40 * 3600
            os.utime(stale, (old_ts, old_ts))
            fresh = d / "live.json"
            fresh.write_text(
                json.dumps({"session_id": "live", "status": "running"}),
                encoding="utf-8",
            )
            active = list_active_sessions(root, data)
            self.assertEqual([a["session_id"] for a in active], ["live"])
            self.assertIn('"status": "running"', stale.read_text(encoding="utf-8"))
            now = time.time()
            os.utime(stale, (now, now))
            again = [a["session_id"] for a in list_active_sessions(root, data)]
            self.assertEqual(again, ["live", "old"])
            os.utime(stale, (old_ts, old_ts))
            ok, _msg = assert_can_start(root, data, session_id="newer")
            self.assertFalse(ok)
            data_open = {"config": {"agent": {"max_parallel": 2, "slot_stale_hours": 36}}}
            ok2, _ = assert_can_start(root, data_open, session_id="newer")
            self.assertTrue(ok2)


class TestIconTasteFilter(unittest.TestCase):
    def test_character_habit_stays_off_app_icon_prompts(self) -> None:
        habit = "狗狗棋子要全身多姿势灵动，不要只画狗头；眼睛要虹膜瞳孔湿高光"
        self.assertFalse(
            habit_relevant_for_task(habit, "brand.WorldStyle", "1024 App Icon Tile Match")
        )
        self.assertFalse(habit_relevant_for_task(habit, "ui.MainMenu", "休闲主菜单 HUD"))
        self.assertTrue(habit_relevant_for_task(habit, "character.Dog", "画一只狗全身"))

    def test_merge_keep_does_not_enter_app_icon(self) -> None:
        kept, _dropped = filter_keeps_with_audit(
            [
                {
                    "text": "五链合成：不必每档保留L1原件/母体锁死；同域合理升级、档差明显即可",
                    "scopes": ["merge_ladder"],
                }
            ],
            "brand.WorldStyle",
            "1024 App Icon",
        )
        self.assertEqual(kept, [])

    def test_body_framing_prefs_drop_for_icons(self) -> None:
        vals = filter_composition_prefs(
            ["全身", "半身居中"],
            "brand.WorldStyle",
            "1024 桌面启动图标",
        )
        self.assertEqual(vals, [])
        kept = filter_composition_prefs(["居中单符号"], "brand.WorldStyle", "1024 App Icon")
        self.assertEqual(kept, ["居中单符号"])


class TestAppiconColloquial(unittest.TestCase):
    def test_appicon_one_word_locks_icon_a(self) -> None:
        self.assertIn("icon.a", _icon_modes("出一个 tilematch 的 appicon"))
        brief = build_canonical_brief("出一个 tilematch 的 appicon")
        self.assertEqual(brief["guess_route_id"], "icon.a")


class TestIconGeometrySkip(unittest.TestCase):
    def test_confident_undersize_caps_safe_zone_and_skips_remote(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            small = Path(tmp) / "small.png"
            large = Path(tmp) / "large.png"
            _solid(small, 128, (20, 140, 120), (250, 236, 210), 40)
            _solid(large, 128, (20, 140, 120), (250, 236, 210), 100)
            goal = "1024 App Icon Tile Match"
            self.assertTrue(icon_geometry_skip_reason(small, goal=goal, module="brand.WorldStyle"))
            self.assertFalse(icon_geometry_skip_reason(large, goal=goal, module="brand.WorldStyle"))
            self.assertFalse(
                icon_geometry_skip_reason(small, goal="窗边水彩女孩", module="character.Hero")
            )
            self.assertFalse(
                icon_geometry_skip_reason(small, goal="1024 竖构图窗边女孩", module="brand.WorldStyle")
            )
            dims = "识别度9.6/安全区9.7/光影质感9.5/多尺寸合规9.6/色板纯粹9.7/无瑕疵9.6"
            capped, reason = cap_dims_for_icon_geometry(
                small, dims, goal=goal, module="brand.WorldStyle"
            )
            self.assertIn("安全区7.2", capped)
            self.assertTrue(reason)
            parsed = parse_5d_dims(capped, module="brand.WorldStyle")
            self.assertLessEqual(float(parsed["weighted_score"]), 7.2)
            from skills_kit.judge_auto import auto_vlm_judge_image
            from skills_kit.prompt_scale import get_converge_scale_profile

            prof = get_converge_scale_profile("medium", goal=goal, module="brand.WorldStyle")
            judged = auto_vlm_judge_image(
                str(small),
                prof,
                round_num=1,
                dims="构图9.80/光影9.70/透视9.60/质感9.70/风格9.70/无瑕疵9.80",
                use_remote_vlm=False,
                goal=goal,
                module="brand.WorldStyle",
            )
            self.assertLessEqual(float(judged["calibrated_score"]), 7.2)
            self.assertFalse(judged["passed"])


class TestPrepareOneProcess(unittest.TestCase):
    def test_prepare_emits_prompt_with_one_warm_pack(self) -> None:
        from skills_kit.converge import cmd_converge_prepare
        from skills_kit.reasonableness_gate import default_checklist_template

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data: dict = {"config": {"converge": {}}, "modules": {}, "entries": []}
            buf = io.StringIO()
            revised = (
                "青瓷小猫蹲坐捧茶盏，爪与盏接触清楚；背景最多一扇窗；"
                "竖构图无字；一眼失败是多爪或茶盏漂浮。"
            )
            with redirect_stdout(buf):
                rc = cmd_converge_prepare(
                    root,
                    data,
                    session_id="prep-1",
                    goal="青瓷小猫蹲坐捧茶盏",
                    module="brand.WorldStyle",
                    scale="medium",
                    skip_route_gate=True,
                    skip_reason="unit test prepare",
                    reason_skill="ordinary",
                    reason_draft="青瓷小猫蹲坐捧茶盏",
                    revised=revised,
                    checklist=default_checklist_template("ordinary"),
                    keep="同一只青瓷小猫",
                    forbid="不要文字",
                )
            text = buf.getvalue()
            self.assertEqual(rc, 0, text)
            sess = json.loads((root / ".memory-art" / "converge" / "prep-1.json").read_text(encoding="utf-8"))
            self.assertEqual(sess.get("opened_by"), "prepare")
            grid = (sess.get("understanding_contract") or {}).get("grid") or {}
            self.assertIn("同一只青瓷小猫", grid.get("keep") or [])
            self.assertIn("不要文字", grid.get("forbid") or [])
            self.assertIn("emit-prompt", text)
            self.assertEqual(text.count("WARM_START_DEFERRED=1"), 1)
            self.assertEqual(text.count("收敛会话已启动"), 1)
            self.assertGreaterEqual(text.count("【Warm-Start"), 1)

    def test_failed_review_does_not_open_a_slot(self) -> None:
        from skills_kit.converge import _session_file, cmd_converge_prepare
        from skills_kit.parallel_slots import list_active_sessions

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data: dict = {"config": {"agent": {"max_parallel": 1}}, "modules": {}, "entries": []}
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = cmd_converge_prepare(
                    root,
                    data,
                    session_id="prep-bad",
                    goal="青瓷小猫蹲坐捧茶盏",
                    module="brand.WorldStyle",
                    scale="medium",
                    skip_route_gate=True,
                    skip_reason="unit test prepare reject",
                    reason_skill="ordinary",
                    reason_draft="",
                    revised="",
                    checklist="",
                )
            self.assertEqual(rc, 1, buf.getvalue())
            self.assertFalse(_session_file(root, "prep-bad").exists())
            self.assertEqual(list_active_sessions(root, data), [])


if __name__ == "__main__":
    unittest.main()
