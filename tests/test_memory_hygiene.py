"""Memory hygiene + STALE semantic split."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from improve.memory_hygiene import is_noise_candidate


class TestNoiseCandidates(unittest.TestCase):
    def test_numeric_and_layer_junk(self) -> None:
        self.assertTrue(is_noise_candidate("character.1", "assets/character/1"))
        self.assertTrue(is_noise_candidate("character.Barn", "assets/farm_layer_decomp/Layers/002_Barn.png"))
        self.assertTrue(is_noise_candidate("misc.R1", "assets/misc/r1"))
        self.assertFalse(is_noise_candidate("prop.BirdsMerge.Cute", "assets/prop/birdsmerge"))


class TestStaleMissingNotContent(unittest.TestCase):
    def test_missing_asset_is_gap_not_stale(self) -> None:
        from pmem_art import load_project

        td = Path(tempfile.mkdtemp(prefix="pmem_stale_gap_"))
        try:
            mem = td / ".memory-art"
            (mem / "entries" / "prop.Demo").mkdir(parents=True)
            (mem / "modules.yaml").write_text(
                "categories: {}\nmodules:\n  prop.Demo:\n    title: Demo\n    category: prop\n    status: active\n    paths: [assets/prop/**]\n",
                encoding="utf-8",
            )
            (mem / "config.yaml").write_text(
                "project:\n  name: demo\n  lifecycle_mode: young\ngate:\n  mode: warn\nbootstrap:\n  confirmed: true\n  asset_roots: [assets]\n",
                encoding="utf-8",
            )
            (td / "assets" / "prop").mkdir(parents=True)
            entry = mem / "entries" / "prop.Demo" / "XRECIPE.md"
            entry.write_text(
                "---\n"
                "id: XRECIPE\n"
                "module: prop.Demo\n"
                "kind: recipe\n"
                "status: active\n"
                "summary: keep this text\n"
                "assets:\n"
                "  - path: assets/prop/missing.jpg\n"
                "    role: reference\n"
                "    sha256_16: deadbeefdeadbeef\n"
                "---\nbody\n",
                encoding="utf-8",
            )
            data = load_project(td, embed_images=False)
            e = next(x for x in data["entries"] if x.get("id") == "XRECIPE")
            self.assertFalse(e.get("stale"), e.get("stale_reasons"))
            self.assertEqual(e.get("asset_gaps"), ["assets/prop/missing.jpg"])
            self.assertEqual(data.get("stale_entries"), [])
            self.assertTrue(any(g.get("id") == "XRECIPE" for g in data.get("asset_gap_entries") or []))
        finally:
            import shutil

            shutil.rmtree(td, ignore_errors=True)


class TestHygieneLearnDefault(unittest.TestCase):
    def _minimal_root(self) -> Path:
        td = Path(tempfile.mkdtemp(prefix="pmem_hyg_learn_"))
        mem = td / ".memory-art"
        (mem / "converge").mkdir(parents=True)
        (mem / "_profile").mkdir(parents=True)
        (mem / "modules.yaml").write_text(
            "categories: {}\nmodules: {}\n",
            encoding="utf-8",
        )
        (mem / "config.yaml").write_text(
            "project:\n  name: demo\n  lifecycle_mode: young\n"
            "gate:\n  mode: warn\nbootstrap:\n  confirmed: true\n  asset_roots: [assets]\n",
            encoding="utf-8",
        )
        (td / "assets").mkdir(parents=True)
        return td

    def test_default_skips_learn_accept(self) -> None:
        from pmem_art import load_project
        from improve.memory_hygiene import run_hygiene

        td = self._minimal_root()
        try:
            data = load_project(td, embed_images=False)
            report = run_hygiene(td, data, apply=True, accept_learn=False)
            learn = report.get("learn") or {}
            self.assertTrue(learn.get("skipped"))
            know = td / ".memory-art" / "_knowledge"
            self.assertFalse(any(know.rglob("*.md")) if know.is_dir() else False)
        finally:
            import shutil

            shutil.rmtree(td, ignore_errors=True)

    def test_accept_learn_consumes_stash_once(self) -> None:
        import json
        from pmem_art import load_project
        from improve.memory_hygiene import run_hygiene

        td = self._minimal_root()
        try:
            stash = td / ".memory-art" / "_profile" / "learn_proposals.json"
            stash.write_text(
                json.dumps(
                    {
                        "proposals": [
                            {
                                "id": "test-hyg-card",
                                "title": "Test card",
                                "body": "body",
                                "tags": ["test"],
                            }
                        ]
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            data = load_project(td, embed_images=False)
            report = run_hygiene(td, data, apply=True, accept_learn=True)
            self.assertTrue((report.get("learn") or {}).get("ok"))
            know = td / ".memory-art" / "_knowledge"
            self.assertTrue(any(know.rglob("*.md")))
            self.assertFalse(stash.is_file())
            report2 = run_hygiene(td, load_project(td, embed_images=False), apply=True, accept_learn=True)
            self.assertTrue((report2.get("learn") or {}).get("ok"))
            self.assertEqual(len(list(know.rglob("*.md"))), 1)
        finally:
            import shutil

            shutil.rmtree(td, ignore_errors=True)

    def test_accept_learn_stash_only_empty_queue(self) -> None:
        from pmem_art import load_project
        from improve.memory_hygiene import run_hygiene

        td = self._minimal_root()
        try:
            data = load_project(td, embed_images=False)
            report = run_hygiene(td, data, apply=True, accept_learn=True)
            learn = report.get("learn") or {}
            self.assertTrue(learn.get("ok"))
            know = td / ".memory-art" / "_knowledge"
            self.assertFalse(know.is_dir() and any(know.rglob("*.md")))
        finally:
            import shutil

            shutil.rmtree(td, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
