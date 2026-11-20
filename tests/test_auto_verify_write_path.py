"""Integration: write_memory_entry ai_params → maybe_auto_verify_on_repeat_pass."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path


class TestAutoVerifyWritePath(unittest.TestCase):
    def test_two_written_recipes_auto_verify(self) -> None:
        from feedback import write_memory_entry
        from improve.memory_trust import maybe_auto_verify_on_repeat_pass

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".memory-art" / "projects" / "demo").mkdir(parents=True)
            (root / ".memory-art" / "projects" / "demo" / "library.json").write_text(
                json.dumps({"project_id": "demo", "project_name": "demo"}),
                encoding="utf-8",
            )
            (root / ".memory-art" / "active_project.json").write_text(
                json.dumps(
                    {
                        "project_id": "demo",
                        "project_name": "demo",
                        "bound_root": str(root.resolve()),
                    }
                ),
                encoding="utf-8",
            )
            for i, score in enumerate((9.55, 9.62), start=1):
                write_memory_entry(
                    root,
                    module="character.Astra",
                    kind="recipe",
                    summary=f"过稿{i}",
                    body="body",
                    status="active",
                    trust="candidate",
                    extra_meta={"ai_params": {"prompt": "x", "score": score, "round": 1}},
                )
            # first call after one would no-op; after two → promote
            promoted = maybe_auto_verify_on_repeat_pass(root, module="character.Astra", threshold=9.5)
            self.assertEqual(len(promoted), 2)
            entries = list((root / ".memory-art" / "entries" / "character.Astra").glob("*.md"))
            self.assertEqual(len(entries), 2)
            for p in entries:
                self.assertIn("trust: verified", p.read_text(encoding="utf-8"))

    def test_replace_same_asset_does_not_demote_canonical(self) -> None:
        from feedback import write_memory_entry

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".memory-art" / "projects" / "demo").mkdir(parents=True)
            (root / ".memory-art" / "projects" / "demo" / "library.json").write_text(
                json.dumps({"project_id": "demo", "project_name": "demo"}),
                encoding="utf-8",
            )
            (root / ".memory-art" / "active_project.json").write_text(
                json.dumps(
                    {
                        "project_id": "demo",
                        "project_name": "demo",
                        "bound_root": str(root.resolve()),
                    }
                ),
                encoding="utf-8",
            )
            asset = "assets/keep.png"
            (root / "assets").mkdir(parents=True)
            (root / asset).write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 32)
            write_memory_entry(
                root,
                module="character.Astra",
                kind="recipe",
                summary="主美定稿",
                body="body1",
                asset=asset,
                status="active",
                trust="canonical",
                replace_same_asset=True,
                extra_meta={"ai_params": {"prompt": "x", "score": 9.7}},
            )
            # Simulate converge finish rewrite with default candidate trust.
            write_memory_entry(
                root,
                module="character.Astra",
                kind="recipe",
                summary="再过线同资产",
                body="body2",
                asset=asset,
                status="active",
                trust="candidate",
                replace_same_asset=True,
                extra_meta={"ai_params": {"prompt": "y", "score": 9.6}},
            )
            entries = list((root / ".memory-art" / "entries" / "character.Astra").glob("*.md"))
            self.assertEqual(len(entries), 1)
            raw = entries[0].read_text(encoding="utf-8")
            self.assertIn("trust: canonical", raw)
            self.assertIn("再过线同资产", raw)

    def test_replace_same_asset_preserves_legacy_grandfather_verified(self) -> None:
        """Old active recipe with no trust: field must not be demoted to candidate."""
        import re

        from feedback import write_memory_entry

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".memory-art" / "projects" / "demo").mkdir(parents=True)
            (root / ".memory-art" / "projects" / "demo" / "library.json").write_text(
                json.dumps({"project_id": "demo", "project_name": "demo"}),
                encoding="utf-8",
            )
            (root / ".memory-art" / "active_project.json").write_text(
                json.dumps(
                    {
                        "project_id": "demo",
                        "project_name": "demo",
                        "bound_root": str(root.resolve()),
                    }
                ),
                encoding="utf-8",
            )
            asset = "assets/legacy.png"
            (root / "assets").mkdir(parents=True)
            (root / asset).write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 32)
            # Write via API first (survives copy-isolation), then strip trust to simulate legacy.
            write_memory_entry(
                root,
                module="character.Astra",
                kind="recipe",
                summary="旧定稿无trust",
                body="old body",
                asset=asset,
                status="active",
                trust="candidate",
                replace_same_asset=True,
            )
            mod_dir = root / ".memory-art" / "entries" / "character.Astra"
            entries = list(mod_dir.glob("*.md"))
            self.assertEqual(len(entries), 1)
            legacy = entries[0]
            stripped = re.sub(r"^trust:\s*\w+\s*\n", "", legacy.read_text(encoding="utf-8"), count=1, flags=re.M)
            legacy.write_text(stripped, encoding="utf-8")
            self.assertNotIn("trust:", stripped)

            write_memory_entry(
                root,
                module="character.Astra",
                kind="recipe",
                summary="覆盖旧资产",
                body="new body",
                asset=asset,
                status="active",
                trust="candidate",
                replace_same_asset=True,
            )
            raw = legacy.read_text(encoding="utf-8")
            self.assertIn("trust: verified", raw)
            self.assertIn("覆盖旧资产", raw)


if __name__ == "__main__":
    unittest.main()
