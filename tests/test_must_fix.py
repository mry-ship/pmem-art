"""must_fix clip + inject: stable additive generate constraints."""
from __future__ import annotations

import unittest

from skills_kit.must_fix import (
    clip_must_fix,
    inject_must_fix,
    previous_round_next_fix,
    sanitize_continuation_fix,
)
from skills_kit.prompt_scale import compose_continuation_prompt, get_converge_scale_profile


class TestMustFix(unittest.TestCase):
    def test_clip_keeps_two_items(self) -> None:
        text = "优先删减发髻外围交叉线并整理发束走向；再用轻微明暗补强近侧眼窝；合并右肩零碎衣褶色块"
        out = clip_must_fix(text, max_items=2)
        self.assertIn("发髻", out)
        self.assertIn("眼窝", out)
        self.assertNotIn("右肩", out)

    def test_inject_idempotent(self) -> None:
        base = "watercolor half-body by window"
        fix = "减少发丝交叉；整理右肩衣褶"
        once = inject_must_fix(base, fix)
        twice = inject_must_fix(once, fix)
        self.assertEqual(once.count("MUST_FIX"), 1)
        self.assertEqual(twice, once)
        self.assertIn("MUST_FIX (≤2):", once)

    def test_previous_round_next_fix(self) -> None:
        rounds = [
            {"round": 1, "next_fix": "修发丝"},
            {"round": 2, "next_fix": "修衣褶"},
        ]
        self.assertEqual(previous_round_next_fix(rounds, 3), "修衣褶")
        self.assertEqual(previous_round_next_fix(rounds, 2), "修发丝")
        self.assertEqual(previous_round_next_fix([], 2), "")

    def test_sanitize_drops_direction_swap(self) -> None:
        text = "把右手五指画清楚；整张改成水彩题材；推倒重来换条路"
        out = sanitize_continuation_fix(text)
        self.assertIn("五指", out)
        self.assertNotIn("水彩题材", out)
        self.assertNotIn("推倒重来", out)
        clipped = clip_must_fix(text)
        self.assertIn("五指", clipped)
        self.assertNotIn("换成", clipped)
        self.assertNotIn("推倒", clipped)

    def test_continuation_pins_locks_and_bans_swap(self) -> None:
        prof = get_converge_scale_profile("medium")
        text = compose_continuation_prompt(
            "换成赛博画风；只修杯沿高光",
            prof,
            locks=["平面锁不住时仍保糖釉", "无字无脸"],
        )
        self.assertIn("只修杯沿高光", text)
        self.assertNotIn("赛博画风", text)
        self.assertIn("L1锁必须保住", text)
        self.assertIn("无字无脸", text)
        self.assertIn("禁止借改点换题材", text)


if __name__ == "__main__":
    unittest.main()
