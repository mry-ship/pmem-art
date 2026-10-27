"""Hard-path wiring for anatomy veto, pad=auto, R1 floor, early-stop policy."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from skills_kit.converge_policy import (  # noqa: E402
    DEFAULT_ANATOMY_FLOOR,
    DEFAULT_EARLY_STOP_MIN_ROUND,
    DEFAULT_REGRESSION_DROP,
    anatomy_ok_for_stop,
    clone_subject_structure_ok_for_stop,
    decide_round_stop,
    plate_safe_to_pad,
    scale_lock_marked,
    ui_shell_structure_ok_for_stop,
)
from skills_kit.scoring import audit_score_inflation  # noqa: E402
from skills_kit.judge_auto import auto_vlm_judge_image  # noqa: E402
from skills_kit.prompt_scale import (  # noqa: E402
    build_r1_structure_floor,
    compose_style_first_prompt,
    get_converge_scale_profile,
)
from skills_kit.subject_lexicon import to_prompt_english  # noqa: E402
from skills_kit.converge import _resolve_pad_auto  # noqa: E402


class TestPolicyDefaults(unittest.TestCase):
    def test_defaults_match_docs(self) -> None:
        self.assertEqual(DEFAULT_ANATOMY_FLOOR, 7.5)
        self.assertEqual(DEFAULT_REGRESSION_DROP, 0.5)
        self.assertEqual(DEFAULT_EARLY_STOP_MIN_ROUND, 4)

    def test_early_stop_ignored_before_r4(self) -> None:
        self.assertIsNone(
            decide_round_stop(
                score_ok=True,
                total=8.0,
                dims={"perspective_anatomy": 9.0},
                round_num=3,
                min_rounds=1,
                threshold=9.6,
                anatomy_floor=7.5,
                best_total=9.0,
                no_improve_streak=5,
                regression_drop=0.5,
                early_stop_min_round=4,
            )
        )

    def test_regression_fires_at_r4(self) -> None:
        self.assertEqual(
            decide_round_stop(
                score_ok=True,
                total=8.0,
                dims={"perspective_anatomy": 9.0},
                round_num=4,
                min_rounds=1,
                threshold=9.6,
                anatomy_floor=7.5,
                best_total=9.0,
                no_improve_streak=0,
                regression_drop=0.5,
                early_stop_min_round=4,
            ),
            "STOP_REGRESSION",
        )

    def test_missing_anat_fail_closed(self) -> None:
        self.assertFalse(anatomy_ok_for_stop(None))
        self.assertFalse(anatomy_ok_for_stop({"composition": 9.9}))
        self.assertTrue(anatomy_ok_for_stop({"perspective_anatomy": 7.5}))


class TestR1Floor(unittest.TestCase):
    def test_ui_empty(self) -> None:
        self.assertEqual(build_r1_structure_floor(goal="主菜单 HUD 九宫格", module="ui.hud"), "")

    def test_ui_shell_clone_injects_floor(self) -> None:
        goal = "空内容弹框母版，中心留白可拉伸，禁止礼盒"
        s = build_r1_structure_floor(goal=goal, module="ui.PopupClone")
        self.assertIn("stretchable", s.lower())
        self.assertIn("gift box", s.lower())
        zh = build_r1_structure_floor(goal=goal, module="ui.PopupClone", lang="zh")
        self.assertIn("留白", zh)

    def test_popupclone_default_shell_floor(self) -> None:
        s = build_r1_structure_floor(goal="Clone UI 弹窗", module="ui.PopupClone")
        self.assertIn("9-slice", s.lower())

    def test_popupclone_negated_reward_illustration_injects_shell_floor(self) -> None:
        goal = (
            "Clone Mode B UI。新题材：空内容弹框九宫格母版（非奖励插画）。"
            "中心大面积留白，禁止礼盒画进内容区。"
        )
        ra = "参考是道具icon不是弹窗布局，弹窗只借材质与描边语法。"
        s = build_r1_structure_floor(goal=goal, ref_analysis=ra, module="ui.PopupClone")
        self.assertIn("9-slice", s.lower())
        self.assertIn("gift box", s.lower())

    def test_clone_mode_b_icon_injects_subject_floor(self) -> None:
        s = build_r1_structure_floor(
            goal="Clone Mode B icon 新题材钥匙",
            module="icon.KeyClone",
            ref_image="docs/ref.png",
        )
        self.assertIn("photocopy", s.lower())
        self.assertIn("gift box", s.lower())

    def test_character_joints_english_in_prompt_chinese_for_display(self) -> None:
        s = build_r1_structure_floor(goal="少女全身立绘", module="character.Hero")
        self.assertIn("joint", s.lower())
        self.assertIn("pupil", s.lower())
        zh = build_r1_structure_floor(goal="少女全身立绘", module="character.Hero", lang="zh")
        self.assertIn("关节", zh)
        self.assertIn("瞳孔", zh)

    def test_empty_scene(self) -> None:
        s = build_r1_structure_floor(goal="空镜无人峡谷", module="scene.Canyon")
        self.assertIn("vanishing", s.lower())
        self.assertNotIn("pupil", s.lower())
        self.assertNotIn("山体", s)
        zh = build_r1_structure_floor(goal="空镜无人峡谷", module="scene.Canyon", lang="zh")
        self.assertIn("灭点", zh)

    def test_vague_brief_injects_nothing(self) -> None:
        self.assertEqual(build_r1_structure_floor(goal="画一张漂亮的图", module="brand.WorldStyle"), "")

    def test_english_knight_not_command(self) -> None:
        knight = build_r1_structure_floor(goal="a knight in armor", module="")
        self.assertIn("joint", knight.lower())
        self.assertEqual(build_r1_structure_floor(goal="command a fleet of ships", module=""), "")

    def test_woman_is_human_not_man_substring(self) -> None:
        s = build_r1_structure_floor(goal="a woman portrait", module="")
        self.assertIn("pupil", s.lower())

    def test_creature_is_not_human_elbows(self) -> None:
        for goal in ("a cat sitting", "一只猫咪", "a dragon", "a fox", "一只鹿"):
            s = build_r1_structure_floor(goal=goal, module="character.Pet")
            self.assertIn("species", s.lower(), goal)
            self.assertNotIn("pupil", s.lower(), goal)
            zh = build_r1_structure_floor(goal=goal, module="character.Pet", lang="zh")
            self.assertNotIn("双肩双肘", zh, goal)

    def test_mechanical_is_not_human_eyes(self) -> None:
        s = build_r1_structure_floor(goal="a robot mecha", module="")
        self.assertIn("mechanical", s.lower())
        self.assertNotIn("pupil", s.lower())
        zh = build_r1_structure_floor(goal="一台机器人", module="", lang="zh")
        self.assertIn("机械关节", zh)

    def test_character_module_without_species_is_generic(self) -> None:
        s = build_r1_structure_floor(goal="一张立绘", module="character.Pet")
        self.assertIn("silhouette", s.lower())
        self.assertNotIn("pupil", s.lower())

    def test_mention_ui_does_not_steal_a_person(self) -> None:
        s = build_r1_structure_floor(goal="少女站在界面前", module="")
        self.assertIn("pupil", s.lower())
        self.assertIn("joint", build_r1_structure_floor(goal="a knight holding a menu", module="").lower())
        self.assertEqual(build_r1_structure_floor(goal="画一套主菜单", module=""), "")
        self.assertEqual(build_r1_structure_floor(goal="a menu of dishes", module=""), "")

    def test_phone_is_not_a_hand(self) -> None:
        self.assertEqual(build_r1_structure_floor(goal="一只手机", module=""), "")

    def test_path_and_false_friends_do_not_reclassify(self) -> None:
        canyon = dict(goal="空镜峡谷", module="")
        self.assertIn("vanishing", build_r1_structure_floor(**canyon, ref_image="style_ref_03_sunlit_portrait.png").lower())
        self.assertIn("vanishing", build_r1_structure_floor(**canyon, ref_image="assets/ui/ref.png").lower())
        self.assertIn("joint", build_r1_structure_floor(goal="牛仔", module="").lower())
        self.assertNotIn("species", build_r1_structure_floor(goal="牛仔", module="").lower())
        self.assertIn("vanishing", build_r1_structure_floor(goal="无人机航拍峡谷", module="").lower())
        self.assertIn("vanishing", build_r1_structure_floor(goal="drone shot of a canyon", module="").lower())
        self.assertIn("mechanical", build_r1_structure_floor(goal="机甲站在峡谷", module="").lower())
        self.assertEqual(build_r1_structure_floor(goal="king bed", module=""), "")
        self.assertEqual(build_r1_structure_floor(goal="queen bed by the window", module=""), "")
        self.assertEqual(build_r1_structure_floor(goal="a bee line to the door", module=""), "")
        self.assertIn("species", build_r1_structure_floor(goal="a bee on a flower", module="").lower())
        self.assertIn("species", build_r1_structure_floor(goal="a pet portrait", module="").lower())
        self.assertNotIn("pupil", build_r1_structure_floor(goal="a pet portrait", module="").lower())
        self.assertIn("pupil", build_r1_structure_floor(goal="图标风格的角色", module="").lower())
        self.assertEqual(build_r1_structure_floor(goal="药水图标", module=""), "")
        self.assertIn("vanishing", build_r1_structure_floor(goal="鸟瞰峡谷", module="").lower())
        self.assertNotIn("species", build_r1_structure_floor(goal="鸟瞰峡谷", module="").lower())
        self.assertIn("species", build_r1_structure_floor(goal="一匹马在码头", module="").lower())
        self.assertEqual(build_r1_structure_floor(goal="马上出发", module=""), "")
        self.assertEqual(build_r1_structure_floor(goal="无人机航拍", module=""), "")
        self.assertIn("vanishing", build_r1_structure_floor(goal="空镜峡谷的 ui", module="").lower())
        self.assertIn("pupil", build_r1_structure_floor(goal="少女的 ui", module="").lower())
        self.assertEqual(build_r1_structure_floor(goal="app icon of a cat", module=""), "")
        self.assertEqual(build_r1_structure_floor(goal="a potion icon", module=""), "")
        self.assertEqual(build_r1_structure_floor(goal="a pet project", module=""), "")


class TestPadAuto(unittest.TestCase):
    def test_unsafe_plate_falls_back_to_ref(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            img = root / "r1.png"
            img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)
            ref = root / "ref.png"
            ref.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)
            rounds = [
                {
                    "round": 1,
                    "image": str(img),
                    "score": 9.7,
                    "next_fix": "修手",
                    "dims_parsed": {"perspective_anatomy": 6.5},
                }
            ]
            pad, fix, num, cont, reason = _resolve_pad_auto(
                rounds, 2, root, style_ref=str(ref), pad_mode="auto", anatomy_floor=7.5
            )
            self.assertFalse(cont)
            self.assertEqual(Path(pad).resolve(), ref.resolve())
            self.assertIn("style_ref", reason)

    def test_safe_plate_stays_on_style_ref(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            img = root / "r1.png"
            img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)
            ref = root / "ref.png"
            ref.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)
            rounds = [
                {
                    "round": 1,
                    "image": str(img),
                    "score": 9.2,
                    "next_fix": "修光影",
                    "dims_parsed": {"perspective_anatomy": 8.8},
                }
            ]
            pad, fix, num, cont, reason = _resolve_pad_auto(
                rounds, 2, root, style_ref=str(ref), pad_mode="auto", anatomy_floor=7.5
            )
            self.assertFalse(cont)
            self.assertEqual(Path(pad).resolve(), ref.resolve())
            self.assertEqual(num, 0)
            self.assertEqual(fix, "修光影")
            self.assertIn("style_ref", reason)
            self.assertFalse(plate_safe_to_pad(pad_mode="auto", dims={"perspective_anatomy": 8.8}))

    def test_style_jump_pads_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            img = root / "r1.png"
            img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)
            ref = root / "ref.png"
            ref.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)
            rounds = [
                {
                    "round": 1,
                    "image": str(img),
                    "score": 8.8,
                    "next_fix": "换剪影",
                    "dims_parsed": {"perspective_anatomy": 8.8},
                }
            ]
            pad, fix, _num, cont, reason = _resolve_pad_auto(
                rounds,
                2,
                root,
                style_ref=str(ref),
                pad_mode="auto",
                scale="recompose_bold",
            )
            self.assertEqual(pad, "")
            self.assertFalse(cont)
            self.assertEqual(fix, "换剪影")
            self.assertIn("style_jump", reason)

    def test_scale_or_eye_defect_does_not_chain(self) -> None:
        dims = {"perspective_anatomy": 9.6, "composition": 9.6}
        self.assertTrue(scale_lock_marked("巩膜月牙偏窄，道具仍偏小"))
        self.assertFalse(scale_lock_marked("巩膜月牙合格，禁黑点瞳"))
        self.assertFalse(scale_lock_marked("金齿偏珠宝光洁"))
        self.assertFalse(
            plate_safe_to_pad(pad_mode="auto", dims=dims, defects="巩膜月牙偏窄，蛋糕仍偏小")
        )
        self.assertFalse(
            plate_safe_to_pad(pad_mode="auto", dims=dims, defects="金齿偏珠宝光洁")
        )
        self.assertTrue(
            plate_safe_to_pad(pad_mode="previous", dims=dims, defects="巩膜月牙偏窄")
        )

    def test_scale_defect_resolve_falls_back_to_style_ref(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            img = root / "r1.png"
            img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)
            ref = root / "ref.png"
            ref.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)
            rounds = [
                {
                    "round": 1,
                    "image": str(img),
                    "score": 9.58,
                    "next_fix": "放大巩膜月牙",
                    "defects": "巩膜月牙偏窄，主体偏小",
                    "dims_parsed": {"perspective_anatomy": 9.6, "composition": 9.6},
                }
            ]
            pad, fix, num, cont, reason = _resolve_pad_auto(
                rounds, 2, root, style_ref=str(ref), pad_mode="auto", anatomy_floor=7.5
            )
            self.assertFalse(cont)
            self.assertEqual(Path(pad).resolve(), ref.resolve())
            self.assertIn("style_ref", reason)
            self.assertEqual(fix, "放大巩膜月牙")
            self.assertEqual(num, 0)

    def test_scene_low_perspective_does_not_chain(self) -> None:
        dims = {"perspective_anatomy": 4.2}
        self.assertFalse(
            plate_safe_to_pad(pad_mode="auto", dims=dims, subject_kind="scene", defects="灭点略偏")
        )
        self.assertFalse(
            plate_safe_to_pad(
                pad_mode="auto",
                dims={"perspective_anatomy": 5.9},
                subject_kind="scene",
                defects="灭点略偏",
            )
        )


class TestJudgeAnatomyVeto(unittest.TestCase):
    def _prof(self) -> dict:
        return get_converge_scale_profile("medium")

    def test_high_total_low_anat_blocks_stop(self) -> None:
        # high 档解剖权 15%：构图10/光影10/透视7.4/质感10/风格10 → 加权约 9.61，但解剖 <7.5 应熔断。
        with tempfile.TemporaryDirectory() as td:
            img = Path(td) / "x.png"
            img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 200)
            dims = "构图10/光影10/透视7.4/质感10/风格10"
            prof = get_converge_scale_profile("high")
            with mock.patch("skills_kit.judge_auto._physical_image_gate", return_value={"blocked": False, "reasons": [], "score_cap": None}):
                with mock.patch(
                    "skills_kit.judge_auto._inspect_image_physical_traits",
                    return_value={
                        "exists": True,
                        "size_bytes": 5000,
                        "size_kb": 5.0,
                        "width": 1024,
                        "height": 1024,
                        "aspect_ratio": "1:1",
                        "color_entropy": 4.0,
                    },
                ):
                    res = auto_vlm_judge_image(
                        str(img),
                        prof,
                        round_num=2,
                        dims=dims,
                        defects="左手腕融化进剑柄，关节不连续",
                        next_fix="已达标，无需继续叠加",
                        use_remote_vlm=False,
                        module="character.Hero",
                    )
        self.assertGreaterEqual(float(res.get("weighted_score") or 0), 9.6)
        self.assertTrue(res.get("anatomy_veto_blocked"))
        self.assertFalse(res.get("passed"))
        self.assertNotEqual(res.get("decision"), "STOP_TARGET_REACHED")
        self.assertLess(float(res.get("anatomy_score") or 0), 7.5)

    def test_missing_anat_dim_fail_closed(self) -> None:
        # 缺 perspective_anatomy 时即使其它维满分也不能 STOP（fail-closed）。
        with tempfile.TemporaryDirectory() as td:
            img = Path(td) / "x.png"
            img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 200)
            # Force dims_parsed without anatomy via audit path: incomplete string → no parse,
            # so inject by patching audit result after — instead call with full dims then
            # patch anatomy_ok path by using empty dims_parsed through module character.
            dims = "构图10/光影10/质感10/风格10/透视缺失"
            with mock.patch("skills_kit.judge_auto._physical_image_gate", return_value={"blocked": False, "reasons": [], "score_cap": None}):
                with mock.patch(
                    "skills_kit.judge_auto._inspect_image_physical_traits",
                    return_value={
                        "exists": True,
                        "size_bytes": 5000,
                        "size_kb": 5.0,
                        "width": 1024,
                        "height": 1024,
                        "aspect_ratio": "1:1",
                        "color_entropy": 4.0,
                    },
                ):
                    with mock.patch(
                        "skills_kit.judge_auto.audit_score_inflation",
                        return_value={
                            "calibrated_score": 9.7,
                            "dims_parsed": {
                                "composition": 10,
                                "lighting_color": 10,
                                "texture_detail": 10,
                                "spec_style": 10,
                            },
                            "weighted_score": 9.7,
                            "raw_score": 9.7,
                            "warnings": [],
                            "stagnated": False,
                        },
                    ):
                        res = auto_vlm_judge_image(
                            str(img),
                            get_converge_scale_profile("medium"),
                            round_num=2,
                            dims=dims,
                            defects="右手五指糊成一团，腕部断裂",
                            next_fix="",
                            use_remote_vlm=False,
                            module="character.Hero",
                        )
        self.assertTrue(res.get("anatomy_veto_blocked"))
        self.assertFalse(res.get("passed"))

    def test_clone_subject_echo_blocks_stop(self) -> None:
        self.assertFalse(
            clone_subject_structure_ok_for_stop(
                goal="Clone Mode B icon 新题材钥匙",
                module="icon.KeyClone",
                ref_image="ref.png",
                defects="完全抄参考心形礼盒",
                dims={"composition": 4.0},
            )
        )
        self.assertFalse(
            plate_safe_to_pad(
                pad_mode="auto",
                dims={"composition": 4.0, "perspective_anatomy": 9.0},
                defects="完全抄参考",
                goal="Clone Mode B icon 垫 ref 新题材钥匙",
                module="icon.KeyClone",
                ref_image="ref.png",
            )
        )

    def test_clone_subject_audit_caps_score(self) -> None:
        prof = {
            "goal": "Clone Mode B icon 新题材钥匙",
            "ref_image": "ref.png",
            "ref_analysis": "",
            "dim_weights": {
                "composition": 0.2,
                "lighting_color": 0.25,
                "perspective_anatomy": 0.2,
                "texture_detail": 0.2,
                "spec_style": 0.15,
            },
        }
        res = audit_score_inflation(
            9.7,
            "构图4.0/光影9.5/透视9.0/质感9.5/风格9.6",
            "完全抄参考礼盒主体",
            None,
            prof,
            module="icon.KeyClone",
        )
        self.assertLessEqual(float(res["calibrated_score"]), 8.85)

    def test_ui_shell_echo_blocks_stop(self) -> None:
        self.assertFalse(
            ui_shell_structure_ok_for_stop(
                goal="空内容弹框母版",
                module="ui.PopupClone",
                defects="中心有礼盒，抄参考主体",
            )
        )
        with tempfile.TemporaryDirectory() as td:
            img = Path(td) / "ui.png"
            img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 200)
            dims = "风格色板9.7/九宫格9.6/光影材质9.5/透明底合规9.5/状态族9.6"
            prof = get_converge_scale_profile("medium", goal="空内容弹框", module="ui.PopupClone")
            with mock.patch("skills_kit.judge_auto._physical_image_gate", return_value={"blocked": False, "reasons": [], "score_cap": None}):
                with mock.patch(
                    "skills_kit.judge_auto._inspect_image_physical_traits",
                    return_value={
                        "exists": True,
                        "size_bytes": 5000,
                        "size_kb": 5.0,
                        "width": 1024,
                        "height": 1024,
                        "aspect_ratio": "1:1",
                        "color_entropy": 4.0,
                    },
                ):
                    with mock.patch(
                        "skills_kit.judge_auto.audit_score_inflation",
                        return_value={
                            "calibrated_score": 9.68,
                            "dims_parsed": {
                                "style_palette": 9.7,
                                "nine_slice_structure": 9.6,
                                "lighting_material": 9.5,
                                "rgba_pipeline_compliance": 9.5,
                                "state_suite_cohesion": 9.6,
                            },
                            "weighted_score": 9.68,
                            "raw_score": 9.68,
                            "warnings": [],
                            "stagnated": False,
                            "rubric_mode": "ui_5d",
                        },
                    ):
                        res = auto_vlm_judge_image(
                            str(img),
                            prof,
                            round_num=2,
                            dims=dims,
                            defects="中心有礼盒，内容区非空中心",
                            next_fix="已达标",
                            use_remote_vlm=False,
                            module="ui.PopupClone",
                            goal="空内容弹框母版，禁止礼盒",
                        )
        self.assertTrue(res.get("ui_shell_veto_blocked"))
        self.assertFalse(res.get("passed"))

    def test_ui_module_skips_anat_veto(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            img = Path(td) / "ui.png"
            img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 200)
            # UI dedicated dims (no perspective_anatomy)
            dims = "风格色板9.7/九宫格9.6/光影材质9.5/透明底合规9.5/状态族9.6"
            with mock.patch("skills_kit.judge_auto._physical_image_gate", return_value={"blocked": False, "reasons": [], "score_cap": None}):
                with mock.patch(
                    "skills_kit.judge_auto._inspect_image_physical_traits",
                    return_value={
                        "exists": True,
                        "size_bytes": 5000,
                        "size_kb": 5.0,
                        "width": 1024,
                        "height": 1024,
                        "aspect_ratio": "1:1",
                        "color_entropy": 4.0,
                    },
                ):
                    res = auto_vlm_judge_image(
                        str(img),
                        self._prof(),
                        round_num=2,
                        dims=dims,
                        defects="内描边略糊，中缝拉伸区可读性不足",
                        next_fix="",
                        use_remote_vlm=False,
                        module="ui.hud",
                    )
        self.assertFalse(res.get("anatomy_veto_blocked"))

    def test_scene_mild_perspective_can_stop(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            img = Path(td) / "s.png"
            img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 200)
            dims = "构图10/光影10/透视7.4/质感10/风格10"
            with mock.patch("skills_kit.judge_auto._physical_image_gate", return_value={"blocked": False, "reasons": [], "score_cap": None}):
                with mock.patch(
                    "skills_kit.judge_auto._inspect_image_physical_traits",
                    return_value={
                        "exists": True, "size_bytes": 5000, "size_kb": 5.0,
                        "width": 1024, "height": 1024, "aspect_ratio": "1:1", "color_entropy": 4.0,
                    },
                ):
                    res = auto_vlm_judge_image(
                        str(img),
                        get_converge_scale_profile("high"),
                        round_num=2,
                        dims=dims,
                        defects="远处楼群灭点略散，接触阴影偏轻",
                        next_fix="收紧远景灭点",
                        use_remote_vlm=False,
                        module="scene.Canyon",
                        goal="空镜无人峡谷",
                    )
        self.assertFalse(res.get("anatomy_veto_blocked"))
        self.assertGreaterEqual(float(res.get("weighted_score") or 0), 9.6)

    def test_weak_next_fix_is_rewritten(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            img = Path(td) / "x.png"
            img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 200)
            dims = "构图8/光影8/透视7.0/质感8/风格8"
            with mock.patch("skills_kit.judge_auto._physical_image_gate", return_value={"blocked": False, "reasons": [], "score_cap": None}):
                with mock.patch(
                    "skills_kit.judge_auto._inspect_image_physical_traits",
                    return_value={
                        "exists": True, "size_bytes": 5000, "size_kb": 5.0,
                        "width": 1024, "height": 1024, "aspect_ratio": "1:1", "color_entropy": 4.0,
                    },
                ):
                    res = auto_vlm_judge_image(
                        str(img),
                        get_converge_scale_profile("medium"),
                        round_num=2,
                        dims=dims,
                        defects="左手腕融化",
                        next_fix="加强氛围",
                        use_remote_vlm=False,
                        module="character.Hero",
                        goal="少女全身立绘",
                    )
        self.assertNotIn("体积光", str(res.get("next_fix") or ""))
        self.assertIn("关节", str(res.get("next_fix") or ""))
        self.assertIn("joint", to_prompt_english(str(res.get("next_fix") or "")).lower())

    def test_scene_mild_5_9_can_stop(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            img = Path(td) / "s.png"
            img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 200)
            dims = "构图10/光影10/透视5.9/质感10/风格10"
            with mock.patch("skills_kit.judge_auto._physical_image_gate", return_value={"blocked": False, "reasons": [], "score_cap": None}):
                with mock.patch(
                    "skills_kit.judge_auto._inspect_image_physical_traits",
                    return_value={
                        "exists": True, "size_bytes": 5000, "size_kb": 5.0,
                        "width": 1024, "height": 1024, "aspect_ratio": "1:1", "color_entropy": 4.0,
                    },
                ):
                    res = auto_vlm_judge_image(
                        str(img),
                        get_converge_scale_profile("high"),
                        round_num=2,
                        dims=dims,
                        defects="远处楼群灭点略偏，接触阴影还在",
                        next_fix="收紧远景灭点",
                        use_remote_vlm=False,
                        module="scene.Canyon",
                        goal="空镜无人峡谷",
                    )
        self.assertFalse(res.get("anatomy_veto_blocked"))
        self.assertAlmostEqual(float(res.get("anatomy_score") or 0), 5.9, places=1)
        self.assertGreaterEqual(float(res.get("calibrated_score") or 0), 9.6)
        self.assertTrue(res.get("passed"))
        self.assertTrue(any("轻微" in w for w in (res.get("audit_warnings") or [])))

    def test_scene_collapse_language_blocks_stop(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            img = Path(td) / "s.png"
            img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 200)
            dims = "构图10/光影10/透视7.4/质感10/风格10"
            with mock.patch("skills_kit.judge_auto._physical_image_gate", return_value={"blocked": False, "reasons": [], "score_cap": None}):
                with mock.patch(
                    "skills_kit.judge_auto._inspect_image_physical_traits",
                    return_value={
                        "exists": True, "size_bytes": 5000, "size_kb": 5.0,
                        "width": 1024, "height": 1024, "aspect_ratio": "1:1", "color_entropy": 4.0,
                    },
                ):
                    res = auto_vlm_judge_image(
                        str(img),
                        get_converge_scale_profile("high"),
                        round_num=2,
                        dims=dims,
                        defects="楼体结构崩了，体块散开",
                        next_fix="收紧远景灭点",
                        use_remote_vlm=False,
                        module="scene.Canyon",
                        goal="空镜无人峡谷",
                    )
        self.assertTrue(res.get("anatomy_veto_blocked"))
        self.assertFalse(res.get("passed"))

    def test_scene_missing_dim_on_general_5d_stays_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            img = Path(td) / "s.png"
            img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 200)
            with mock.patch("skills_kit.judge_auto._physical_image_gate", return_value={"blocked": False, "reasons": [], "score_cap": None}):
                with mock.patch(
                    "skills_kit.judge_auto._inspect_image_physical_traits",
                    return_value={
                        "exists": True, "size_bytes": 5000, "size_kb": 5.0,
                        "width": 1024, "height": 1024, "aspect_ratio": "1:1", "color_entropy": 4.0,
                    },
                ):
                    with mock.patch(
                        "skills_kit.judge_auto.audit_score_inflation",
                        return_value={
                            "calibrated_score": 9.7,
                            "dims_parsed": {
                                "composition": 10,
                                "lighting_color": 10,
                                "texture_detail": 10,
                                "spec_style": 10,
                            },
                            "weighted_score": 9.7,
                            "raw_score": 9.7,
                            "warnings": [],
                            "stagnated": False,
                            "rubric_mode": "general_5d",
                        },
                    ):
                        res = auto_vlm_judge_image(
                            str(img),
                            get_converge_scale_profile("medium"),
                            round_num=2,
                            dims="构图10/光影10/质感10/风格10",
                            defects="远处楼体接触阴影偏轻，灭点略散",
                            next_fix="收紧灭点",
                            use_remote_vlm=False,
                            module="scene.Canyon",
                            goal="空镜无人峡谷",
                        )
        self.assertTrue(res.get("anatomy_veto_blocked"))
        self.assertFalse(res.get("passed"))

    def test_skill_additive_scene_skips_missing_anatomy(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            img = Path(td) / "s.png"
            img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 200)
            dims = "风格10/结构10/光影10/合规10/还原10"
            with mock.patch("skills_kit.judge_auto._physical_image_gate", return_value={"blocked": False, "reasons": [], "score_cap": None}):
                with mock.patch(
                    "skills_kit.judge_auto._inspect_image_physical_traits",
                    return_value={
                        "exists": True, "size_bytes": 5000, "size_kb": 5.0,
                        "width": 1024, "height": 1024, "aspect_ratio": "1:1", "color_entropy": 4.0,
                    },
                ):
                    res = auto_vlm_judge_image(
                        str(img),
                        get_converge_scale_profile("medium"),
                        round_num=2,
                        dims=dims,
                        defects="远处楼体接触阴影偏轻，灭点略散",
                        next_fix="收紧灭点",
                        use_remote_vlm=False,
                        module="scene.Canyon",
                        goal="空镜无人峡谷",
                    )
        self.assertEqual(res.get("rubric_mode"), "skill_additive_5d")
        self.assertFalse(res.get("anatomy_veto_blocked"))
        self.assertTrue(res.get("passed"))

    def test_skill_additive_character_stays_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            img = Path(td) / "c.png"
            img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 200)
            dims = "风格10/结构10/光影10/合规10/还原10"
            with mock.patch("skills_kit.judge_auto._physical_image_gate", return_value={"blocked": False, "reasons": [], "score_cap": None}):
                with mock.patch(
                    "skills_kit.judge_auto._inspect_image_physical_traits",
                    return_value={
                        "exists": True, "size_bytes": 5000, "size_kb": 5.0,
                        "width": 1024, "height": 1024, "aspect_ratio": "1:1", "color_entropy": 4.0,
                    },
                ):
                    res = auto_vlm_judge_image(
                        str(img),
                        get_converge_scale_profile("medium"),
                        round_num=2,
                        dims=dims,
                        defects="左手腕融化进剑柄",
                        next_fix="接好左手腕",
                        use_remote_vlm=False,
                        module="character.Hero",
                        goal="少女全身立绘",
                    )
        self.assertTrue(res.get("anatomy_veto_blocked"))
        self.assertFalse(res.get("passed"))

    def test_scene_credit_does_not_lift_a_hard_cap(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            img = Path(td) / "s.png"
            img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 200)
            dims = "构图10/光影10/透视5.9/质感10/风格10"
            with mock.patch("skills_kit.judge_auto._physical_image_gate", return_value={"blocked": False, "reasons": [], "score_cap": None}):
                with mock.patch(
                    "skills_kit.judge_auto._inspect_image_physical_traits",
                    return_value={
                        "exists": True, "size_bytes": 5000, "size_kb": 5.0,
                        "width": 1024, "height": 1024, "aspect_ratio": "1:1", "color_entropy": 4.0,
                    },
                ):
                    res = auto_vlm_judge_image(
                        str(img),
                        get_converge_scale_profile("high"),
                        round_num=2,
                        dims=dims,
                        defects="远处灭点略偏，天空有数字化噪点",
                        next_fix="收紧远景灭点",
                        use_remote_vlm=False,
                        module="scene.Canyon",
                        goal="空镜无人峡谷",
                    )
        self.assertFalse(res.get("passed"))
        self.assertLess(float(res.get("calibrated_score") or 0), 9.6)
        self.assertFalse(any("轻微" in w for w in (res.get("audit_warnings") or [])))

    def test_human_joint_fix_on_a_scene_is_replaced(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            img = Path(td) / "s.png"
            img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 200)
            dims = "构图8/光影8/透视6.2/质感8/风格8"
            with mock.patch("skills_kit.judge_auto._physical_image_gate", return_value={"blocked": False, "reasons": [], "score_cap": None}):
                with mock.patch(
                    "skills_kit.judge_auto._inspect_image_physical_traits",
                    return_value={
                        "exists": True, "size_bytes": 5000, "size_kb": 5.0,
                        "width": 1024, "height": 1024, "aspect_ratio": "1:1", "color_entropy": 4.0,
                    },
                ):
                    res = auto_vlm_judge_image(
                        str(img),
                        get_converge_scale_profile("medium"),
                        round_num=2,
                        dims=dims,
                        defects="灭点略偏",
                        next_fix="修正双肩双肘关节和瞳孔",
                        use_remote_vlm=False,
                        module="scene.Canyon",
                        goal="空镜无人峡谷",
                    )
        self.assertIn("灭点", str(res.get("next_fix") or ""))
        self.assertNotIn("双肘", str(res.get("next_fix") or ""))


class TestToyStubStrip(unittest.TestCase):
    def test_vinyl_stripped_unless_brief_declares_toy(self) -> None:
        plain = get_converge_scale_profile("medium", goal="写实骑士", module="character.Hero")
        out = compose_style_first_prompt("a knight, vinyl toy, chibi proportions, 搪胶桶身", plain)
        self.assertNotIn("vinyl", out.lower())
        self.assertNotIn("chibi", out.lower())
        self.assertNotIn("搪胶", out)
        self.assertNotIn("桶身", out)
        toy = get_converge_scale_profile("medium", goal="Q版玩具骑士", module="character.Hero")
        kept = compose_style_first_prompt("vinyl toy chibi", toy)
        self.assertIn("vinyl", kept.lower())
        self.assertIn("chibi", kept.lower())
        negated = get_converge_scale_profile("medium", goal="不要卡通的写实骑士", module="character.Hero")
        stripped = compose_style_first_prompt("vinyl toy chibi", negated)
        self.assertNotIn("vinyl", stripped.lower())
        self.assertNotIn("chibi", stripped.lower())
        kept_cartoon = get_converge_scale_profile("medium", goal="非常卡通的骑士", module="character.Hero")
        self.assertIn("vinyl", compose_style_first_prompt("vinyl toy", kept_cartoon).lower())
        for goal in ("非卡通写实骑士", "避免卡通", "destroy the knight"):
            prof = get_converge_scale_profile("medium", goal=goal, module="character.Hero")
            out = compose_style_first_prompt("vinyl toy chibi", prof)
            self.assertNotIn("vinyl", out.lower(), goal)
            self.assertNotIn("chibi", out.lower(), goal)


if __name__ == "__main__":
    unittest.main()
