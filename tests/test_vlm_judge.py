#!/usr/bin/env python3
"""Tests for optional independent vision judge (vlm_judge)."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from vlm_judge import (
    build_judge_system_prompt,
    is_vlm_judge_configured,
    load_vlm_judge_config,
    maybe_run_independent_vlm_judge,
    observations_from_vlm_payload,
    resolve_api_key,
    vlm_judge_status,
)


class TestVlmJudgeConfig(unittest.TestCase):
    def test_no_key_means_inactive(self) -> None:
        td = Path(tempfile.mkdtemp())
        (td / ".memory-art").mkdir()
        cfg = load_vlm_judge_config(td, {"config": {"vlm_judge": {"enabled": "auto", "api_key": ""}}})
        with mock.patch.dict(os.environ, {}, clear=True):
            # Clear only our key candidates while keeping PATH etc. — patch specific keys
            env = {k: v for k, v in os.environ.items() if k not in (
                "PMEM_VLM_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"
            )}
            with mock.patch.dict(os.environ, env, clear=True):
                self.assertFalse(is_vlm_judge_configured(cfg))
                st = vlm_judge_status(td, {"config": {"vlm_judge": cfg}})
                self.assertFalse(st["active"])
                self.assertEqual(st["source"], "agent_self_judge")

    def test_env_key_activates_auto(self) -> None:
        cfg = load_vlm_judge_config(None, {"config": {"vlm_judge": {"enabled": "auto", "api_key": ""}}})
        realish = "sk-proj-unit-test-key-abcdef"
        with mock.patch.dict(os.environ, {"PMEM_VLM_API_KEY": realish}, clear=False):
            self.assertTrue(is_vlm_judge_configured(cfg))
            self.assertEqual(resolve_api_key(cfg), realish)

    def test_never_ignores_key(self) -> None:
        cfg = load_vlm_judge_config(
            None,
            {"config": {"vlm_judge": {"enabled": "never", "api_key": "sk-proj-unit-test-key-abcdef"}}},
        )
        self.assertFalse(is_vlm_judge_configured(cfg))

    def test_placeholder_key_rejected(self) -> None:
        cfg = load_vlm_judge_config(
            None,
            {"config": {"vlm_judge": {"enabled": "auto", "api_key": "sk-x"}}},
        )
        self.assertEqual(resolve_api_key(cfg), "")
        self.assertFalse(is_vlm_judge_configured(cfg))

    def test_local_yaml_merge(self) -> None:
        td = Path(tempfile.mkdtemp())
        mem = td / ".memory-art"
        mem.mkdir()
        local_key = "sk-ant-local-unit-test-key99"
        (mem / "vlm_judge.local.yaml").write_text(
            f"vlm_judge:\n  provider: anthropic\n  model: claude-test\n  api_key: {local_key}\n",
            encoding="utf-8",
        )
        with mock.patch.dict(os.environ, {}, clear=False):
            for k in ("PMEM_VLM_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
                os.environ.pop(k, None)
            cfg = load_vlm_judge_config(td, {"config": {"vlm_judge": {"enabled": "auto"}}})
            self.assertEqual(cfg["provider"], "anthropic")
            self.assertEqual(cfg["model"], "claude-test")
            self.assertEqual(resolve_api_key(cfg), local_key)


class TestVlmJudgeParse(unittest.TestCase):
    def test_observations_from_payload(self) -> None:
        obs = observations_from_vlm_payload({
            "composition": 8.6,
            "lighting_color": 8.2,
            "perspective_anatomy": 7.8,
            "texture_detail": 8.0,
            "spec_style": 8.4,
            "defects": "平光",
            "strengths": "色板稳",
            "next_fix": "加轮廓光",
            "score_evidence": {
                "composition": "主体偏左，右侧留白",
                "lighting_color": "脸部受光均匀",
            },
        })
        self.assertIn("构图8.6", obs["dims"])
        self.assertEqual(obs["defects"], "平光")
        self.assertEqual(obs["score_evidence"]["composition"], "主体偏左，右侧留白")
        self.assertEqual(obs["score_evidence"]["lighting_color"], "脸部受光均匀")

    def test_agent_fallback_prompt_requires_pixel_evidence_and_borderline_reread(self) -> None:
        from skills_kit.absolute_5d_agent_rubric import agent_absolute_5d_judge_prompt

        prompt = agent_absolute_5d_judge_prompt(
            target_threshold=9.5,
            dim_weights={"composition": 0.2, "lighting_color": 0.25},
            anatomy_floor=7.5,
        )
        self.assertIn("像素依据", prompt)
        self.assertIn("自动临界复评", prompt)
        self.assertIn("不参考第一遍分数", prompt)
        self.assertIn("构图=15%", prompt)
        vlm_prompt = build_judge_system_prompt({
            "dim_weights": {
                "composition": 0.20,
                "lighting_color": 0.25,
                "perspective_anatomy": 0.20,
                "texture_detail": 0.20,
                "spec_style": 0.15,
            }
        })
        self.assertIn("构图15%", vlm_prompt)
        self.assertIn("无瑕度25%", vlm_prompt)

    def test_borderline_remote_score_gets_one_independent_rerate(self) -> None:
        td = Path(tempfile.mkdtemp())
        (td / ".memory-art").mkdir()
        img = td / "candidate.png"
        img.write_bytes(b"image")

        def judged(score: float) -> dict[str, object]:
            obs = observations_from_vlm_payload({
                "composition": score,
                "lighting_color": score,
                "perspective_anatomy": score,
                "texture_detail": score,
                "spec_style": score,
                "flawlessness": score,
                "score_evidence": {"composition": f"主体边界可见，评分 {score}"},
                "defects": "边缘略软",
                "strengths": "主体轮廓清楚",
                "next_fix": "收紧边缘",
            })
            obs.update({"provider": "openai", "model": "test-vlm"})
            return obs

        with mock.patch("vlm_judge.is_vlm_judge_configured", return_value=True), \
             mock.patch("vlm_judge.call_vision_judge", side_effect=[judged(9.4), judged(9.5)]) as call:
            res = maybe_run_independent_vlm_judge(
                str(img),
                root=td,
                data={"config": {"vlm_judge": {
                    "enabled": "auto",
                    "api_key": "sk-proj-unit-test-key-abcdef",
                    "write_sidecar": True,
                }}},
                scale_prof={"scale": "medium", "target_score_threshold": 9.5},
            )

        self.assertEqual(call.call_count, 2)
        self.assertIn("构图9.5", res["dims"])
        self.assertTrue(res["review"]["rerated"])
        self.assertEqual(res["review"]["pass_count"], 2)
        self.assertEqual(res["review"]["score_spread"], 0.1)
        self.assertIn("composition", res["score_evidence"])
        self.assertIn("flawlessness", res["evidence_missing_dims"])
        self.assertTrue(call.call_args_list[1].kwargs["independent_rereview"])
        saved = json.loads(img.with_suffix(".png.vlm.json").read_text(encoding="utf-8"))
        self.assertTrue(saved["review"]["rerated"])
        self.assertIn("composition", saved["score_evidence"])
        self.assertIn("flawlessness", saved["evidence_missing_dims"])

    def test_remote_score_far_from_threshold_is_not_rerated(self) -> None:
        td = Path(tempfile.mkdtemp())
        (td / ".memory-art").mkdir()
        img = td / "candidate.png"
        img.write_bytes(b"image")
        obs = observations_from_vlm_payload({
            "composition": 8.0,
            "lighting_color": 8.0,
            "perspective_anatomy": 8.0,
            "texture_detail": 8.0,
            "spec_style": 8.0,
            "flawlessness": 8.0,
        })
        obs.update({"provider": "openai", "model": "test-vlm"})

        with mock.patch("vlm_judge.is_vlm_judge_configured", return_value=True), \
             mock.patch("vlm_judge.call_vision_judge", return_value=obs) as call:
            res = maybe_run_independent_vlm_judge(
                str(img),
                root=td,
                data={"config": {"vlm_judge": {
                    "enabled": "auto",
                    "api_key": "sk-proj-unit-test-key-abcdef",
                    "write_sidecar": False,
                }}},
                scale_prof={"scale": "medium", "target_score_threshold": 9.5},
            )

        self.assertEqual(call.call_count, 1)
        self.assertFalse(res["review"]["rerated"])

    def test_failed_rerate_keeps_first_valid_score(self) -> None:
        td = Path(tempfile.mkdtemp())
        (td / ".memory-art").mkdir()
        img = td / "candidate.png"
        img.write_bytes(b"image")
        first = observations_from_vlm_payload({
            "composition": 9.4,
            "lighting_color": 9.4,
            "perspective_anatomy": 9.4,
            "texture_detail": 9.4,
            "spec_style": 9.4,
            "flawlessness": 9.4,
        })

        with mock.patch("vlm_judge.is_vlm_judge_configured", return_value=True), \
             mock.patch("vlm_judge.call_vision_judge", side_effect=[first, RuntimeError("temporary API error")]):
            res = maybe_run_independent_vlm_judge(
                str(img),
                root=td,
                data={"config": {"vlm_judge": {
                    "enabled": "auto",
                    "api_key": "sk-proj-unit-test-key-abcdef",
                    "write_sidecar": False,
                }}},
                scale_prof={"scale": "medium", "target_score_threshold": 9.5},
            )

        self.assertEqual(res["source"], "independent_vlm")
        self.assertIn("构图9.4", res["dims"])
        self.assertFalse(res["review"]["rerated"])
        self.assertIn("temporary API error", res["review"]["recheck_error"])

    def test_bridge_keeps_vlm_evidence_and_rerate_metadata(self) -> None:
        from skills_kit.converge_judge_bridge import score_for_converge

        td = Path(tempfile.mkdtemp())
        image = td / "candidate.png"
        remote = {
            "active": True,
            "source": "independent_vlm",
            "dims": "构图9.4/光影9.4/透视9.4/质感9.4/风格9.4/无瑕度9.4",
            "defects": "边缘略软",
            "provider": "openai",
            "model": "test-vlm",
            "score_evidence": {"composition": "主体偏左"},
            "evidence_missing_dims": ["flawlessness"],
            "review": {"pass_count": 2, "rerated": True, "score_spread": 0.1},
        }
        with mock.patch("vlm_judge.maybe_run_independent_vlm_judge", return_value=remote):
            result = score_for_converge(
                {"path": str(image), "module": "art.general", "round": 1},
                {},
                "test-model",
                root=td,
                scale_prof={
                    "scale": "medium",
                    "target_score_threshold": 9.5,
                    "dim_weights": {
                        "composition": 0.20,
                        "lighting_color": 0.25,
                        "perspective_anatomy": 0.20,
                        "texture_detail": 0.20,
                        "spec_style": 0.15,
                    },
                },
            )

        self.assertEqual(result["score_evidence"]["composition"], "主体偏左")
        self.assertEqual(result["evidence_missing_dims"], ["flawlessness"])
        self.assertTrue(result["review"]["rerated"])

    def test_maybe_run_falls_back_without_key(self) -> None:
        # Use an empty temp project root so repo .memory-art/vlm_judge.local.yaml
        # cannot leak a real key into this unit test.
        td = Path(tempfile.mkdtemp())
        (td / ".memory-art").mkdir()
        with mock.patch.dict(os.environ, {}, clear=False):
            for k in ("PMEM_VLM_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
                os.environ.pop(k, None)
            res = maybe_run_independent_vlm_judge(
                "",
                root=td,
                data={"config": {"vlm_judge": {"enabled": "auto", "api_key": ""}}},
                cli_dims="构图9.0/光影9.0/透视9.0/质感9.0/风格9.0",
                cli_defects="干净",
            )
            self.assertEqual(res["source"], "agent_self_judge")
            self.assertEqual(res["dims"], "构图9.0/光影9.0/透视9.0/质感9.0/风格9.0")

    def test_maybe_run_uses_remote_when_mocked(self) -> None:
        fake_obs = {
            "dims": "构图8.5/光影8.5/透视8.5/质感8.5/风格8.5",
            "defects": "略平",
            "strengths": "ok",
            "next_fix": "加层次",
            "provider": "openai",
            "model": "gpt-4o",
            "raw_payload": {},
        }
        img = ROOT / "comparison" / "scale_01_night_city_high.jpg"
        with mock.patch("vlm_judge.is_vlm_judge_configured", return_value=True), \
             mock.patch("vlm_judge.call_vision_judge", return_value=fake_obs):
            res = maybe_run_independent_vlm_judge(
                str(img),
                root=ROOT,
                data={"config": {"vlm_judge": {
                    "enabled": "auto",
                    "api_key": "sk-proj-unit-test-key-abcdef",
                    "write_sidecar": False,
                }}},
                cli_dims="构图9.9/光影9.9/透视9.9/质感9.9/风格9.9",
            )
            self.assertEqual(res["source"], "independent_vlm")
            self.assertIn("构图8.5", res["dims"])
            self.assertNotIn("9.9", res["dims"])

    def test_auto_vlm_judge_prefers_remote_dims(self) -> None:
        from skills_kit import auto_vlm_judge_image, get_converge_scale_profile
        img = ROOT / "comparison" / "scale_01_night_city_high.jpg"
        prof = get_converge_scale_profile("medium")
        remote = {
            "source": "independent_vlm",
            "active": True,
            "dims": "构图8.0/光影8.0/透视8.0/质感8.0/风格8.0",
            "defects": "平光",
            "strengths": "构图尚可",
            "next_fix": "加重轮廓光",
            "provider": "openai",
            "model": "gpt-4o",
            "error": "",
        }
        with mock.patch("vlm_judge.maybe_run_independent_vlm_judge", return_value=remote):
            res = auto_vlm_judge_image(
                str(img),
                prof,
                round_num=1,
                dims="构图9.9/光影9.9/透视9.9/质感9.9/风格9.9",
                defects="完美",
                root=ROOT,
                data={"config": {"vlm_judge": {"api_key": "sk-proj-unit-test-key-abcdef"}}},
            )
        self.assertEqual(res["judge_source"], "independent_vlm")
        self.assertLessEqual(res["calibrated_score"], 8.90)  # 平光 anti-inflation
        self.assertFalse(res["passed"])

    def test_stale_independent_sidecar_not_used_without_key(self) -> None:
        from skills_kit import auto_vlm_judge_image, get_converge_scale_profile
        import shutil
        td = Path(tempfile.mkdtemp())
        img = td / "cand.jpg"
        shutil.copy2(ROOT / "comparison" / "scale_01_night_city_high.jpg", img)
        sidecar = img.with_suffix(img.suffix + ".vlm.json")
        sidecar.write_text(json.dumps({
            "source": "independent_vlm",
            "dims": "构图9.9/光影9.9/透视9.9/质感9.9/风格9.9",
            "defects": "完美",
        }), encoding="utf-8")
        with mock.patch.dict(os.environ, {}, clear=False):
            for k in ("PMEM_VLM_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
                os.environ.pop(k, None)
            res = auto_vlm_judge_image(
                str(img),
                get_converge_scale_profile("medium"),
                round_num=1,
                dims="",
                defects="画面干净",
                root=td,
                data={"config": {"vlm_judge": {"enabled": "auto", "api_key": ""}}},
            )
        self.assertEqual(res["judge_source"], "agent_self_judge")
        self.assertIsNone(res["weighted_score"])  # empty dims, no sidecar bleed


if __name__ == "__main__":
    unittest.main()
