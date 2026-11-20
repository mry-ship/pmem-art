"""Effect-oriented checks for MemoryTrust + Warm-Start + B2 + memory CLI."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _run_py(args: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(cwd) if cwd else None,
    )


class TestWarmStartTrustEffect(unittest.TestCase):
    def test_candidate_recipe_does_not_boost_confidence(self) -> None:
        from improve.warm_start import build_warm_start_pack

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".memory-art" / "entries" / "character.Astra").mkdir(parents=True)
            (root / ".memory-art" / "projects" / "demo").mkdir(parents=True)
            (root / ".memory-art" / "projects" / "demo" / "library.json").write_text(
                json.dumps({"project_id": "demo", "project_name": "demo"}),
                encoding="utf-8",
            )
            (root / ".memory-art" / "active_project.json").write_text(
                json.dumps({"project_id": "demo", "project_name": "demo", "bound_root": str(root)}),
                encoding="utf-8",
            )
            data = {
                "modules": {"character.Astra": {"status": "active", "category": "character"}},
                "entries": [
                    {
                        "id": "CAND1",
                        "module": "character.Astra",
                        "kind": "recipe",
                        "status": "active",
                        "trust": "candidate",
                        "summary": "阿斯特拉立绘过稿配方",
                        "body": "7.5头身",
                    }
                ],
                "assets": {},
                "profile": {},
            }
            pack = build_warm_start_pack(root, data, module="character.Astra", goal="阿斯特拉立绘")
            reasons = " ".join(pack.get("confidence_reasons") or [])
            self.assertIn("candidate", reasons.lower())
            self.assertNotIn("verified/canonical recipe", reasons)
            # No verified boost → confidence should stay below 0.45 from recipes alone
            self.assertLess(float(pack.get("confidence") or 0), 0.45)

    def test_verified_recipe_boosts_confidence(self) -> None:
        from improve.warm_start import build_warm_start_pack

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".memory-art" / "projects" / "demo").mkdir(parents=True)
            (root / ".memory-art" / "projects" / "demo" / "library.json").write_text(
                json.dumps({"project_id": "demo", "project_name": "demo"}),
                encoding="utf-8",
            )
            (root / ".memory-art" / "active_project.json").write_text(
                json.dumps({"project_id": "demo", "project_name": "demo", "bound_root": str(root)}),
                encoding="utf-8",
            )
            data = {
                "modules": {"character.Astra": {"status": "active", "category": "character"}},
                "entries": [
                    {
                        "id": "VER1",
                        "module": "character.Astra",
                        "kind": "recipe",
                        "status": "active",
                        "trust": "verified",
                        "summary": "阿斯特拉立绘过稿配方",
                        "body": "7.5头身",
                    }
                ],
                "assets": {},
                "profile": {},
            }
            pack = build_warm_start_pack(root, data, module="character.Astra", goal="阿斯特拉立绘")
            reasons = " ".join(pack.get("confidence_reasons") or [])
            self.assertIn("verified/canonical", reasons)
            self.assertGreaterEqual(float(pack.get("confidence") or 0), 0.45)


class TestMemoryCliEffect(unittest.TestCase):
    def test_promote_revoke_via_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / ".memory-art" / "entries" / "character.Astra"
            d.mkdir(parents=True)
            (d / "CLI01.md").write_text(
                "---\n"
                "id: CLI01\n"
                "module: character.Astra\n"
                "kind: recipe\n"
                "status: active\n"
                "trust: candidate\n"
                "summary: \"cli recipe\"\n"
                "---\nbody\n",
                encoding="utf-8",
            )
            proc = _run_py(
                [
                    str(REPO / "pmem_art.py"),
                    "--root",
                    str(root),
                    "memory",
                    "promote",
                    "--id",
                    "CLI01",
                    "--to",
                    "verified",
                ]
            )
            self.assertEqual(proc.returncode, 0, (proc.stdout or "") + (proc.stderr or ""))
            raw = (d / "CLI01.md").read_text(encoding="utf-8")
            self.assertIn("trust: verified", raw)

            proc2 = _run_py(
                [
                    str(REPO / "pmem_art.py"),
                    "--root",
                    str(root),
                    "memory",
                    "revoke",
                    "--id",
                    "CLI01",
                    "--reason",
                    "test",
                ]
            )
            self.assertEqual(proc2.returncode, 0, (proc2.stdout or "") + (proc2.stderr or ""))
            raw2 = (d / "CLI01.md").read_text(encoding="utf-8")
            self.assertIn("status: revoked", raw2)


class TestB2EffectPipeline(unittest.TestCase):
    def test_dry_run_and_assemble_gate(self) -> None:
        proc = _run_py([str(REPO / "benchmarks" / "b2_visual_bench.py"), "--dry-run"], cwd=REPO)
        self.assertEqual(proc.returncode, 0, (proc.stdout or "") + (proc.stderr or ""))
        self.assertIn("SUITE_OK", proc.stdout or "")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # non-empirical row must not claim evolution
            results = root / ".memory-art" / "_profile" / "b2_results.jsonl"
            results.parent.mkdir(parents=True)
            results.write_text(
                json.dumps(
                    {
                        "ok": True,
                        "empirical": False,
                        "arm": "warm_start",
                        "metrics": {"brief_fit": 0.9},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            proc2 = _run_py(
                [
                    str(REPO / "benchmarks" / "b2_visual_bench.py"),
                    "--root",
                    str(root),
                    "--assemble",
                ],
                cwd=REPO,
            )
            self.assertEqual(proc2.returncode, 0, (proc2.stdout or "") + (proc2.stderr or ""))
            last = json.loads((root / ".memory-art" / "_profile" / "b2_last.json").read_text(encoding="utf-8"))
            self.assertFalse(last.get("empirical"))


class TestWriteMemoryTrustDefault(unittest.TestCase):
    def test_feedback_write_defaults_candidate(self) -> None:
        from feedback import write_memory_entry

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".memory-art" / "projects" / "demo").mkdir(parents=True)
            (root / ".memory-art" / "projects" / "demo" / "library.json").write_text(
                json.dumps({"project_id": "demo", "project_name": "demo"}),
                encoding="utf-8",
            )
            (root / ".memory-art" / "active_project.json").write_text(
                json.dumps({"project_id": "demo", "project_name": "demo", "bound_root": str(root)}),
                encoding="utf-8",
            )
            path = write_memory_entry(
                root,
                module="character.Astra",
                kind="style_redline",
                summary="禁赛博紫",
                body="不要霓虹紫边光",
            )
            raw = path.read_text(encoding="utf-8")
            self.assertIn("trust: candidate", raw)


if __name__ == "__main__":
    unittest.main()
