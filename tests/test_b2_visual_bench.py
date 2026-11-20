"""B2 suite loads and doctor-safe compare skips non-empirical stubs."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from benchmarks.b2_visual_bench import (
    assemble_empirical_report,
    compare_to_baseline,
    load_suite,
    map_vlm_to_b2_metrics,
    stub_scores,
    validate_suite,
    write_profile,
)


class TestB2Suite(unittest.TestCase):
    def test_suite_valid(self) -> None:
        suite = load_suite()
        self.assertEqual(suite.get("layer"), "B2")
        self.assertEqual(validate_suite(suite), [])
        self.assertGreaterEqual(len(suite.get("tasks") or []), 6)

    def test_stub_compare_skips(self) -> None:
        suite = load_suite()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_profile(root, stub_scores(suite))
            write_profile(root, stub_scores(suite), baseline=True)
            report = compare_to_baseline(root)
            self.assertTrue(report.get("ok"))
            self.assertTrue(report.get("skipped"))

    def test_empirical_regression(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = {
                "empirical": True,
                "aggregate": {"character_consistency": 0.80, "style_consistency": 0.75},
            }
            last = {
                "empirical": True,
                "aggregate": {"character_consistency": 0.50, "style_consistency": 0.74},
            }
            (root / ".memory-art" / "_profile").mkdir(parents=True)
            (root / ".memory-art" / "_profile" / "b2_baseline.json").write_text(
                json.dumps(base), encoding="utf-8"
            )
            (root / ".memory-art" / "_profile" / "b2_last.json").write_text(
                json.dumps(last), encoding="utf-8"
            )
            report = compare_to_baseline(root, drop=0.15)
            self.assertFalse(report.get("ok"))
            self.assertTrue(any("character_consistency" in r for r in report.get("regressions") or []))

    def test_rejects_non_image(self) -> None:
        from benchmarks.b2_visual_bench import score_task_image

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake = root / "note.txt"
            fake.write_text("x", encoding="utf-8")
            row = score_task_image(
                root, task_id="b2-char-expr", image=fake, allow_agent_fallback=True
            )
            self.assertFalse(row.get("ok"))
            self.assertIn("not an image", str(row.get("error") or ""))

    def test_map_metrics_and_assemble(self) -> None:
        suite = load_suite()
        task = next(t for t in suite["tasks"] if t["id"] == "b2-char-expr")
        metrics = map_vlm_to_b2_metrics(
            task=task,
            dims={"composition": 9.0, "perspective_anatomy": 9.2, "spec_style": 9.1},
            overall=9.3,
        )
        self.assertIn("character_consistency", metrics)
        self.assertGreater(metrics["brief_fit"], 0.9)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            results = root / ".memory-art" / "_profile" / "b2_results.jsonl"
            results.parent.mkdir(parents=True)
            row = {
                "ok": True,
                "empirical": True,
                "arm": "warm_start",
                "task_id": "b2-char-expr",
                "metrics": metrics,
            }
            results.write_text(json.dumps(row) + "\n", encoding="utf-8")
            payload = assemble_empirical_report(root, suite=suite)
            self.assertTrue(payload.get("empirical"))
            self.assertIsNotNone((payload.get("aggregate") or {}).get("brief_fit"))

    def test_assemble_skips_historical_stubs_without_poisoning(self) -> None:
        suite = load_suite()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            results = root / ".memory-art" / "_profile" / "b2_results.jsonl"
            results.parent.mkdir(parents=True)
            stub = {
                "ok": True,
                "empirical": False,
                "arm": "warm_start",
                "task_id": "b2-char-expr",
                "metrics": {"brief_fit": 0.1},
            }
            real = {
                "ok": True,
                "empirical": True,
                "arm": "warm_start",
                "task_id": "b2-char-expr",
                "metrics": {"brief_fit": 0.93, "character_consistency": 0.91},
            }
            results.write_text(
                json.dumps(stub) + "\n" + json.dumps(real) + "\n",
                encoding="utf-8",
            )
            payload = assemble_empirical_report(root, suite=suite)
            self.assertTrue(payload.get("empirical"), msg=payload)
            self.assertEqual(payload.get("rows_used"), 1)
            self.assertEqual(payload.get("rows_non_empirical_skipped"), 1)
            self.assertAlmostEqual(
                float((payload.get("aggregate") or {}).get("brief_fit") or 0), 0.93
            )


if __name__ == "__main__":
    unittest.main()
