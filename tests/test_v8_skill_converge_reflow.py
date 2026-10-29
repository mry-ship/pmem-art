"""Unit tests for V8 skill converge pad/stop/reflow policy (no API / no bots)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from v8_skill_converge_policy import (  # noqa: E402
    choose_next_pad,
    decide_round_stop,
    pick_best_round_on_stop,
    rewrite_reflow_by_dims,
    should_force_ref_pad,
    truncate_prompt,
)


class TestPadAndStop(unittest.TestCase):
    def test_default_pad_ref_always(self) -> None:
        ref = Path("/tmp/ref.png")
        cur = Path("/tmp/r3.jpg")
        nxt = choose_next_pad(
            mode="ref", ref=ref, current_out=cur, score_ok=True, total=9.5, best_total=9.2
        )
        self.assertEqual(nxt, ref)

    def test_previous_pad_chains_only_on_score_ok(self) -> None:
        ref = Path("/tmp/ref.png")
        cur = Path("/tmp/r3.jpg")
        self.assertEqual(
            choose_next_pad(
                mode="previous", ref=ref, current_out=cur, score_ok=True, total=9.0, best_total=8.5
            ),
            cur,
        )
        self.assertEqual(
            choose_next_pad(
                mode="previous", ref=ref, current_out=cur, score_ok=False, total=None, best_total=8.5
            ),
            ref,
        )

    def test_auto_pad_stays_on_original_ref(self) -> None:
        ref = Path("/tmp/ref.png")
        cur = Path("/tmp/r3.jpg")
        self.assertEqual(
            choose_next_pad(
                mode="auto", ref=ref, current_out=cur, score_ok=True, total=9.2, best_total=9.0
            ),
            ref,
        )
        self.assertEqual(
            choose_next_pad(
                mode="auto", ref=ref, current_out=cur, score_ok=True, total=8.5, best_total=9.0, auto_drop=0.2
            ),
            ref,
        )
        self.assertEqual(
            choose_next_pad(
                mode="auto", ref=ref, current_out=cur, score_ok=True, total=8.95, best_total=9.0, auto_drop=0.2
            ),
            ref,
        )

    def test_stop_requires_anatomy_floor(self) -> None:
        self.assertIsNone(
            decide_round_stop(
                score_ok=True,
                total=9.7,
                dims={"perspective_anatomy": 7.5},
                round_num=3,
                min_rounds=2,
                threshold=9.5,
                anatomy_floor=8.5,
                best_total=9.5,
                no_improve_streak=0,
            )
        )
        self.assertEqual(
            decide_round_stop(
                score_ok=True,
                total=9.7,
                dims={"perspective_anatomy": 8.6},
                round_num=3,
                min_rounds=2,
                threshold=9.5,
                anatomy_floor=8.5,
                best_total=9.5,
                no_improve_streak=0,
            ),
            "STOP_TARGET_REACHED",
        )
        # Missing anatomy dims: fail closed (do not STOP_TARGET_REACHED)
        self.assertIsNone(
            decide_round_stop(
                score_ok=True,
                total=9.7,
                dims={"lighting_color": 9.8},
                round_num=3,
                min_rounds=2,
                threshold=9.5,
                anatomy_floor=8.5,
                best_total=9.5,
                no_improve_streak=0,
            )
        )
        self.assertIsNone(
            decide_round_stop(
                score_ok=True,
                total=9.7,
                dims=None,
                round_num=3,
                min_rounds=2,
                threshold=9.5,
                anatomy_floor=8.5,
                best_total=9.5,
                no_improve_streak=0,
            )
        )

    def test_plateau_and_regression(self) -> None:
        self.assertEqual(
            decide_round_stop(
                score_ok=True,
                total=8.8,
                dims={"perspective_anatomy": 9.0},
                round_num=4,
                min_rounds=1,
                threshold=9.5,
                anatomy_floor=8.5,
                best_total=9.0,
                no_improve_streak=2,
            ),
            "STOP_PLATEAU",
        )
        self.assertEqual(
            decide_round_stop(
                score_ok=True,
                total=8.5,
                dims={"perspective_anatomy": 9.0},
                round_num=4,
                min_rounds=1,
                threshold=9.5,
                anatomy_floor=8.5,
                best_total=9.0,
                no_improve_streak=0,
                regression_drop=0.3,
            ),
            "STOP_REGRESSION",
        )

    def test_score_fail_never_stops(self) -> None:
        self.assertIsNone(
            decide_round_stop(
                score_ok=False,
                total=None,
                dims=None,
                round_num=5,
                min_rounds=1,
                threshold=9.5,
                anatomy_floor=8.5,
                best_total=9.0,
                no_improve_streak=5,
            )
        )

    def test_anatomy_block_still_allows_plateau(self) -> None:
        # total over threshold but anat weak → not STOP_TARGET; plateau still fires
        self.assertEqual(
            decide_round_stop(
                score_ok=True,
                total=9.7,
                dims={"perspective_anatomy": 7.0},
                round_num=4,
                min_rounds=1,
                threshold=9.5,
                anatomy_floor=8.5,
                best_total=9.7,
                no_improve_streak=2,
            ),
            "STOP_PLATEAU",
        )

    def test_anatomy_alias_alone_does_not_unlock_stop(self) -> None:
        # Only loose alias present → fail closed (no STOP_TARGET)
        self.assertIsNone(
            decide_round_stop(
                score_ok=True,
                total=9.7,
                dims={"perspective": 9.9},
                round_num=3,
                min_rounds=1,
                threshold=9.5,
                anatomy_floor=8.5,
                best_total=9.5,
                no_improve_streak=0,
            )
        )

    def test_force_ref_skips_previous_pad(self) -> None:
        self.assertFalse(
            should_force_ref_pad(
                pad_mode="previous",
                total=9.7,
                threshold=9.5,
                dims={"perspective_anatomy": 7.0},
                anatomy_floor=8.5,
            )
        )
        self.assertTrue(
            should_force_ref_pad(
                pad_mode="ref",
                total=9.7,
                threshold=9.5,
                dims={"perspective_anatomy": 7.0},
                anatomy_floor=8.5,
            )
        )

    def test_pick_best_on_stop_target_prefers_anatomy_ok(self) -> None:
        weak = {"round": 2, "total": 9.85, "dims": {"perspective_anatomy": 7.0}}
        ok = {"round": 3, "total": 9.62, "dims": {"perspective_anatomy": 8.8}}
        picked = pick_best_round_on_stop(
            stop_reason="STOP_TARGET_REACHED",
            best_round=weak,
            current=ok,
            anatomy_floor=8.5,
        )
        self.assertEqual(picked["round"], 3)
        # plateau keeps historical max
        picked2 = pick_best_round_on_stop(
            stop_reason="STOP_PLATEAU",
            best_round=weak,
            current=ok,
            anatomy_floor=8.5,
        )
        self.assertEqual(picked2["round"], 2)

    def test_anatomy_block_still_allows_regression(self) -> None:
        self.assertEqual(
            decide_round_stop(
                score_ok=True,
                total=9.3,
                dims={"perspective_anatomy": 7.0},
                round_num=4,
                min_rounds=1,
                threshold=9.5,
                anatomy_floor=8.5,
                best_total=9.7,
                no_improve_streak=0,
                regression_drop=0.3,
            ),
            "STOP_REGRESSION",
        )


class TestReflowAndTruncate(unittest.TestCase):
    def test_reflow_prefers_anatomy_not_volume_light(self) -> None:
        out = rewrite_reflow_by_dims(
            "GOAL keep camera | 乌篷船低机位",
            defects=["加强体积光", "手部糊"],
            dims={"perspective_anatomy": 7.0, "lighting_color": 9.5, "texture_detail": 8.0},
            api_scale="high",
            max_fixes=2,
        )
        self.assertIn("【回流修正】", out)
        self.assertIn("joint", out.lower())
        self.assertNotIn("加强体积光", out)
        self.assertNotIn("体积光", out)
        self.assertNotIn("volumetric", out.lower())
        self.assertIn("乌篷船", out)

    def test_reflow_lighting_tip_avoids_volume_when_anat_weak(self) -> None:
        # lighting is the lowest dim → tip selected first, must not push 体积光
        out = rewrite_reflow_by_dims(
            "base",
            defects=[],
            dims={"perspective_anatomy": 7.0, "lighting_color": 6.0, "texture_detail": 9.0},
            api_scale="high",
            max_fixes=2,
        )
        self.assertNotIn("体积光", out)
        self.assertNotIn("volumetric", out.lower())
        self.assertIn("key-light", out.lower())

    def test_reflow_no_empty_volume_fallback(self) -> None:
        out = rewrite_reflow_by_dims(
            "base prompt",
            defects=[],
            dims={"perspective_anatomy": 7.2, "texture_detail": 9.0},
            api_scale="high",
        )
        self.assertIn("joint", out.lower())
        self.assertNotIn("体积光/材质区分", out)

    def test_truncate_keeps_head_drops_reflow(self) -> None:
        head = "GOAL " + ("x" * 100)
        full = head + " | 【回流修正】" + ("y" * 4000)
        trunc = truncate_prompt(full, budget=200)
        self.assertTrue(trunc.startswith("GOAL"))
        self.assertLessEqual(len(trunc), 200)


class TestScorerByDimCompat(unittest.TestCase):
    def test_tail_keeps_high_volume_hint(self) -> None:
        sys.path.insert(0, str(ROOT / "scripts"))
        from absolute_5d_scorer import rewrite_prompt_from_defects  # noqa: E402

        out = rewrite_prompt_from_defects(
            "base",
            defects=["手糊"],
            api_scale="high",
            strategy="tail",
        )
        self.assertNotIn("体积光", out)
        self.assertIn("已经有的层次", out)
        self.assertIn("手糊", out)

    def test_by_dim_keeps_intent_reason(self) -> None:
        sys.path.insert(0, str(ROOT / "scripts"))
        from absolute_5d_scorer import rewrite_prompt_from_defects  # noqa: E402

        out = rewrite_prompt_from_defects(
            "base",
            defects=[],
            intent={"pass": False, "reason": "机位未跳够"},
            api_scale="medium",
            strategy="by_dim",
            dims={},
        )
        self.assertIn("机位未跳够", out)
        self.assertNotIn("加强体积光/冷暖分离", out)

    def test_by_dim_intent_survives_full_dims(self) -> None:
        sys.path.insert(0, str(ROOT / "scripts"))
        from absolute_5d_scorer import rewrite_prompt_from_defects  # noqa: E402

        out = rewrite_prompt_from_defects(
            "base",
            defects=[],
            intent={"pass": False, "reason": "机位未跳够"},
            api_scale="medium",
            strategy="by_dim",
            dims={
                "perspective_anatomy": 8.0,
                "lighting_color": 7.0,
                "texture_detail": 7.5,
                "composition": 8.2,
            },
        )
        self.assertIn("机位未跳够", out)

    def test_runner_helpers_import_without_vlm(self) -> None:
        # Fresh path: ensure module load does not require vlm_quant_5d_scorer
        sys.path.insert(0, str(ROOT / "scripts"))
        sys.modules.pop("run_v8_20_skill_converge", None)
        sys.modules.pop("vlm_quant_5d_scorer", None)
        import run_v8_20_skill_converge as r  # noqa: F401

        self.assertTrue(hasattr(r, "AR_SIZE"))
        self.assertTrue(hasattr(r, "best_overlay"))
        self.assertNotIn("vlm_quant_5d_scorer", sys.modules)


if __name__ == "__main__":
    unittest.main()
