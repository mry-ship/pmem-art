from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from skills_kit.converge_loop import loop_followup, mark_active_session  # noqa: E402
from skills_kit.understanding_contract import (  # noqa: E402
    apply_feedback,
    build_contract,
    classify_feedback,
    cmd_contract,
    contract_from_session_bootstrap,
    defaults_visibility_ok,
    ensure_session_contract,
    format_working_set,
    resolve_contract_session_id,
    working_set_from_session,
)


class TestUnderstandingContract(unittest.TestCase):
    def test_classify_layers(self) -> None:
        self.assertEqual(classify_feedback("不对，走错技能了")["layer"], "l0")
        self.assertEqual(classify_feedback("不符合预期")["layer"], "l0")
        self.assertEqual(classify_feedback("这张对不上，差太远")["layer"], "l0")
        self.assertEqual(classify_feedback("不是我想要的效果")["layer"], "l0")
        self.assertEqual(classify_feedback("机位不要动")["layer"], "l1")
        self.assertEqual(classify_feedback("手再小一点")["layer"], "l2")
        self.assertEqual(classify_feedback("再高级点")["layer"], "l2")
        # 裸「作废」不得误杀成 L0；明确整套作废才升 L0
        self.assertEqual(classify_feedback("这版方案作废，把手修小一点")["layer"], "l2")
        self.assertEqual(classify_feedback("刚才那套作废")["layer"], "l0")
        self.assertEqual(classify_feedback("全部作废")["layer"], "l0")

    def test_defaults_visibility(self) -> None:
        empty = build_contract(raw_utterance="画一张")
        ok, _ = defaults_visibility_ok(empty)
        self.assertFalse(ok)
        filled = build_contract(defaults_shown=["默认：水彩绘本气质"])
        ok2, msg = defaults_visibility_ok(filled)
        self.assertTrue(ok2)
        self.assertIn("水彩", msg)

    def test_apply_feedback_l2_updates_surface(self) -> None:
        c = build_contract(route_ids=["draw.ordinary"], delivery="draw.ordinary")
        c2 = apply_feedback(c, "颜色再暖一点")
        self.assertEqual(c2["l2"]["feedback_layer"], "l2")
        self.assertIn("暖", c2["l2"]["surface_fix"])

    def test_apply_feedback_l0_notes_reopen(self) -> None:
        c = build_contract(route_ids=["draw.ordinary"])
        c2 = apply_feedback(c, "不对，我要的是图标")
        self.assertEqual(c2["l2"]["feedback_layer"], "l0")
        self.assertIn("L0", c2["notes"])

    def test_working_set_mentions_single_fix(self) -> None:
        c = contract_from_session_bootstrap(
            goal="窗边女孩",
            route_ids=["draw.ordinary"],
            defaults_shown=["默认：水彩"],
        )
        text = format_working_set(c, session_id="t1", next_fix="只修右手")
        self.assertIn("最小工作集", text)
        self.assertIn("只修右手", text)
        self.assertIn("水彩", text)

    def test_cli_set_and_working_set(self) -> None:
        # 手工写会话文件测 contract CLI；不测 generate 无 start（仍须失败，见 Session 排除项）
        td = Path(tempfile.mkdtemp())
        folder = td / ".memory-art" / "converge"
        folder.mkdir(parents=True)
        sess = {
            "session_id": "uc1",
            "goal": "画一张窗边女孩",
            "route_ids": ["draw.ordinary"],
            "rounds": [
                {
                    "round": 1,
                    "image": "r1.jpg",
                    "judged": True,
                    "score": 8.2,
                    "defects": "手指粘连",
                    "next_fix": "只分手",
                }
            ],
            "understanding_contract": build_contract(
                raw_utterance="画一张窗边女孩",
                route_ids=["draw.ordinary"],
                delivery="draw.ordinary",
            ),
        }
        (folder / "uc1.json").write_text(json.dumps(sess, ensure_ascii=False), encoding="utf-8")
        rc = cmd_contract(
            td,
            action="set",
            session_id="uc1",
            defaults="默认：水彩绘本",
            locks="身份",
            unlocks="光影细节",
            commercial_vibe="纸纹飞白",
        )
        self.assertEqual(rc, 0)
        data = json.loads((folder / "uc1.json").read_text(encoding="utf-8"))
        uc = data["understanding_contract"]
        self.assertIn("水彩", uc["l1"]["defaults_shown"][0])
        self.assertEqual(uc["l1"]["locks"], ["身份"])
        pack = working_set_from_session(data, session_id="uc1")
        self.assertIn("手指粘连", pack)
        self.assertIn("只分手", pack)
        rc2 = cmd_contract(td, action="defaults-check", session_id="uc1")
        self.assertEqual(rc2, 0)
        rc3 = cmd_contract(td, action="patch", session_id="uc1", feedback="手再小一点")
        self.assertEqual(rc3, 0)
        rc4 = cmd_contract(td, action="classify", text="再高级点")
        self.assertEqual(rc4, 0)

    def test_latest_remaps_to_active(self) -> None:
        td = Path(tempfile.mkdtemp())
        folder = td / ".memory-art" / "converge"
        folder.mkdir(parents=True)
        (folder / "cellA.json").write_text(
            json.dumps(
                {
                    "session_id": "cellA",
                    "goal": "g",
                    "route_ids": ["draw.ordinary"],
                    "understanding_contract": build_contract(
                        route_ids=["draw.ordinary"], delivery="draw.ordinary"
                    ),
                    "rounds": [],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        mark_active_session(td, "cellA")
        sid, note = resolve_contract_session_id(td, "latest")
        self.assertEqual(sid, "cellA")
        self.assertIn("cellA", note)
        rc = cmd_contract(td, action="show", session_id="latest")
        self.assertEqual(rc, 0)

    def test_legacy_session_show_matches_working_set_l0(self) -> None:
        sess = {
            "goal": "旧会话",
            "route_ids": ["draw.multi"],
            "contract": "split",
            "rounds": [],
        }
        c = ensure_session_contract(sess)
        self.assertEqual(c["l0"]["delivery"], "draw.multi")
        pack = working_set_from_session(sess, session_id="old")
        self.assertIn("draw.multi", pack)

    def test_loop_followup_includes_working_set(self) -> None:
        td = Path(tempfile.mkdtemp())
        folder = td / ".memory-art" / "converge"
        folder.mkdir(parents=True)
        sess = {
            "status": "continue",
            "accept_threshold": 9.5,
            "max_rounds": 4,
            "route_ids": ["draw.ordinary"],
            "understanding_contract": build_contract(
                route_ids=["draw.ordinary"],
                delivery="draw.ordinary",
                defaults_shown=["默认：测试气质"],
            ),
            "rounds": [
                {
                    "round": 1,
                    "image": "r1.jpg",
                    "judged": True,
                    "score": 8.0,
                    "defects": "透视塌",
                    "next_fix": "只修透视",
                }
            ],
        }
        (folder / "ws1.json").write_text(json.dumps(sess, ensure_ascii=False), encoding="utf-8")
        mark_active_session(td, "ws1")
        hit = loop_followup(td, "ws1")
        self.assertEqual(hit["reason"], "need_next_round")
        self.assertIn("最小工作集", hit["message"])
        self.assertIn("测试气质", hit["message"])

    def test_l1_patch_short_lock_not_full_sentence(self) -> None:
        c = build_contract(route_ids=["draw.ordinary"])
        c2 = apply_feedback(c, "机位不要动，别改构图")
        self.assertEqual(c2["l2"]["feedback_layer"], "l1")
        self.assertTrue(any("机位" in x for x in c2["l1"]["locks"]))
        self.assertTrue(any("构图" in x for x in c2["l1"]["locks"]))
        self.assertTrue(all(len(x) <= 24 for x in c2["l1"]["locks"]))
        self.assertIn("机位不要动", c2["notes"])

    def test_split_only_legacy_delivery(self) -> None:
        sess = {"goal": "多图", "contract": "split", "rounds": []}
        c = ensure_session_contract(sess)
        self.assertEqual(c["l0"]["delivery"], "split")

    def test_show_persists_missing_contract(self) -> None:
        td = Path(tempfile.mkdtemp())
        folder = td / ".memory-art" / "converge"
        folder.mkdir(parents=True)
        (folder / "legacy.json").write_text(
            json.dumps(
                {"session_id": "legacy", "goal": "旧", "route_ids": ["draw.ordinary"], "rounds": []},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        rc = cmd_contract(td, action="show", session_id="legacy")
        self.assertEqual(rc, 0)
        data = json.loads((folder / "legacy.json").read_text(encoding="utf-8"))
        self.assertIn("understanding_contract", data)
        self.assertEqual(data["understanding_contract"]["l0"]["delivery"], "draw.ordinary")


if __name__ == "__main__":
    unittest.main()
