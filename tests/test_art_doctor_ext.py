"""Art doctor extras: skills / candidate backlog / repair tips."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from improve.art_doctor_ext import (
    build_repair_tips,
    check_candidate_backlog,
    check_missing_trust,
    check_skill_files,
    collect_art_doctor_extras,
)


class TestArtDoctorExt(unittest.TestCase):
    def test_skill_files_in_repo(self) -> None:
        root = Path(__file__).resolve().parent.parent
        info = check_skill_files(root)
        self.assertTrue(info.get("ok"), msg=info)
        self.assertIn("pmem-draw", info.get("present") or [])

    def test_candidate_backlog_soft_limit(self) -> None:
        entries = [
            {"id": f"c{i}", "kind": "recipe", "status": "active", "trust": "candidate"}
            for i in range(21)
        ]
        # provisional / inferred must not inflate promote queue
        entries.append({"id": "P1", "kind": "recipe", "status": "provisional"})
        entries.append({"id": "LEGACY", "kind": "recipe", "status": "active"})  # no trust → not candidate queue
        info = check_candidate_backlog({"entries": entries}, soft_limit=20)
        self.assertFalse(info.get("ok"))
        self.assertEqual(info.get("candidate_recipes"), 21)

    def test_missing_trust_soft_signal(self) -> None:
        entries = [
            {"id": "M1", "kind": "style_redline", "status": "active", "summary": "避免赛博"},
            {"id": "M2", "kind": "art_decision", "status": "active", "summary": "水彩优先"},
            {"id": "R0", "kind": "recipe", "status": "active", "summary": "旧配方"},  # 不计 doctor 软信号
            {"id": "OK", "kind": "style_redline", "status": "active", "trust": "verified"},
            {"id": "C1", "kind": "style_redline", "status": "active", "trust": "candidate"},
        ]
        info = check_missing_trust({"entries": entries})
        self.assertFalse(info.get("ok"))
        self.assertEqual(info.get("missing_total"), 2)
        self.assertEqual(info.get("missing_redlines"), 1)
        self.assertEqual(info.get("missing_decisions"), 1)
        self.assertEqual(info.get("missing_recipes"), 0)
        self.assertIn("promote-missing", info.get("hint") or "")

    def test_repair_tips_include_b2(self) -> None:
        tips = build_repair_tips(
            skills={"ok": True, "hint": ""},
            backlog={"ok": True, "hint": ""},
            anchors={"ok": True, "hint": ""},
            b2={"ok": False, "skipped": False, "regressions": ["style_consistency: 0.8 → 0.5"]},
            missing_trust={"ok": False, "hint": "缺 trust 2 条"},
        )
        self.assertTrue(any("B2" in t for t in tips))
        self.assertTrue(any("缺 trust" in t for t in tips))

    def test_collect_on_temp(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # no skills dirs → missing list
            extras = collect_art_doctor_extras(root, {"entries": [], "asset_gap_entries": []})
            self.assertFalse((extras.get("skills") or {}).get("ok"))


if __name__ == "__main__":
    unittest.main()
