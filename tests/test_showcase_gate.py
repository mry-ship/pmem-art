from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
if "fcntl" not in sys.modules:
    sys.modules["fcntl"] = types.ModuleType("fcntl")

from skills_kit.showcase_gate import (  # noqa: E402
    audit_showcase_html,
    can_accept_winner,
    last_score,
    round_count,
)


class TestCanAcceptWinner(unittest.TestCase):
    def test_threshold_stops(self) -> None:
        self.assertTrue(can_accept_winner(1, 9.60))
        self.assertTrue(can_accept_winner(2, 9.61))

    def test_under_threshold_must_continue(self) -> None:
        self.assertFalse(can_accept_winner(1, 8.30))
        self.assertFalse(can_accept_winner(3, 8.56))

    def test_max_rounds_may_ship_best(self) -> None:
        self.assertTrue(can_accept_winner(4, 8.56))

    def test_unscored_skipped(self) -> None:
        self.assertTrue(can_accept_winner(None, None))


class TestHtmlAudit(unittest.TestCase):
    def test_flags_early_stop(self) -> None:
        html = """
        <figure><figcaption><strong>low · 3 轮</strong>8.43 → 8.50</figcaption></figure>
        <figure><figcaption><strong>原图</strong></figcaption></figure>
        """
        issues = audit_showcase_html(html)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["score"], 8.50)
        self.assertEqual(issues[0]["rounds"], 3)

    def test_skips_prompt_section_and_refs(self) -> None:
        html = """
        <section id="prompt"><figure><figcaption>方案 A 9.10</figcaption></figure></section>
        <figure><figcaption><strong>原图</strong></figcaption></figure>
        <figure><figcaption><strong>high · 4 轮</strong>8.20 → 8.40 → 8.50 → 8.52</figcaption></figure>
        """
        self.assertEqual(audit_showcase_html(html), [])

    def test_ok_when_threshold_hit(self) -> None:
        html = '<figure><figcaption><strong>high · 3 轮</strong>9.32 → 9.46 → 9.60</figcaption></figure>'
        self.assertEqual(audit_showcase_html(html), [])

    def test_parsers(self) -> None:
        self.assertEqual(round_count("low · 3 轮 8.50"), 3)
        self.assertEqual(last_score("8.43 → 8.48 → 8.50"), 8.50)
        self.assertEqual(round_count("前 4 轮漂成蓝发作废 · 本张 9.18"), 1)
        self.assertEqual(round_count("8.43 → 8.48 → 8.50"), 3)
        self.assertFalse(can_accept_winner(round_count("前 4 轮作废 · 本张 9.18"), 9.18))
        self.assertEqual(round_count("low · 4 轮 · 胜出第 3 轮 8.37 → 8.95 → 9.08 → 8.72"), 4)
        self.assertEqual(round_count("4 轮 · 第 1 轮最高 8.67 → 8.36 → 8.41 → 8.47"), 4)

    def test_missing_image_flagged(self) -> None:
        html = "<figure><figcaption><strong>clone · 1 轮</strong>未出图</figcaption></figure>"
        issues = audit_showcase_html(html)
        self.assertEqual(issues[0]["reason"], "missing_image")

    def test_voided_prior_rounds_do_not_count(self) -> None:
        html = (
            "<figure><figcaption><strong>low · 发色重锁</strong>"
            "前 4 轮漂成蓝发作废 · 本张 9.18</figcaption></figure>"
        )
        issues = audit_showcase_html(html)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["rounds"], 1)
        self.assertEqual(issues[0]["score"], 9.18)

    def test_mentions_of_source_image_are_not_skipped(self) -> None:
        html = (
            "<figure><figcaption><strong>low · 袜子重锁</strong>"
            "本张 9.00<br>跟原图对齐。</figcaption></figure>"
        )
        issues = audit_showcase_html(html)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["score"], 9.00)


if __name__ == "__main__":
    unittest.main()
