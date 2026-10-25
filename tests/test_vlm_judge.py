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
        })
        self.assertIn("构图8.6", obs["dims"])
        self.assertEqual(obs["defects"], "平光")

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
