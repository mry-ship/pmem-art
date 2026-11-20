"""Memory trust tiers: candidate → verified → canonical."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from improve.memory_trust import (
    entry_trust,
    maybe_auto_verify_on_repeat_pass,
    normalize_trust,
    promote_entry,
    resolve_conflict,
    revoke_entry,
    trust_counts_for_recipe_confidence,
)


class TestNormalizeTrust(unittest.TestCase):
    def test_explicit(self) -> None:
        self.assertEqual(normalize_trust("canonical"), "canonical")
        self.assertEqual(normalize_trust("verified", status="active"), "verified")

    def test_provisional_is_candidate(self) -> None:
        self.assertEqual(normalize_trust("", status="provisional"), "candidate")

    def test_missing_trust_is_candidate(self) -> None:
        self.assertEqual(normalize_trust("", status="active"), "candidate")

    def test_recipe_confidence_gate(self) -> None:
        self.assertFalse(
            trust_counts_for_recipe_confidence(
                {"kind": "recipe", "status": "active", "trust": "candidate"}
            )
        )
        self.assertTrue(
            trust_counts_for_recipe_confidence(
                {"kind": "recipe", "status": "active", "trust": "verified"}
            )
        )


class TestPromoteRevoke(unittest.TestCase):
    def _write_entry(
        self,
        root: Path,
        eid: str,
        *,
        trust: str = "candidate",
        score: float | None = 9.6,
    ) -> Path:
        d = root / ".memory-art" / "entries" / "character.Astra"
        d.mkdir(parents=True, exist_ok=True)
        p = d / f"{eid}.md"
        score_line = f"ai_params: {{\"score\": {score}}}\n" if score is not None else ""
        p.write_text(
            "---\n"
            f"id: {eid}\n"
            "module: character.Astra\n"
            "kind: recipe\n"
            "status: active\n"
            f"trust: {trust}\n"
            "summary: \"test recipe\"\n"
            f"{score_line}"
            "---\n"
            "body\n",
            encoding="utf-8",
        )
        return p

    def test_promote_and_revoke(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_entry(root, "CHATTEST01")
            promote_entry(root, "CHATTEST01", to="verified", by="tester")
            raw = (root / ".memory-art" / "entries" / "character.Astra" / "CHATTEST01.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("trust: verified", raw)
            revoke_entry(root, "CHATTEST01", reason="画师否定")
            raw2 = (root / ".memory-art" / "entries" / "character.Astra" / "CHATTEST01.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("status: revoked", raw2)
            self.assertEqual(
                entry_trust({"status": "revoked", "trust": "candidate"}),
                "candidate",
            )

    def test_resolve_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_entry(root, "KEEP01", trust="candidate")
            self._write_entry(root, "DROP01", trust="verified")
            resolve_conflict(root, keep_id="KEEP01", drop_id="DROP01", reason="新合同")
            keep = (root / ".memory-art" / "entries" / "character.Astra" / "KEEP01.md").read_text(
                encoding="utf-8"
            )
            drop = (root / ".memory-art" / "entries" / "character.Astra" / "DROP01.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("trust: verified", keep)
            self.assertIn("status: superseded", drop)

    def test_auto_verify_needs_two_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_entry(root, "R1", trust="candidate", score=9.6)
            self.assertEqual(maybe_auto_verify_on_repeat_pass(root, module="character.Astra"), [])
            self._write_entry(root, "R2", trust="candidate", score=9.55)
            promoted = maybe_auto_verify_on_repeat_pass(root, module="character.Astra")
            self.assertEqual(promoted, [])
            for eid in ("R1", "R2"):
                raw = (root / ".memory-art" / "entries" / "character.Astra" / f"{eid}.md").read_text(
                    encoding="utf-8"
                )
                self.assertIn("trust: candidate", raw)


if __name__ == "__main__":
    unittest.main()
