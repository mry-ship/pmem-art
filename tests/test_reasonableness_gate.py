"""Reasonableness gate: checklist + revised prompt before first generate."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("PMEM_ART_ALLOW_GATE_SKIP", "1")
os.environ.setdefault("PMEM_ART_UNDER_TEST", "1")

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
        self.assertEqual(normalize_skill("lens"), "shotpack")
        self.assertEqual(normalize_skill("镜头包"), "shotpack")
        self.assertEqual(normalize_skill("镜头"), "shotpack")
        self.assertEqual(normalize_skill("draw.lens"), "shotpack")
        self.assertEqual(normalize_skill("多图"), "split")
        self.assertEqual(normalize_skill("multi"), "split")
        self.assertEqual(normalize_skill("draw.multi"), "split")
        self.assertEqual(normalize_skill("合成"), "merge")
        self.assertEqual(normalize_skill("merge.ladder"), "merge")
        self.assertEqual(normalize_skill("UI kit"), "ui")
        self.assertEqual(normalize_skill("ui.kit"), "ui")
        self.assertEqual(normalize_skill("整表"), "merge")
        self.assertEqual(normalize_skill("icon"), "icon.unspecified")
        self.assertEqual(normalize_skill("图标"), "icon.unspecified")
        self.assertNotEqual(normalize_skill("icon"), "icon.a")
        self.assertNotEqual(normalize_skill("icon"), "ordinary")
        self.assertNotEqual(normalize_skill("镜头"), "ordinary")
        self.assertNotEqual(normalize_skill("draw.lens"), "ordinary")

    def test_bare_icon_fails_review(self) -> None:
        out = review_reasonableness(
            skill="图标",
            draft="画个图标",
            revised="随便画",
            checklist_text="subject_action=ok",
        )
        self.assertFalse(out["passed"])
        self.assertTrue(any("icon.a" in x or "图标A" in x for x in out["issues"]), out["issues"])

    def test_merge_checklist_not_same_object_only(self) -> None:
        chk = default_checklist_template("merge")
        self.assertIn("chain_mode_declared=ok", chk)
        self.assertIn("upgrade_reason_concrete=ok", chk)
        self.assertIn("family_or_base_lock=ok", chk)
        self.assertNotIn("parts_add_concrete=ok", chk)
        self.assertNotIn("base_body_retained=ok", chk)

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
            "1024 满幅直角 App Icon，四角顶边无圆角蒙版；红发女抱哭婴圣诞装单符号；"
            "主体落在 72%-80% 安全区；无字；窗外只留极淡光点预算。"
            "一眼失败：贴边、烤进圆角底板或细碎灯串糊成噪点。"
        )
        out = review_reasonableness(
            skill="icon.a", draft="icon draft", revised=rev, checklist_text=chk
        )
        self.assertTrue(out["passed"], out["issues"])

    def test_icon_a_rejects_round_mask(self) -> None:
        chk = default_checklist_template("icon.a")
        out = review_reasonableness(
            skill="icon.a",
            draft="app icon",
            revised="1024 圆角底板 App Icon，主体 75% 安全区，无字单符号。",
            checklist_text=chk,
        )
        self.assertFalse(out["passed"])
        self.assertTrue(any("圆角" in x or "满幅" in x for x in out["issues"]))

    def test_ui_rejects_illustration_pad(self) -> None:
        chk = default_checklist_template("ui")
        out = review_reasonableness(
            skill="ui",
            draft="主菜单",
            revised="顶栏资源+中央Play，场景插画垫图出主菜单。",
            checklist_text=chk,
            notes="场景插画垫图当UI参考",
        )
        self.assertFalse(out["passed"])
        self.assertTrue(any("插画" in x or "控件" in x for x in out["issues"]))
        # 电池翻车口语：叙事插画裁切当 UI 参考
        out2 = review_reasonableness(
            skill="ui",
            draft="主菜单",
            revised=(
                "商业休闲主菜单：顶栏资源珠、中央主按钮；描边体积投影字重；"
                "主按钮不遮脸；无乱码；一眼失败是插画海报。"
            ),
            checklist_text=chk,
            notes="垫图：rm_prop_ui_crop 叙事插画裁切当UI参考",
        )
        self.assertFalse(out2["passed"])
        self.assertTrue(any("插画" in x for x in out2["issues"]), out2["issues"])

    def test_soft_candy_material_inherits_on_clone_variant(self) -> None:
        for skill in ("clone", "variant", "merge"):
            chk = default_checklist_template(skill)
            bad = review_reasonableness(
                skill=skill,
                draft="草莓软糖道具",
                revised="硬塑胶抛光塑料草莓玩具，黑底居中，无字。",
                checklist_text=chk,
            )
            self.assertFalse(bad["passed"], skill)
            self.assertTrue(
                any("软糖" in x or "硬塑" in x for x in bad["issues"]),
                (skill, bad["issues"]),
            )

    def test_merge_ban_gift_phrase_not_false_positive(self) -> None:
        chk = default_checklist_template("merge")
        rev = (
            "shop_ladder 草莓软糖单件居中：锁家族色相与软糖介质；evolve_to 可读；"
            "合成理由具体；禁止装饰换装断故事；软糖半透明 SSS；"
            "一眼失败是礼盒奖杯乱跳换货或硬塑胶。"
        )
        out = review_reasonableness(
            skill="merge", draft="草莓软糖合成梯", revised=rev, checklist_text=chk
        )
        self.assertTrue(out["passed"], out["issues"])

    def test_icon_a_long_fail_at_glance_not_false_positive(self) -> None:
        chk = default_checklist_template("icon.a")
        rev = (
            "1024 满幅直角 App Icon，主体 75% 安全区，无字单符号；"
            "一眼失败包括：主体贴边、安全区不够、角区露白、以及烤进圆角底板。"
        )
        out = review_reasonableness(
            skill="icon.a", draft="app icon", revised=rev, checklist_text=chk
        )
        self.assertTrue(out["passed"], out["issues"])

    def test_ui_catches_colloquial_illustration_pads(self) -> None:
        chk = default_checklist_template("ui")
        chrome = (
            "顶栏资源珠、中央主按钮；描边体积投影字重；主按钮不遮脸；无乱码。"
        )
        for note in (
            "茶会庆祝场景裁切当界面母版",
            "把立绘当界面参考",
            "插画当界面母版",
            "把插画海报当主菜单",
        ):
            out = review_reasonableness(
                skill="ui",
                draft="主菜单",
                revised=chrome,
                checklist_text=chk,
                notes=note,
            )
            self.assertFalse(out["passed"], note)
            self.assertTrue(any("插画" in x for x in out["issues"]), (note, out["issues"]))

    def test_soft_candy_fail_at_glance_hard_plastic_ok(self) -> None:
        chk = default_checklist_template("clone")
        rev = (
            "草莓软糖半透明 SSS 宽柔高光，黑底居中无字；"
            "一眼失败是硬塑胶抛光塑料玩具。"
        )
        out = review_reasonableness(
            skill="clone", draft="草莓软糖", revised=rev, checklist_text=chk
        )
        self.assertTrue(out["passed"], out["issues"])

    def test_merge_same_object_requires_mother_retention_phrase(self) -> None:
        chk = default_checklist_template("merge")
        bad = review_reasonableness(
            skill="merge",
            draft="合成梯",
            revised="same_object 草莓软糖单件居中，软糖半透明 SSS，黑底。",
            checklist_text=chk,
        )
        self.assertFalse(bad["passed"])
        self.assertTrue(any("母体" in x for x in bad["issues"]), bad["issues"])

    def test_merge_shop_ladder_does_not_require_parts_add_keys(self) -> None:
        chk = default_checklist_template("merge")
        rev = (
            "shop_ladder 草莓软糖单件居中：锁家族色相；evolve_to 糖纸→罐装可读；"
            "merge_why 两件同级合成升级包装；软糖半透明 SSS；一眼失败是装饰换装断故事。"
        )
        out = review_reasonableness(
            skill="merge", draft="软糖合成梯", revised=rev, checklist_text=chk
        )
        self.assertTrue(out["passed"], out["issues"])

    def test_merge_light_gate_ok_without_same_object_parts(self) -> None:
        chk = default_checklist_template("merge")
        rev = (
            "轻门：木屋建造单件居中，同任务域棚→框架→封皮；每档体量只大一圈；"
            "升级理由具体可读；一眼失败是跨店乱跳或回退。"
        )
        out = review_reasonableness(
            skill="merge", draft="木屋合成梯", revised=rev, checklist_text=chk
        )
        self.assertTrue(out["passed"], out["issues"])

    def test_wu_zi_does_not_negate_hard_plastic(self) -> None:
        """「无字」不得把后面的肯定硬塑当成已禁止。"""
        chk = default_checklist_template("clone")
        out = review_reasonableness(
            skill="clone",
            draft="草莓软糖",
            revised="草莓软糖半透明 SSS，黑底居中无字；硬塑胶抛光塑料质感。",
            checklist_text=chk,
        )
        self.assertFalse(out["passed"])
        self.assertTrue(any("硬塑" in x for x in out["issues"]), out["issues"])

    def test_split_ban_closed_lock_phrase_not_false_positive(self) -> None:
        chk = default_checklist_template("split")
        for rev in (
            "软塑胶宝箱开盖态：铰链可见，挂锁解锁移除，只改盖；黑底居中；禁止闭锁开盖同框。",
            "软塑胶宝箱开盖态；禁止闭锁开盖；铰链可见，挂锁解锁移除，只改盖；黑底居中。",
        ):
            out = review_reasonableness(
                skill="split", draft="宝箱打开", revised=rev, checklist_text=chk
            )
            self.assertTrue(out["passed"], (rev, out["issues"]))

    def test_ui_illustration_poster_pad_blocked(self) -> None:
        chk = default_checklist_template("ui")
        chrome = (
            "顶栏资源珠、中央主按钮；描边体积投影字重；主按钮不遮脸；无乱码。"
        )
        out = review_reasonableness(
            skill="ui",
            draft="主菜单",
            revised=chrome,
            checklist_text=chk,
            notes="插画海报垫",
        )
        self.assertFalse(out["passed"])
        self.assertTrue(any("插画" in x for x in out["issues"]), out["issues"])

    def test_bie_hard_plastic_negates(self) -> None:
        chk = default_checklist_template("clone")
        out = review_reasonableness(
            skill="clone",
            draft="草莓软糖",
            revised="草莓软糖半透明 SSS，黑底居中；勿硬塑胶抛光塑料。",
            checklist_text=chk,
        )
        self.assertTrue(out["passed"], out["issues"])

    def test_ui_pass_chrome_spec(self) -> None:
        chk = default_checklist_template("ui")
        rev = (
            "商业休闲主菜单 9:16：顶栏三资源珠、侧栏设置商店、中央主按钮；"
            "控件工艺统一描边+体积投影+字重；主按钮不遮脸；"
            "场景铺底控件叠层；无乱码；一眼失败是叙事插画海报或 CTA 压脸。"
        )
        out = review_reasonableness(
            skill="ui", draft="主菜单", revised=rev, checklist_text=chk
        )
        self.assertTrue(out["passed"], out["issues"])

    def test_keyart_requires_layout_not_style_echo(self) -> None:
        self.assertIn("layout_not_style_echo", default_checklist_template("keyart"))
        self.assertIn("framing_lock", default_checklist_template("keyart"))
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
            "节日主视觉：新机位俯视中景大圆桌，只借画风色板与暖光；"
            "不贴样张构图；主体动作清楚；元素预算桌面三件道具；"
            "硬锁 16:9 无字；一眼失败是贴回样张左右分区或改成全身群像。"
        )
        good = review_reasonableness(
            skill="keyart",
            draft="主视觉",
            revised=good_rev,
            checklist_text=chk,
        )
        self.assertTrue(good["passed"], good["issues"])

    def test_split_open_needs_state_machine(self) -> None:
        chk = default_checklist_template("split")
        bad = review_reasonableness(
            skill="split",
            draft="宝箱打开",
            revised="软塑胶宝箱开盖露金币，黑底居中，锁机位。",
            checklist_text=chk,
        )
        self.assertFalse(bad["passed"])
        self.assertTrue(any("状态机" in x or "铰链" in x for x in bad["issues"]))
        good = review_reasonableness(
            skill="split",
            draft="宝箱打开",
            revised=(
                "软塑胶宝箱开盖态：铰链可见，挂锁解锁移除，只改盖；"
                "同机关闭态机位；黑底居中；一眼失败是闭合挂锁仍挂着。"
            ),
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
