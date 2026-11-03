"""Reasonableness gate: checklist + revised prompt before first generate."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from skills_kit.reasonableness_gate import (  # noqa: E402
    apply_review_to_session,
    check_reasonableness_gate,
    default_checklist_template,
    normalize_skill,
    parse_checklist,
    review_reasonableness,
)
from skills_kit.converge import cmd_converge, _session_file  # noqa: E402


class TestNormalizeAndParse(unittest.TestCase):
    def test_aliases(self) -> None:
        self.assertEqual(normalize_skill("图标A"), "icon.a")
        self.assertEqual(normalize_skill("合成梯"), "merge")
        self.assertEqual(normalize_skill("普通图"), "ordinary")

    def test_parse_checklist(self) -> None:
        d = parse_checklist("subject_action=ok;element_budget=fail:窗外太满")
        self.assertEqual(d["subject_action"]["status"], "ok")
        self.assertEqual(d["element_budget"]["status"], "fail")
        self.assertIn("窗外", d["element_budget"]["note"])


class TestReview(unittest.TestCase):
    def test_pass_ordinary(self) -> None:
        chk = default_checklist_template("ordinary")
        rev = (
            "红发女子抱哭婴坐在破窗前，圣诞毛衣大色块少碎纹；"
            "窗台只留一支小烛，窗外最多极淡光点；满幅叙事插画，无字。"
            "一眼失败：窗外灯村堆满或毛衣细雪花噪声。"
        )
        out = review_reasonableness(
            skill="ordinary",
            draft="圣诞女人抱婴儿",
            revised=rev,
            checklist_text=chk,
        )
        self.assertTrue(out["passed"], out["issues"])

    def test_fail_missing_checklist(self) -> None:
        out = review_reasonableness(
            skill="ordinary",
            draft="a" * 40,
            revised="主体站立握手接触清楚，元素预算最多两件道具，硬锁竖构图无字，一眼失败是多手。",
            checklist_text="subject_action=ok",
        )
        self.assertFalse(out["passed"])
        self.assertTrue(any("清单未齐" in x for x in out["issues"]))

    def test_icon_a_requires_safe_zone(self) -> None:
        chk = default_checklist_template("icon.a")
        out = review_reasonableness(
            skill="icon.a",
            draft="圣诞 app icon",
            revised="双人剪影满幅直角 1024 无字，单符号叙事。",
            checklist_text=chk,
        )
        self.assertFalse(out["passed"])
        self.assertTrue(any("安全区" in x for x in out["issues"]))

    def test_icon_a_pass(self) -> None:
        chk = default_checklist_template("icon.a")
        rev = (
            "1024 满幅直角 App Icon；红发女抱哭婴圣诞装单符号；"
            "主体落在 72%-80% 安全区；无字；窗外只留极淡光点预算。"
            "一眼失败：贴边或细碎灯串糊成噪点。"
        )
        out = review_reasonableness(
            skill="icon.a", draft="icon draft", revised=rev, checklist_text=chk
        )
        self.assertTrue(out["passed"], out["issues"])

    def test_keyart_requires_layout_not_style_echo(self) -> None:
        self.assertIn("layout_not_style_echo", default_checklist_template("keyart"))
        chk = default_checklist_template("keyart")
        bad = review_reasonableness(
            skill="keyart",
            draft="主视觉",
            revised="照着样张构图再画一张节日主视觉，参考分区不变。",
            checklist_text=chk,
        )
        self.assertFalse(bad["passed"])
        self.assertTrue(any("layout" in x or "构图" in x for x in bad["issues"]))
        good_rev = (
            "节日主视觉：新机位俯视大圆桌，只借画风色板与暖光；"
            "不贴样张构图；主体动作清楚；元素预算桌面三件道具；"
            "硬锁 16:9 无字；一眼失败是贴回样张左右分区。"
        )
        good = review_reasonableness(
            skill="keyart",
            draft="主视觉",
            revised=good_rev,
            checklist_text=chk,
        )
        self.assertTrue(good["passed"], good["issues"])


class TestSessionGate(unittest.TestCase):
    def test_generate_blocked_then_unlocked(self) -> None:
        # Session exclusion: must start before generate; never auto-create session.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data: dict = {"config": {"converge": {}}}
            rc = cmd_converge(
                root,
                data,
                "start",
                session_id="reas-test",
                goal="测试合理性闸",
                module="brand.WorldStyle",
                skip_route_gate=True,
            )
            self.assertEqual(rc, 0)
            rc2 = cmd_converge(
                root,
                data,
                "generate",
                session_id="reas-test",
                round_num=1,
                image="",
                prompt="随便画一张",
                skip_route_gate=True,
            )
            self.assertEqual(rc2, 1)

            sf = _session_file(root, "reas-test")
            sess = json.loads(sf.read_text(encoding="utf-8"))
            chk = default_checklist_template("ordinary")
            rev = (
                "青瓷小猫蹲坐捧茶盏，爪与盏接触清楚；背景最多一扇窗；"
                "竖构图无字；一眼失败是多爪或茶盏漂浮。"
            )
            review = review_reasonableness(
                skill="ordinary",
                draft="青瓷小猫",
                revised=rev,
                checklist_text=chk,
            )
            self.assertTrue(review["passed"], review["issues"])
            sess = apply_review_to_session(sess, review)
            sf.write_text(json.dumps(sess, ensure_ascii=False, indent=2), encoding="utf-8")

            ok, msg, prompt_use = check_reasonableness_gate(sess, round_num=1, prompt="")
            self.assertTrue(ok, msg)
            self.assertEqual(prompt_use, rev)

            ok2, _, prompt2 = check_reasonableness_gate(sess, round_num=1, prompt="青瓷小猫")
            self.assertTrue(ok2)
            self.assertEqual(prompt2, rev)

    def test_round2_cannot_skip_without_review(self) -> None:
        """Empty rounds + --round 2 must still require reasonableness (no loophole)."""
        sess = {"rounds": [], "reasonableness": None}
        ok, msg, _ = check_reasonableness_gate(sess, round_num=2, prompt="skip?")
        self.assertFalse(ok)
        self.assertIn("合理性审核", msg)

    def test_icon_a_requires_no_text_phrase(self) -> None:
        chk = default_checklist_template("icon.a")
        out = review_reasonableness(
            skill="icon.a",
            draft="app icon",
            revised="1024 满幅直角，主体在 75% 安全区，单符号剪影。",
            checklist_text=chk,
        )
        self.assertFalse(out["passed"])
        self.assertTrue(any("无字" in x for x in out["issues"]))

    def test_first_generate_forces_revised(self) -> None:
        rev = "青瓷小猫蹲坐捧茶盏，爪与盏接触清楚；背景最多一扇窗；竖构图无字；一眼失败是多爪。"
        sess = {
            "rounds": [],
            "reasonableness": {
                "passed": True,
                "revised_prompt": rev,
                "draft_prompt": "小猫",
            },
        }
        ok, msg, prompt_use = check_reasonableness_gate(
            sess, round_num=1, prompt="totally different unreviewed prompt"
        )
        self.assertTrue(ok)
        self.assertEqual(prompt_use, rev)
        self.assertIn("强制", msg)

    def test_later_round_empty_prompt_falls_back_to_revised(self) -> None:
        rev = "青瓷小猫蹲坐捧茶盏，爪与盏接触清楚；背景最多一扇窗；竖构图无字；一眼失败是多爪。"
        sess = {
            "rounds": [{"round": 1, "image": "r1.png"}],
            "reasonableness": {
                "passed": True,
                "revised_prompt": rev,
                "draft_prompt": "小猫",
            },
        }
        ok, msg, prompt_use = check_reasonableness_gate(sess, round_num=2, prompt="")
        self.assertTrue(ok)
        self.assertEqual(prompt_use, rev)
        self.assertIn("回退", msg)


if __name__ == "__main__":
    unittest.main()
