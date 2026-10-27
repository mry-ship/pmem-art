#!/usr/bin/env python3
"""Unit tests for per-case hard parameter validation and VLM three-hands / anti-inflation guardrails."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from skills_kit import (
    CASE_CONFIG_MAP,
    audit_score_inflation,
    auto_vlm_judge_image,
    check_scale_task_text,
    cmd_converge,
    find_affirmative_lock_hits,
    get_converge_scale_profile,
    parse_5d_dims,
    validate_case_generation_params,
)


class TestCaseParameterValidation(unittest.TestCase):
    def test_nonexistent_reference_path_raises(self) -> None:
        with self.assertRaises(FileNotFoundError) as ctx:
            validate_case_generation_params(
                "Case 01",
                aspect_ratio="9:16",
                reference_image_paths=["comparison/style_refs/does_not_exist_999.png"],
                root=ROOT,
            )
        msg = str(ctx.exception)
        self.assertIn("Case 01", msg)
        self.assertIn("does_not_exist_999.png", msg)

    def test_wrong_aspect_ratio_raises(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            validate_case_generation_params(
                "Case 01",
                aspect_ratio="3:4",
                reference_image_paths=["comparison/style_refs/style_ref_01_night_city.png"],
                root=ROOT,
            )
        msg = str(ctx.exception)
        self.assertIn("Case 01", msg)
        self.assertIn("aspect_ratio", msg)
        self.assertIn("9:16", msg)
        self.assertIn("3:4", msg)

        with self.assertRaises(ValueError) as ctx2:
            validate_case_generation_params(
                "Case 02",
                aspect_ratio="3:4",
                reference_image_paths=["comparison/style_refs/style_ref_02_pastel_sketch.png"],
                root=ROOT,
            )
        self.assertIn("Case 02", str(ctx2.exception))
        self.assertIn("4:3", str(ctx2.exception))

    def test_correct_configs_pass_for_all_four_cases(self) -> None:
        cases = [
            ("Case 01", "9:16", "comparison/style_refs/style_ref_01_night_city.png"),
            ("Case 02", "4:3", "comparison/style_refs/style_ref_02_pastel_sketch.png"),
            ("Case 03", "3:4", "comparison/style_refs/style_ref_03_sunlit_portrait.png"),
            ("Case 04", "4:3", "comparison/web_refs/web_ref_01_concept_ishtar.png"),
        ]
        for case_id, ar, ref_path in cases:
            res = validate_case_generation_params(
                case_id,
                aspect_ratio=ar,
                reference_image_paths=[ref_path],
                root=ROOT,
            )
            self.assertTrue(res["valid"])
            self.assertEqual(res["case_id"], case_id)
            self.assertEqual(res["aspect_ratio"], ar)

    def test_converge_generate_aborts_before_running_cmd_on_bad_params(self) -> None:
        marker = Path(tempfile.gettempdir()) / "pmem_should_not_run.txt"
        if marker.exists():
            marker.unlink()
        rc = cmd_converge(
            ROOT,
            {},
            "generate",
            session_id="scale_01_night_city_low",
            round_num=1,
            aspect_ratio="3:4",  # Wrong aspect ratio for Case 01 (expects 9:16)
            ref_image="comparison/style_refs/style_ref_01_night_city.png",
            generate_cmd=f"touch {marker}",
            prompt="test prompt",
        )
        self.assertEqual(rc, 1)
        self.assertFalse(marker.exists(), "generate_cmd must NOT execute when parameter validation fails")

    def test_three_hands_and_extra_hand_trigger_hard_cap(self) -> None:
        prof = get_converge_scale_profile("recompose")
        for phrase in ("three hands", "extra hand", "3 hands", "三只手", "多余刀鞘", "extra sheath"):
            res = audit_score_inflation(
                9.68,
                "构图9.7/光影9.7/透视9.6/质感9.6/风格9.7",
                f"角色手部出现 {phrase} 伪影",
                None,
                prof,
                round_num=3,
            )
            self.assertLessEqual(res["calibrated_score"], 7.90, f"Failed to hard-cap phrase: {phrase}")

    def test_auto_vlm_judge_not_short_circuited_by_cli_defects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_p = Path(tmp)
            # 3:4 pixels + Case 02 ref (expects 4:3) + sidecar three-hands; output filename must NOT alone select case.
            src_3x4 = ROOT / "comparison" / "scale_03_portrait_low_r3.jpg"
            bad_case02_img = tmp_p / "scale_02_sketch_recompose_r3.jpg"
            bad_case02_img.write_bytes(src_3x4.read_bytes())
            sidecar = bad_case02_img.with_suffix(bad_case02_img.suffix + ".vlm.json")
            sidecar.write_text(json.dumps({"defects": "The girl has three hands near her knee"}), encoding="utf-8")

            prof = get_converge_scale_profile("recompose")
            hijack = auto_vlm_judge_image(
                str(bad_case02_img),
                prof,
                round_num=2,
                dims="构图9.7/光影9.6/透视9.6/质感9.6/风格9.7",
                defects="远景空气层次偏弱",
                next_fix="已达标",
                root=ROOT,
                session_id="custom_session",
                ref_image="",
                use_remote_vlm=False,  # assert sidecar merge, not live API rewrite
            )
            self.assertIn("three hands", hijack["defects"])
            self.assertNotIn("画幅比例错误", hijack["defects"])

            judge_res = auto_vlm_judge_image(
                str(bad_case02_img),
                prof,
                round_num=2,
                dims="构图9.7/光影9.6/透视9.6/质感9.6/风格9.7",
                defects="远景空气层次偏弱",
                next_fix="已达标",
                root=ROOT,
                session_id="case02",
                ref_image="comparison/style_refs/style_ref_02_pastel_sketch.png",
                use_remote_vlm=False,
            )
            self.assertLessEqual(judge_res["calibrated_score"], 7.90)
            self.assertFalse(judge_res["passed"])
            self.assertIn("three hands", judge_res["defects"])
            self.assertIn("画幅比例错误", judge_res["defects"])


class TestGateFixes(unittest.TestCase):
    def test_hex_color_survives_yaml_comment_strip(self) -> None:
        import pmem_art as pa
        data = pa.load_yaml(
            "summary: 严禁洋红(#FF00FF)/电光青(#00FFFF)\n"
            "applies: 除受击警示可用 #E11D48 朱砂\n"
        )
        self.assertIn("#FF00FF", data["summary"])
        self.assertIn("#00FFFF", data["summary"])
        self.assertIn("#E11D48", data["applies"])
        self.assertIn("朱砂", data["applies"])

    def test_skill_additive_dims_sum_instead_of_zero(self) -> None:
        info = __import__("skills_kit", fromlist=["parse_5d_dims"]).parse_5d_dims(
            "风格2.2/结构2.0/光影1.7/合规1.4/还原1.3"
        )
        self.assertEqual(info["weighted_score"], 8.6)
        self.assertEqual(info["rubric_mode"], "skill_additive_5d")

    def test_hand_filled_total_cannot_float_above_weighted(self) -> None:
        prof = get_converge_scale_profile("medium")
        res = audit_score_inflation(
            9.64,
            "构图9.5/光影9.5/透视9.5/质感9.5/风格9.5",
            "画面干净",
            None,
            prof,
            round_num=1,
        )
        self.assertAlmostEqual(res["calibrated_score"], res["weighted_score"], places=2)
        self.assertLess(res["calibrated_score"], 9.6)

    def test_negation_and_kept_pose_do_not_hard_cap(self) -> None:
        prof = get_converge_scale_profile("low")
        limb = audit_score_inflation(
            9.7,
            "构图9.7/光影9.7/透视9.7/质感9.7/风格9.7",
            "未出现三只手，并非平光，无解剖错误",
            None,
            prof,
            round_num=2,
        )
        self.assertGreater(limb["calibrated_score"], 9.2)
        self.assertFalse(any("一票否决" in w or "反虚高" in w for w in limb["warnings"]))
        pose = audit_score_inflation(
            9.7,
            "构图9.7/光影9.7/透视9.7/质感9.7/风格9.7",
            "成功保持托腮坐姿，未改动作",
            None,
            prof,
            round_num=1,
        )
        self.assertGreater(pose["calibrated_score"], 9.2)
        self.assertFalse(any("动作红线" in w for w in pose["warnings"]))

    def test_near_9_16_is_not_a_hard_aspect_fail(self) -> None:
        from skills_kit import _aspect_relation
        rel = _aspect_relation(768, 1344, "9:16")
        self.assertFalse(rel["hard_fail"])
        flipped = _aspect_relation(1344, 768, "9:16")
        self.assertTrue(flipped["hard_fail"])

    def test_case_04_ref_is_not_case_01(self) -> None:
        from skills_kit import resolve_case_config
        cfg = resolve_case_config("", "comparison/web_refs/web_ref_01_concept_ishtar.png")
        self.assertIsNotNone(cfg)
        self.assertEqual(cfg["case_id"], "Case 04")
        self.assertIsNone(resolve_case_config("a sketch of a harbor"))

    def test_low_weight_punishes_bad_texture(self) -> None:
        from skills_kit import parse_5d_dims
        low = get_converge_scale_profile("low")
        parsed = parse_5d_dims("构图9.9/光影9.9/透视9.9/质感7.0/风格9.9", low["dim_weights"])
        self.assertLess(parsed["weighted_score"], 9.6)

    def test_jpeg_header_has_resolution(self) -> None:
        import pmem_art as pa
        # Case02 interim style-ref master is 720×580 (4:3 whitelist); old 3:4 cold-start lives as counter-example.
        info = pa.inspect_png(ROOT / "assets/character/pastelgirl/pmem_02_pastel_sketch_girl.jpg")
        self.assertEqual(info["resolution"], "720x580")
        self.assertEqual(info["mode"], "RGB")
        counter = pa.inspect_png(
            ROOT / "assets/character/pastelgirl/pmem_02_pastel_sketch_girl_aspect3x4.jpg"
        )
        self.assertEqual(counter["resolution"], "864x1152")

    def test_high_directive_does_not_import_foreign_props(self) -> None:
        prof = get_converge_scale_profile("high", goal="峡谷天井绿龙", ref_image="canyon")
        self.assertNotIn("耳机", prof["prompt_directive"])
        self.assertNotIn("孔明灯", prof["prompt_directive"])
        # V4-short skeleton: no prop laundry list, no affirmative DNA locks.
        self.assertIn("光影张力", prof["prompt_directive"])
        self.assertNotIn("严格锁死", prof["prompt_directive"])
        self.assertEqual(find_affirmative_lock_hits(prof["prompt_directive"]), [])

    def test_scale_leap_and_cumulative_delta_ladder(self) -> None:
        low = get_converge_scale_profile("low")
        med = get_converge_scale_profile("medium")
        high = get_converge_scale_profile("high")
        rec = get_converge_scale_profile("recompose")
        self.assertLess(low["min_round_leap"], med["min_round_leap"])
        self.assertLess(med["min_round_leap"], high["min_round_leap"])
        # recompose is orthogonal to intensity but must not undercut high leap.
        self.assertGreaterEqual(rec["min_round_leap"], high["min_round_leap"])
        self.assertEqual(med["max_prompt_delta_ratio"], 0.40)
        self.assertEqual(med["max_prompt_delta_vs_first"], 0.60)
        self.assertEqual(high["max_prompt_delta_ratio"], 0.80)
        self.assertEqual(high["max_prompt_delta_vs_first"], 0.90)
        self.assertEqual(rec["max_prompt_delta_ratio"], 0.85)
        self.assertEqual(rec["max_prompt_delta_vs_first"], 0.95)
        self.assertIsNone(low.get("max_prompt_delta_vs_first"))
        self.assertIsNone(low.get("min_prompt_delta_ratio"))
        self.assertEqual(low["max_prompt_delta_ratio"], 0.20)
        self.assertIsNone(med.get("min_prompt_delta_ratio"))
        self.assertIsNone(high.get("min_prompt_delta_ratio"))
        self.assertIsNone(rec.get("min_prompt_delta_ratio"))
        self.assertEqual(rec["max_prompt_delta_ratio"], 0.85)
        # medium: small pose/layout OK; still lock viewpoint + no full recompose
        self.assertTrue(med["allow_action_pose_change"])
        self.assertTrue(med["allow_layout_change"])
        self.assertFalse(med["allow_viewpoint_change"])
        self.assertFalse(med["allow_recompose"])
        self.assertFalse(med["allow_element_count_change"])
        # high: bold leap + narrative; recompose orthogonal axis stays separate
        self.assertTrue(high["allow_recompose"])
        self.assertTrue(high["allow_element_count_change"])
        self.assertTrue(any("no_identity_swap" in str(x) for x in high["forbidden_changes"]))
        # high / recompose must not 1-round stop (anti photocopy).
        self.assertEqual(int(low["min_rounds_before_stop"]), 1)
        self.assertEqual(int(med["min_rounds_before_stop"]), 1)
        self.assertGreaterEqual(int(high["min_rounds_before_stop"]), 2)
        self.assertGreaterEqual(int(rec["min_rounds_before_stop"]), 2)

    def test_continuation_pad_keeps_one_fix_and_accepts_previous_plate(self) -> None:
        from skills_kit.prompt_scale import compose_continuation_prompt
        import shutil

        text = compose_continuation_prompt("把右手五指画清楚", get_converge_scale_profile("high"))
        self.assertIn("目前分数最高", text)
        self.assertIn("只改这一处：把右手五指画清楚", text)
        self.assertIn("没点名的地方保持垫图", text)
        self.assertNotIn("体积光", text)
        rec = compose_continuation_prompt(
            "把梁画清楚",
            get_converge_scale_profile("recompose", recompose_dir="改为街巷仰视"),
        )
        self.assertIn("改为街巷仰视", rec)
        self.assertIn("机位保持指定方向", rec)

        src = ROOT / "docs" / "showcase" / "default_round" / "images" / "night_city_ref.png"
        if not src.is_file():
            self.skipTest("night city plate missing")
        with tempfile.TemporaryDirectory() as tmp:
            plate = Path(tmp) / "round1_plate.png"
            shutil.copyfile(src, plate)
            with self.assertRaises(ValueError):
                validate_case_generation_params(
                    "Case 01",
                    aspect_ratio="9:16",
                    reference_image_paths=[str(plate)],
                    root=ROOT,
                )
            ok = validate_case_generation_params(
                "Case 01",
                aspect_ratio="9:16",
                reference_image_paths=[str(plate)],
                root=ROOT,
                continuation_pad=True,
            )
            self.assertTrue(ok["validation_passed"])
            self.assertTrue(any("目前最高分的成图" in w for w in ok["warnings"]))

    def test_style_jump_empty_pad_does_not_inherit_style_ref(self) -> None:
        from skills_kit.validate_params import validate_converge_params

        res = validate_converge_params(
            session_id="Case 01",
            scale="recompose",
            ref_image="comparison/style_refs/style_ref_01_night_city.png",
            aspect_ratio="9:16",
            reference_image_paths=[],
            allow_empty_pad=True,
            root=ROOT,
        )
        self.assertEqual(res["reference_image_paths"], [])
        self.assertFalse(res["inherited_default_pad_image"])
        self.assertEqual(res["aspect_ratio"], "9:16")

    def test_best_plate_skips_a_later_worse_round(self) -> None:
        from skills_kit.converge import _best_plate

        src = ROOT / "docs" / "showcase" / "default_round" / "images" / "night_city_ref.png"
        if not src.is_file():
            self.skipTest("night city plate missing")
        image, fix, number = _best_plate(
            [
                {"round": 1, "image": str(src), "score": 8.4, "next_fix": "修手指"},
                {"round": 2, "image": str(src), "score": 7.1, "next_fix": "重画全身"},
            ],
            3,
            ROOT,
        )
        self.assertEqual(number, 1)
        self.assertEqual(fix, "修手指")
        self.assertTrue(image.endswith("night_city_ref.png"))

    def test_next_waits_until_the_open_round_is_judged(self) -> None:
        import contextlib
        import io
        from skills_kit.converge import cmd_converge

        src = ROOT / "docs" / "showcase" / "default_round" / "images" / "night_city_ref.png"
        if not src.is_file():
            self.skipTest("night city plate missing")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sess_dir = root / ".memory-art" / "converge"
            sess_dir.mkdir(parents=True)
            (sess_dir / "latest.json").write_text(
                json.dumps({
                    "scale": "low",
                    "rounds": [
                        {"round": 1, "image": str(src), "score": 8.4, "judged": True, "next_fix": "修瓦当"},
                        {"round": 2, "image": str(src), "score": None, "judged": False},
                    ],
                }),
                encoding="utf-8",
            )
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = cmd_converge(root, {}, "next", session_id="latest")
            self.assertEqual(rc, 0)
            self.assertIn("第 2 轮还没审图", buf.getvalue())
            (sess_dir / "latest.json").write_text(
                json.dumps({
                    "scale": "low",
                    "rounds": [
                        {"round": 1, "image": str(src), "score": 8.4, "judged": True, "next_fix": "修瓦当"},
                        {"round": 2, "image": str(src), "score": 7.2, "judged": True, "next_fix": "重画屋顶"},
                    ],
                }),
                encoding="utf-8",
            )
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = cmd_converge(root, {}, "next", session_id="latest")
            text = buf.getvalue()
            self.assertEqual(rc, 0)
            self.assertIn("下一轮第 3 轮", text)
            self.assertIn("第 1 轮", text)
            self.assertIn("修瓦当", text)
            self.assertNotIn("重画屋顶", text)

    def test_high_and_recompose_refuse_round1_stop(self) -> None:
        dims = "构图9.8/光影9.9/透视9.7/质感9.8/风格9.8"
        defects = "远景灯火略糊，冷暖交界可更锐"
        for scale, dir_kw in (("high", ""), ("recompose", "改为运河石拱桥仰视")):
            prof = get_converge_scale_profile(scale, recompose_dir=dir_kw)
            r1 = auto_vlm_judge_image(
                "",
                prof,
                round_num=1,
                dims=dims,
                defects=defects,
                next_fix="继续加强体积光",
                require_image=False,
            )
            self.assertFalse(r1["passed"], scale)
            self.assertTrue(r1.get("early_stop_blocked"), scale)
            self.assertEqual(r1["decision"], "CONTINUE_NEXT_ROUND")
            r2 = auto_vlm_judge_image(
                "",
                prof,
                round_num=2,
                dims=dims,
                defects=defects,
                next_fix="继续加强体积光",
                require_image=False,
            )
            self.assertTrue(r2["passed"], scale)
            self.assertEqual(r2["decision"], "STOP_TARGET_REACHED")

    def test_best_direction_hint_is_additive_not_dna_lock(self) -> None:
        from skills_kit import build_best_direction_hint, SCALE_BEST_DIRECTION_HINTS

        high = get_converge_scale_profile("high")
        self.assertTrue(high["best_direction_hint"].startswith("最优方向："))
        self.assertIn("体积光", high["best_direction_hint"])
        self.assertEqual(find_affirmative_lock_hits(high["best_direction_hint"]), [])
        self.assertEqual(find_affirmative_lock_hits(high["prompt_directive"]), [])
        self.assertIn("光影张力", high["prompt_directive"])
        med = get_converge_scale_profile("medium")
        self.assertIn("光影", med["best_direction_hint"])
        self.assertIn("柔化光影", med["prompt_directive"])
        rec = get_converge_scale_profile("recompose", recompose_dir="改为阳台侧机位")
        self.assertIn("改为阳台侧机位", rec["prompt_directive"])
        self.assertIn("重构机位", rec["prompt_directive"])
        self.assertIn("目标机位", build_best_direction_hint("recompose"))
        self.assertEqual(find_affirmative_lock_hits(rec["prompt_directive"]), [])
        bold = build_best_direction_hint("recompose", recompose_bold=True)
        self.assertEqual(bold, SCALE_BEST_DIRECTION_HINTS["recompose_bold"])
        self.assertIn("剪影", bold)
        self.assertEqual(find_affirmative_lock_hits(bold), [])

    def test_recompose_change_evidence_helper(self) -> None:
        from skills_kit import _recompose_change_evidence

        self.assertFalse(_recompose_change_evidence("核验DNA：高空俯瞰飞檐", "改为运河仰视"))
        self.assertTrue(
            _recompose_change_evidence("已改为运河石拱桥仰视全景机位", "改为运河石拱桥仰视全景")
        )
        self.assertTrue(_recompose_change_evidence("low angle riverside bridge", "运河仰视"))

    def test_high_dull_photocopy_scores_below_drama(self) -> None:
        """Same case: dull flat lighting + locked composition must score below cold/warm drama."""
        high = get_converge_scale_profile("high")
        dull_dims = "构图9.9/光影8.2/透视9.5/质感9.0/风格9.5"
        drama_dims = "构图9.2/光影9.9/透视9.3/质感9.5/风格9.6"
        dull_w = parse_5d_dims(dull_dims, high["dim_weights"])["weighted_score"]
        drama_w = parse_5d_dims(drama_dims, high["dim_weights"])["weighted_score"]
        self.assertLess(dull_w, drama_w)
        dull_audit = audit_score_inflation(
            dull_w, dull_dims, "冷暖分离不足，闷贴原图", None, high, round_num=2
        )
        drama_audit = audit_score_inflation(
            drama_w, drama_dims, "体积光可再锐一点", None, high, round_num=2
        )
        self.assertLess(dull_audit["calibrated_score"], drama_audit["calibrated_score"])
        self.assertLessEqual(dull_audit["calibrated_score"], 8.95)

    def test_compose_strips_affirmative_locks(self) -> None:
        from skills_kit import compose_style_first_prompt, strip_affirmative_locks_from_prompt

        dirty = (
            "严格保留DNA：高空俯瞰 | 参考垫图一致性高 | 构图：锁死9:16飞檐 | "
            "升级体积光与冷暖碰撞"
        )
        cleaned = strip_affirmative_locks_from_prompt(dirty, scale="high")
        self.assertNotIn("严格保留DNA", cleaned)
        self.assertNotIn("垫图一致性高", cleaned)
        self.assertNotIn("构图：锁死", cleaned)
        self.assertIn("体积光", cleaned)
        high = get_converge_scale_profile("high")
        composed = compose_style_first_prompt(dirty, high)
        self.assertEqual(find_affirmative_lock_hits(composed), [])
        self.assertIn("光影张力", composed)

    def test_preflight_affirmative_lock_and_min_rounds(self) -> None:
        bad = check_scale_task_text(
            scale="high",
            goal="严格锁死高空俯瞰，垫图一致性高",
        )
        self.assertFalse(bad["ok"])
        self.assertTrue(any("肯定锁" in x for x in bad["issues"]))
        good = check_scale_task_text(
            scale="high",
            goal="升级体积光与冷暖碰撞，保媒介身份",
        )
        self.assertTrue(good["ok"])
        self.assertGreaterEqual(good["min_rounds_before_stop"], 2)
        # Negation must not count as affirmative lock.
        self.assertEqual(find_affirmative_lock_hits("勿写锁死构图，禁止垫图一致性高"), [])
        rec_bad = check_scale_task_text(
            scale="recompose",
            goal="高空俯瞰左下飞檐微调",
            recompose_dir="高空俯瞰左下飞檐",
        )
        self.assertFalse(rec_bad["ok"])
        rec_ok = check_scale_task_text(
            scale="recompose",
            goal="改为阳台花格过肩仰视",
            recompose_dir="改为阳台花格过肩仰视",
        )
        self.assertTrue(rec_ok["ok"], rec_ok["issues"])

    def test_low_case_redlines_replace_generic_not_stack(self) -> None:
        prof = get_converge_scale_profile(
            "low", goal="仙侠不夜城男侠", ref_image="comparison/style_refs/style_ref_01_night_city.png"
        )
        keys = [str(x).split("(", 1)[0].strip() for x in prof["forbidden_changes"]]
        # Case-specific clauses present; generic viewpoint/pose/layout/element/identity dropped.
        self.assertIn("low_angle_back_pose", keys)
        self.assertIn("pavilion_and_lantern_layout", keys)
        self.assertIn("male_swordsman_identity", keys)
        self.assertNotIn("viewpoint_angle", keys)
        self.assertNotIn("character_action_and_pose", keys)
        self.assertNotIn("element_count", keys)
        self.assertNotIn("scene_layout", keys)
        self.assertIn("style_medium", keys)
        self.assertNotIn("identity_lock", keys)  # replaced by male_swordsman_identity
        self.assertLessEqual(len(prof["forbidden_changes"]), 5)

    def test_low_pastel_case_redlines_replace_style_generic(self) -> None:
        prof = get_converge_scale_profile(
            "low",
            goal="粉彩速写少女",
            ref_image="comparison/style_refs/style_ref_02_pastel_sketch.png",
        )
        keys = [str(x).split("(", 1)[0].strip() for x in prof["forbidden_changes"]]
        self.assertIn("viewpoint_and_sitting_pose", keys)
        self.assertIn("pastel_sketch_medium_and_whitespace", keys)
        self.assertIn("element_count", keys)
        self.assertNotIn("viewpoint_angle", keys)
        self.assertNotIn("character_action_and_pose", keys)
        self.assertNotIn("style_medium", keys)  # replaced by pastel-specific medium lock
        self.assertIn("identity_lock", keys)

    def test_high_cumulative_delta_exceeds_cap(self) -> None:
        """Judge gate reads max_prompt_delta_vs_first; total rewrite vs first must exceed the cap."""
        from skills_kit import _prompt_change_ratio

        for scale, dir_kw in (("high", ""), ("recompose", "改为仰视运河")):
            prof = get_converge_scale_profile(scale, recompose_dir=dir_kw)
            directive = prof["prompt_directive"]
            first = f"{directive} | lock identity night city pavilion lantern back pose"
            drifted = (
                f"{directive} | "
                "totally rewritten cinematic crane shot volumetric god rays emerald dragon "
                "waterfall bridge orchestra of foreign narrative props and alternate wardrobe "
                "palette shift neon alley cyberpunk rain reflections unrelated subjects"
            )
            cumulative = _prompt_change_ratio(first, drifted, directive)
            self.assertGreater(
                cumulative,
                float(prof["max_prompt_delta_vs_first"]),
                f"{scale}: cumulative={cumulative:.2f} vs cap={prof['max_prompt_delta_vs_first']}",
            )

    def test_redlines_follow_the_subject(self) -> None:
        from skills_kit import compose_style_first_prompt
        prof = get_converge_scale_profile("low", goal="仙侠不夜城男侠", ref_image="night_city")
        text = compose_style_first_prompt("黑衣男侠立于飞檐", prof)
        self.assertTrue(text.startswith(prof["prompt_directive"]))
        self.assertLess(text.find("黑衣男侠"), text.find("约束："))
        self.assertIn("俯瞰", text)
        self.assertNotIn("仰视", text)
        self.assertIn("男性持剑侠客", text)
        medium = get_converge_scale_profile("medium", recompose_dir="改为仰视全景")
        self.assertEqual(medium["scale"], "medium")
        self.assertNotIn("改为仰视全景", medium["prompt_directive"])

    def test_high_style_weight_blocks_a_drifted_medium(self) -> None:
        from skills_kit import parse_5d_dims
        high = get_converge_scale_profile("high")
        parsed = parse_5d_dims("构图9.9/光影9.9/透视9.9/质感9.9/风格7.0", high["dim_weights"])
        self.assertLess(parsed["weighted_score"], 9.6)

    def test_compliance_language_does_not_hard_cap(self) -> None:
        from feedback import detect_kind
        low = get_converge_scale_profile("low", goal="粉彩速写少女", module="character.PastelGirl")
        dims = "构图9.8/光影9.7/透视9.7/质感9.7/风格9.7"
        safe_lines = (
            "锁视角与姿态，仅微调局部笔触",
            "本轮已彻底解决多手与六指问题，无解剖错误",
            "继续锁死坐姿，严禁动作改变或姿态改变",
            "严禁平光",
        )
        for line in safe_lines:
            res = audit_score_inflation(9.72, dims, line, None, low, round_num=1)
            self.assertGreater(res["calibrated_score"], 9.2, line)
        hit = audit_score_inflation(9.72, dims, "膝盖旁多手", None, low, round_num=1)
        self.assertLessEqual(hit["calibrated_score"], 7.90)
        for phrase in ("这张特别多手", "能识别多手", "少不了多手", "这轮改了机位"):
            flagged = audit_score_inflation(9.72, dims, phrase, None, low, round_num=1)
            self.assertLess(flagged["calibrated_score"], 9.2, phrase)
        judge = auto_vlm_judge_image(
            "",
            low,
            round_num=1,
            dims=dims,
            defects="画面干净",
            next_fix="修正画幅比例错误，严禁动作改变",
        )
        self.assertGreater(judge["calibrated_score"], 9.2)
        self.assertEqual(detect_kind("高光太过了，严重过曝，打回重画！"), "style_redline")
        self.assertEqual(detect_kind("这版过曝，不通过"), "style_redline")
        self.assertEqual(detect_kind("不要保留这块高光"), "visual_correction")
        self.assertEqual(detect_kind("unapproved"), "visual_correction")
        self.assertEqual(detect_kind("通过，这版留着"), "recipe")
        self.assertEqual(detect_kind("这版留着，打回"), "style_redline")
        self.assertEqual(detect_kind("不要再保留"), "style_redline")
        self.assertEqual(detect_kind("不可以通过"), "visual_correction")
        self.assertEqual(detect_kind("质检无法通过，打回"), "style_redline")
        self.assertEqual(detect_kind("这版可以用"), "recipe")
        self.assertEqual(detect_kind("特别保留"), "recipe")
        self.assertEqual(detect_kind("识别通过"), "recipe")
        bang = audit_score_inflation(9.72, dims, "已彻底解决多手！六指", None, low, round_num=1)
        self.assertGreater(bang["calibrated_score"], 9.2)
        semicolon = audit_score_inflation(9.72, dims, "已彻底解决多手;六指", None, low, round_num=1)
        self.assertGreater(semicolon["calibrated_score"], 9.2)
        denied = audit_score_inflation(9.72, dims, "画面没有多手", None, low, round_num=1)
        self.assertGreater(denied["calibrated_score"], 9.2)
        pastel = get_converge_scale_profile("medium", goal="粉彩速写少女", module="character.PastelGirl")
        self.assertNotIn("次表面散射", pastel["prompt_directive"])
        for goal in ("水彩少女", "水墨山水", "肖像水彩"):
            flat = get_converge_scale_profile("medium", goal=goal)
            self.assertNotIn("次表面散射", flat["prompt_directive"], goal)
        painterly = get_converge_scale_profile("medium", goal="峡谷天井绿龙", ref_image="canyon")
        self.assertIn("次表面散射", painterly["prompt_directive"])
        film = get_converge_scale_profile("medium", goal="胶片肖像", ref_analysis="背景略有水彩晕染")
        self.assertIn("次表面散射", film["prompt_directive"])
        canyon = get_converge_scale_profile("medium", goal="峡谷天井绿龙", ref_image="canyon", ref_analysis="远景水墨层次")
        self.assertIn("次表面散射", canyon["prompt_directive"])

    def test_scope_phrases_cap_and_negation_does_not(self) -> None:
        low = get_converge_scale_profile("low")
        moved = audit_score_inflation(
            9.7, "构图9.7/光影9.7/透视9.7/质感9.7/风格9.7", "这轮改了机位", None, low, round_num=2,
        )
        self.assertLessEqual(moved["calibrated_score"], 8.50)
        kept = audit_score_inflation(
            9.7, "构图9.7/光影9.7/透视9.7/质感9.7/风格9.7", "没有改机位，保持原布局", None, low, round_num=2,
        )
        self.assertGreater(kept["calibrated_score"], 9.2)
        for phrase in ("不改机位", "不要改机位", "没改机位", "别改机位", "不换脸", "？不换脸", "「不改机位」", "没有发生换脸"):
            safe = audit_score_inflation(
                9.7, "构图9.7/光影9.7/透视9.7/质感9.7/风格9.7", phrase, None, low, round_num=2,
            )
            self.assertGreater(safe["calibrated_score"], 9.2, phrase)
        for phrase in ("这轮换脸了", "不过改了机位", "特别改了机位", "没有问题，改了机位"):
            changed = audit_score_inflation(
                9.7, "构图9.7/光影9.7/透视9.7/质感9.7/风格9.7", phrase, None, low, round_num=2,
            )
            self.assertLessEqual(changed["calibrated_score"], 8.50, phrase)

    def test_recompose_start_requires_a_direction(self) -> None:
        from skills_kit import cmd_converge
        td = Path(tempfile.mkdtemp())
        rc = cmd_converge(td, {}, "start", session_id="need_dir", scale="recompose", goal="换机位")
        self.assertEqual(rc, 1)
        self.assertFalse((td / ".memory-art" / "converge" / "need_dir.json").exists())

    def test_dim_labels_and_clean_bill_do_not_become_lessons(self) -> None:
        from improve import craft_lessons_from_round
        for text in ("构图", "光影", "构图/光影/透视/质感/风格", "构图8.6/光影8.2/透视7.8/质感8.0/风格8.4", "构图:9.7,光影:9.7,透视:9.6,材质:9.8,风格:9.7", "无明显硬伤"):
            lessons = craft_lessons_from_round(defects=text, strengths="", next_fix="")
            self.assertEqual(lessons, [], text)
        real = craft_lessons_from_round(defects="构图拥挤，主体被裁切", strengths="", next_fix="")
        self.assertTrue(any(x["category"] == "composition" for x in real))
        contrasted = craft_lessons_from_round(defects="无明显硬伤，但构图拥挤", strengths="", next_fix="")
        self.assertTrue(any(x["category"] == "composition" for x in contrasted))

    def test_webp_header_has_resolution(self) -> None:
        from skills_kit import _inspect_image_physical_traits
        raw = bytearray(30)
        raw[0:4] = b"RIFF"
        raw[8:12] = b"WEBP"
        raw[12:16] = b"VP8X"
        raw[24:27] = (767).to_bytes(3, "little")
        raw[27:30] = (1343).to_bytes(3, "little")
        path = Path(tempfile.gettempdir()) / "pmem_gate_probe.webp"
        path.write_bytes(bytes(raw))
        info = _inspect_image_physical_traits(path)
        self.assertEqual((info["width"], info["height"]), (768, 1344))

    def test_legacy_four_key_dims_parse(self) -> None:
        from skills_kit import parse_5d_dims
        info = parse_5d_dims("style=7.0,comp=6.5,spec=7.0,detail=6.7")
        self.assertIsNotNone(info["weighted_score"])

    def test_unpassed_finish_recipe_does_not_claim_success(self) -> None:
        from skills_kit import converge_finish
        td = Path(tempfile.mkdtemp())
        mem = td / ".memory-art" / "converge"
        mem.mkdir(parents=True)
        sess = {
            "session_id": "below",
            "goal": "测试未达标",
            "module": "brand.GlobalStyle",
            "scale": "medium",
            "accept_threshold": 9.6,
            "threshold": 9.6,
            "max_rounds": 8,
            "rounds": [{
                "round": 1,
                "score": 8.0,
                "image": "",
                "judged": True,
                "passed": False,
                "strengths": "色调稳",
                "defects": "手部多指",
                "next_fix": "分开五指",
                "prompt": "test",
            }],
        }
        (mem / "below.json").write_text(json.dumps(sess, ensure_ascii=False), encoding="utf-8")
        converge_finish(
            td,
            {"config": {}, "entries": [], "modules": {}},
            session_id="below",
            apply_memory=True,
            silent=True,
        )
        recipes = list((td / ".memory-art" / "entries").rglob("*.md"))
        self.assertTrue(recipes)
        recipe_text = "\n".join(
            p.read_text(encoding="utf-8") for p in recipes if "kind: recipe" in p.read_text(encoding="utf-8")
        )
        self.assertIn("未达阈值", recipe_text)
        self.assertNotIn("轮达标", recipe_text)

    def test_missing_image_cannot_pass_or_register(self) -> None:
        from skills_kit import compose_style_first_prompt, converge_finish
        td = Path(tempfile.mkdtemp())
        cmd_converge(td, {}, "start", session_id="ghost", scale="medium", goal="幽灵图")
        prof = get_converge_scale_profile("medium", goal="幽灵图")
        prompt = compose_style_first_prompt("test", prof)
        rc_gen = cmd_converge(
            td, {}, "generate", session_id="ghost", round_num=1, prompt=prompt, image="",
        )
        self.assertEqual(rc_gen, 1, "generate must refuse empty image path")
        # Register a fake path that does not exist on disk
        rc_gen2 = cmd_converge(
            td, {}, "generate", session_id="ghost", round_num=1,
            prompt=prompt, image="does_not_exist_zzz.jpg",
        )
        self.assertEqual(rc_gen2, 1)
        judge = auto_vlm_judge_image(
            "does_not_exist_zzz.jpg",
            prof,
            round_num=1,
            dims="构图9.8/光影9.8/透视9.8/质感9.8/风格9.8",
            defects="完美",
            root=td,
        )
        self.assertFalse(judge["passed"])
        self.assertTrue(judge["image_gate_blocked"])
        self.assertLess(judge["calibrated_score"], 9.6)

    def test_flat_color_image_cannot_pass(self) -> None:
        from PIL import Image
        flat = Path(tempfile.gettempdir()) / "pmem_flat_gate.png"
        Image.new("RGB", (512, 512), (180, 180, 180)).save(flat)
        prof = get_converge_scale_profile("medium")
        judge = auto_vlm_judge_image(
            str(flat),
            prof,
            round_num=1,
            dims="构图9.8/光影9.8/透视9.8/质感9.8/风格9.8",
            defects="完美",
        )
        self.assertFalse(judge["passed"])
        self.assertTrue(judge["image_gate_blocked"])

    def test_non_digital_praise_is_not_capped(self) -> None:
        prof = get_converge_scale_profile("medium")
        res = audit_score_inflation(
            9.7,
            "构图9.7/光影9.7/透视9.7/质感9.7/风格9.7",
            "非数字化手绘感很好，纸纹清晰",
            None,
            prof,
            round_num=1,
        )
        self.assertGreater(res["calibrated_score"], 9.2)
        hit = audit_score_inflation(
            9.7,
            "构图9.7/光影9.7/透视9.7/质感9.7/风格9.7",
            "表面偏数字化噪点",
            None,
            prof,
            round_num=1,
        )
        self.assertLessEqual(hit["calibrated_score"], 8.90)

    def test_skill_ten_point_scale_normalizes(self) -> None:
        from skills_kit import parse_5d_dims
        info = parse_5d_dims("风格9.5/结构9.0/光影9.0/合规9.0/还原9.0")
        self.assertEqual(info["rubric_mode"], "skill_additive_5d")
        self.assertIsNotNone(info["weighted_score"])
        self.assertGreater(info["weighted_score"], 8.5)

    def test_concept_legacy_emphasis_dims_do_not_zero(self) -> None:
        """旧 concept 侧重标签不得再把 converge judge 打成 0 分。"""
        from skills_kit import parse_5d_dims, audit_score_inflation, get_converge_scale_profile

        legacy = "风格色板9.5/构图叙事与透视9.2/光影材质9.0/红线合规8.8/氛围意图还原9.1"
        info = parse_5d_dims(legacy)
        self.assertIsNotNone(info["weighted_score"], info)
        self.assertGreater(info["weighted_score"], 8.5)
        abs5 = parse_5d_dims("构图9.2/光影9.0/透视8.8/质感8.9/风格9.1")
        self.assertEqual(abs5["rubric_mode"], "general_5d")
        self.assertIsNotNone(abs5["weighted_score"])
        prof = get_converge_scale_profile("medium")
        audited = audit_score_inflation(9.5, legacy, "远景层次偏弱，需加强空气透视", None, prof, round_num=1)
        self.assertGreater(audited["calibrated_score"], 0.0)
        self.assertNotIn("五维字符串无法解析", " ".join(audited.get("warnings") or []))

    def test_loose_case_aliases_no_longer_hijack_sessions(self) -> None:
        from skills_kit import resolve_case_config
        self.assertIsNone(resolve_case_config("my_sketch_art"))
        self.assertIsNone(resolve_case_config("portrait_study"))
        self.assertIsNone(resolve_case_config("canyon_walk"))
        self.assertIsNone(resolve_case_config("pastel_sketch"))
        self.assertIsNone(resolve_case_config("night_city_walk"))
        self.assertIsNone(resolve_case_config("web_ref_01"))
        self.assertIsNone(resolve_case_config("my_pastel_sketch_girl"))
        self.assertIsNone(resolve_case_config("pmem_03_custom"))
        self.assertEqual(resolve_case_config("scale_01_night_city_low")["case_id"], "Case 01")
        self.assertEqual(resolve_case_config("case02")["case_id"], "Case 02")
        self.assertEqual(
            resolve_case_config("", "comparison/web_refs/web_ref_01_concept_ishtar.png")["case_id"],
            "Case 04",
        )

    def test_finish_requires_judged_round(self) -> None:
        from skills_kit import converge_finish, _inspect_image_physical_traits
        import shutil
        td = Path(tempfile.mkdtemp())
        mem = td / ".memory-art" / "converge"
        mem.mkdir(parents=True)
        real = ROOT / "comparison" / "scale_01_night_city_high.jpg"
        out = td / "unjudged.jpg"
        shutil.copy2(real, out)
        traits = _inspect_image_physical_traits(out)
        sess = {
            "session_id": "skip_judge",
            "goal": "跳过审图",
            "module": "brand.GlobalStyle",
            "scale": "medium",
            "accept_threshold": 9.6,
            "threshold": 9.6,
            "max_rounds": 8,
            "rounds": [{
                "round": 1,
                "score": 9.9,
                "image": str(out),
                "judged": False,
                "passed": False,
                "gate_blocked": False,
                "image_gate_blocked": False,
                "image_verification": traits,
                "strengths": "手填分",
                "defects": "",
                "next_fix": "",
                "prompt": "x",
            }],
        }
        (mem / "skip_judge.json").write_text(json.dumps(sess, ensure_ascii=False), encoding="utf-8")
        converge_finish(
            td,
            {"config": {}, "entries": [], "modules": {}},
            session_id="skip_judge",
            apply_memory=True,
            silent=True,
        )
        recipes = list((td / ".memory-art" / "entries").rglob("*.md"))
        recipe_text = "\n".join(
            p.read_text(encoding="utf-8") for p in recipes if "kind: recipe" in p.read_text(encoding="utf-8")
        )
        self.assertIn("未达阈值", recipe_text)

    def test_finish_rejects_stale_image_verification_without_file(self) -> None:
        from skills_kit import converge_finish, _inspect_image_physical_traits
        td = Path(tempfile.mkdtemp())
        mem = td / ".memory-art" / "converge"
        mem.mkdir(parents=True)
        real = ROOT / "comparison" / "scale_01_night_city_high.jpg"
        traits = _inspect_image_physical_traits(real)
        self.assertTrue(traits.get("exists"))
        ghost = td / "ghost_missing.jpg"
        sess = {
            "session_id": "stale_ver",
            "goal": "伪造 verification",
            "module": "brand.GlobalStyle",
            "scale": "medium",
            "accept_threshold": 9.6,
            "threshold": 9.6,
            "max_rounds": 8,
            "rounds": [{
                "round": 1,
                "score": 9.85,
                "image": str(ghost),
                "stage": "judged",
                "judged": True,
                "passed": True,
                "gate_blocked": False,
                "image_gate_blocked": False,
                "image_verification": traits,
                "dims": "构图9.8/光影9.8/透视9.8/质感9.8/风格9.8",
                "step_trace": ["step1_start", "step2_generate", "step3_judge"],
                "strengths": "伪造",
                "defects": "",
                "next_fix": "",
                "prompt": "x",
            }],
        }
        (mem / "stale_ver.json").write_text(json.dumps(sess, ensure_ascii=False), encoding="utf-8")
        converge_finish(
            td,
            {"config": {}, "entries": [], "modules": {}},
            session_id="stale_ver",
            apply_memory=True,
            silent=True,
        )
        recipes = list((td / ".memory-art" / "entries").rglob("*.md"))
        recipe_text = "\n".join(
            p.read_text(encoding="utf-8") for p in recipes if "kind: recipe" in p.read_text(encoding="utf-8")
        )
        self.assertIn("未达阈值", recipe_text)
        self.assertNotIn("达标定稿", recipe_text)

    def test_finish_rejects_forged_judged_without_step3(self) -> None:
        from skills_kit import converge_finish, _inspect_image_physical_traits
        import shutil
        td = Path(tempfile.mkdtemp())
        mem = td / ".memory-art" / "converge"
        mem.mkdir(parents=True)
        real = ROOT / "comparison" / "scale_01_night_city_high.jpg"
        out = td / "forged.jpg"
        shutil.copy2(real, out)
        traits = _inspect_image_physical_traits(out)
        sess = {
            "session_id": "forged_judge",
            "goal": "伪造 judged",
            "module": "brand.GlobalStyle",
            "scale": "medium",
            "accept_threshold": 9.6,
            "threshold": 9.6,
            "max_rounds": 8,
            "rounds": [{
                "round": 1,
                "score": 9.9,
                "image": str(out),
                "stage": "generated_pending_judge",
                "judged": True,
                "passed": True,
                "gate_blocked": False,
                "image_gate_blocked": False,
                "image_verification": traits,
                "dims": "",
                "step_trace": ["step1_start", "step2_generate"],
                "strengths": "伪造",
                "defects": "",
                "next_fix": "",
                "prompt": "x",
            }],
        }
        (mem / "forged_judge.json").write_text(json.dumps(sess, ensure_ascii=False), encoding="utf-8")
        converge_finish(
            td,
            {"config": {}, "entries": [], "modules": {}},
            session_id="forged_judge",
            apply_memory=True,
            silent=True,
        )
        recipes = list((td / ".memory-art" / "entries").rglob("*.md"))
        recipe_text = "\n".join(
            p.read_text(encoding="utf-8") for p in recipes if "kind: recipe" in p.read_text(encoding="utf-8")
        )
        self.assertIn("未达阈值", recipe_text)
        self.assertNotIn("达标定稿", recipe_text)

    def test_medium_constraint_locks_viewpoint_not_pose(self) -> None:
        from skills_kit import _constraint_tail
        med = get_converge_scale_profile("medium")
        self.assertTrue(med["allow_action_pose_change"])
        self.assertTrue(med["allow_layout_change"])
        self.assertFalse(med["allow_viewpoint_change"])
        self.assertFalse(med["allow_recompose"])
        keys = [str(x).split("(", 1)[0].strip() for x in med["forbidden_changes"]]
        self.assertIn("viewpoint_angle", keys)
        self.assertNotIn("character_action_and_pose", keys)
        self.assertNotIn("scene_layout", keys)
        self.assertIn("机位", _constraint_tail(med))
        self.assertNotIn("不改动作与姿态", _constraint_tail(med))

    def test_style_infer_prefers_ref_over_weak_goal_sketch(self) -> None:
        from skills_kit import _infer_case_style_and_subject
        head, _, redlines = _infer_case_style_and_subject(
            goal="画一张 portrait sketch 夜景",
            ref_image="comparison/style_refs/style_ref_01_night_city.png",
        )
        self.assertIn("仙侠", head)
        self.assertTrue(any("俯瞰" in x or "飞檐" in x for x in redlines))

    def test_soft_defects_cannot_stop_target(self) -> None:
        from skills_kit import defects_are_substantive, _round_counts_as_passed
        prof = get_converge_scale_profile("medium")
        img = ROOT / "comparison" / "scale_01_night_city_high.jpg"
        for soft in ("", "无", "无明显硬伤", "细节达标", "画面干净", "基本无明显硬伤"):
            self.assertFalse(defects_are_substantive(soft), soft)
            res = auto_vlm_judge_image(
                str(img),
                prof,
                round_num=1,
                dims="构图9.7/光影9.7/透视9.6/质感9.6/风格9.5",
                defects=soft,
                root=ROOT,
                use_remote_vlm=False,
            )
            self.assertFalse(res["passed"], soft)
            self.assertLess(res["calibrated_score"], 9.6)
        # finish path must reject rubber-stamp defects even if score/trace look passed
        forged = {
            "round": 1,
            "score": 9.7,
            "image": str(img),
            "stage": "judged",
            "judged": True,
            "passed": True,
            "gate_blocked": False,
            "image_gate_blocked": False,
            "dims": "构图9.7/光影9.7/透视9.6/质感9.6/风格9.5",
            "step_trace": ["step1_start", "step2_generate", "step3_judge"],
            "defects": "无明显硬伤",
        }
        self.assertFalse(_round_counts_as_passed(forged, 9.6, root=ROOT))
        forged["defects"] = "远景空气层次偏弱"
        self.assertTrue(_round_counts_as_passed(forged, 9.6, root=ROOT))

    def test_finish_rejects_judge_only_without_generate(self) -> None:
        from skills_kit import converge_finish, _inspect_image_physical_traits, _round_counts_as_passed
        import shutil
        td = Path(tempfile.mkdtemp())
        mem = td / ".memory-art" / "converge"
        mem.mkdir(parents=True)
        real = ROOT / "comparison" / "scale_01_night_city_high.jpg"
        out = td / "only_judge.jpg"
        shutil.copy2(real, out)
        traits = _inspect_image_physical_traits(out)
        round_row = {
            "round": 1,
            "score": 9.7,
            "image": str(out),
            "stage": "judged",
            "judged": True,
            "passed": True,
            "gate_blocked": False,
            "image_gate_blocked": False,
            "image_verification": traits,
            "dims": "构图9.7/光影9.7/透视9.6/质感9.6/风格9.5",
            "step_trace": ["step3_judge"],
            "strengths": "ok",
            "defects": "远景略虚",
            "next_fix": "",
            "prompt": "x",
        }
        self.assertFalse(_round_counts_as_passed(round_row, 9.6, root=td))
        sess = {
            "session_id": "judge_only",
            "goal": "跳过generate",
            "module": "brand.GlobalStyle",
            "scale": "medium",
            "accept_threshold": 9.6,
            "threshold": 9.6,
            "max_rounds": 8,
            "rounds": [round_row],
        }
        (mem / "judge_only.json").write_text(json.dumps(sess, ensure_ascii=False), encoding="utf-8")
        converge_finish(
            td,
            {"config": {}, "entries": [], "modules": {}},
            session_id="judge_only",
            apply_memory=True,
            silent=True,
        )
        recipes = list((td / ".memory-art" / "entries").rglob("*.md"))
        recipe_text = "\n".join(
            p.read_text(encoding="utf-8") for p in recipes if "kind: recipe" in p.read_text(encoding="utf-8")
        )
        self.assertIn("未达阈值", recipe_text)
        self.assertNotIn("达标定稿", recipe_text)

    def test_high_score_without_image_finish_is_not_达标(self) -> None:
        from skills_kit import converge_finish
        td = Path(tempfile.mkdtemp())
        mem = td / ".memory-art" / "converge"
        mem.mkdir(parents=True)
        sess = {
            "session_id": "nofile_win",
            "goal": "假达标",
            "module": "brand.GlobalStyle",
            "scale": "medium",
            "accept_threshold": 9.6,
            "threshold": 9.6,
            "max_rounds": 8,
            "rounds": [{
                "round": 1,
                "score": 9.8,
                "image": "",
                "stage": "judged",
                "judged": True,
                "passed": True,
                "gate_blocked": False,
                "image_gate_blocked": True,
                "image_verification": {"exists": False},
                "dims": "构图9.8/光影9.8/透视9.8/质感9.8/风格9.8",
                "step_trace": ["step1_start", "step2_generate", "step3_judge"],
                "strengths": "虚高",
                "defects": "无图",
                "next_fix": "",
                "prompt": "x",
            }],
        }
        (mem / "nofile_win.json").write_text(json.dumps(sess, ensure_ascii=False), encoding="utf-8")
        converge_finish(
            td,
            {"config": {}, "entries": [], "modules": {}},
            session_id="nofile_win",
            apply_memory=True,
            silent=True,
        )
        recipes = list((td / ".memory-art" / "entries").rglob("*.md"))
        recipe_text = "\n".join(
            p.read_text(encoding="utf-8") for p in recipes if "kind: recipe" in p.read_text(encoding="utf-8")
        )
        self.assertIn("未达阈值", recipe_text)

    def test_judge_rejects_without_prior_generate(self) -> None:
        td = Path(tempfile.mkdtemp())
        mem = td / ".memory-art" / "converge"
        mem.mkdir(parents=True)
        sess = {
            "session_id": "noj",
            "goal": "must generate first",
            "module": "brand.WorldStyle",
            "scale": "medium",
            "accept_threshold": 9.6,
            "threshold": 9.6,
            "max_rounds": 8,
            "rounds": [],
            "status": "running",
        }
        (mem / "noj.json").write_text(json.dumps(sess, ensure_ascii=False), encoding="utf-8")
        rc = cmd_converge(
            td,
            {"config": {}, "entries": [], "modules": {}},
            action="judge",
            session_id="noj",
            round_num=1,
            image=str(td / "missing.jpg"),
            dims="构图9.6/光影9.6/透视9.6/质感9.6/风格9.6",
            defects="无",
            next_fix="",
            silent=True,
        )
        self.assertEqual(rc, 1)
        after = json.loads((mem / "noj.json").read_text(encoding="utf-8"))
        self.assertEqual(after.get("rounds"), [])


if __name__ == "__main__":
    unittest.main()
