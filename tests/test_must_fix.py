"""must_fix clip + inject: stable additive generate constraints."""
from __future__ import annotations

import unittest

from skills_kit.must_fix import (
    clip_must_fix,
    inject_must_fix,
    previous_round_next_fix,
)


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


if __name__ == "__main__":
    unittest.main()
