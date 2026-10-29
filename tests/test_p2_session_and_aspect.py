#!/usr/bin/env python3
"""P2 regressions: no silent generate auto-start; Pastel/Celestial aspect contracts."""
from __future__ import annotations

import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEMO_MODULES = ROOT / ".memory-art" / "projects" / "pmem-art" / "modules.yaml"
sys.path.insert(0, str(ROOT))

from skills_kit.converge import _session_file, cmd_converge


class TestNoSilentAutoStart(unittest.TestCase):
    def test_generate_without_session_fails_and_does_not_create(self) -> None:
        sid = "_test_no_autostart_p2"
        sf = _session_file(ROOT, sid)
        if sf.exists():
            sf.unlink()
        buf = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(buf):
            rc = cmd_converge(
                ROOT,
                {"config": {"converge": {"default_scale": "medium"}}},
                "generate",
                session_id=sid,
                round_num=1,
                prompt="probe",
                silent=False,
            )
        self.assertEqual(rc, 1)
        self.assertFalse(sf.exists(), "generate must not silently create a session")
        out = buf.getvalue()
        self.assertIn("未找到收敛会话", out)
        self.assertIn("converge start", out)
        self.assertNotIn("自动初始化", out)


class TestModuleAspectContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        import pmem_art as pa
        cls.mods = (pa.load_yaml(DEMO_MODULES.read_text(encoding="utf-8")) or {}).get("modules", {})

    def test_pastel_is_4x3_1152x864(self) -> None:
        specs = (self.mods.get("character.PastelGirl") or {}).get("specs") or {}
        self.assertEqual(specs.get("aspect_ratio"), "4:3")
        self.assertEqual(specs.get("resolution"), "1152x864")
        allowed = specs.get("allowed_resolutions") or []
        self.assertIn("1152x864", allowed)
        self.assertNotIn("864x1152", allowed)

    def test_celestial_whitelist_is_9x16_only(self) -> None:
        specs = (self.mods.get("scene.CelestialCity") or {}).get("specs") or {}
        self.assertEqual(specs.get("aspect_ratio"), "9:16")
        allowed = specs.get("allowed_resolutions") or []
        self.assertIn("720x1280", allowed)
        self.assertIn("405x720", allowed)
        self.assertNotIn("864x1152", allowed)
        self.assertNotIn("1024x576", allowed)

    def test_sunlit_is_3x4(self) -> None:
        specs = (self.mods.get("character.SunlitGirl") or {}).get("specs") or {}
        self.assertEqual(specs.get("aspect_ratio"), "3:4")
        self.assertEqual(specs.get("resolution"), "864x1152")


class TestRejectedDraftNotStale(unittest.TestCase):
    def test_astra_expr_correction_not_stale(self) -> None:
        import pmem_art as pa

        demo = ROOT / ".memory-art" / "projects" / "pmem-art"
        td = Path(tempfile.mkdtemp(prefix="pmem_astra_"))
        try:
            mem = td / ".memory-art"
            mem.mkdir()
            shutil.copy2(demo / "modules.yaml", mem / "modules.yaml")
            src_entry = demo / "entries" / "character.Astra.Expressions" / "01ART006EXPRCORRECTION.md"
            dst_entry = mem / "entries" / "character.Astra.Expressions" / src_entry.name
            dst_entry.parent.mkdir(parents=True)
            shutil.copy2(src_entry, dst_entry)
            for rel in (
                "assets/character/astra_expressions_2x2.png",
                "assets/character/astra_expr_shock_draft.png",
            ):
                dst = td / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / rel, dst)
            data = pa.load_project(td)
        finally:
            shutil.rmtree(td, ignore_errors=True)
        entry = next((e for e in data["entries"] if e.get("id") == "01ART006EXPRCORRECTION"), None)
        self.assertIsNotNone(entry)
        self.assertFalse(entry.get("stale"), entry.get("stale_reasons"))
        draft = data["assets"].get("assets/character/astra_expr_shock_draft.png") or {}
        self.assertTrue(draft.get("qa_intentional_reject"))
        self.assertTrue(draft.get("qa_passed"), "rejected counter-example must not fail the gate")

    def test_astra_turnaround_multi_res_still_passes(self) -> None:
        """Whitelist 2048x1024 must bypass single aspect_ratio=1:1 contract."""
        import pmem_art as pa

        data = pa.load_project(ROOT)
        sheet = data["assets"].get("assets/character/astra_turnaround_sheet.png") or {}
        self.assertEqual(sheet.get("resolution"), "2048x1024")
        self.assertTrue(sheet.get("qa_passed"), sheet.get("qa_issues"))
        self.assertEqual(sheet.get("qa_issues") or [], [])


class TestSpecsScaffoldPresent(unittest.TestCase):
    def test_case_modules_have_specs_dirs(self) -> None:
        specs = ROOT / ".memory-art" / "specs"
        for mid in (
            "character.PastelGirl",
            "character.SunlitGirl",
            "scene.CelestialCity",
            "vfx.Nova",
        ):
            d = specs / mid
            self.assertTrue(d.is_dir(), mid)
            self.assertTrue((d / "管线规格.md").is_file(), mid)

    def test_doctor_reports_zero_missing_specs_for_case_modules(self) -> None:
        import io
        from contextlib import redirect_stdout
        import pmem_art as pa
        from lifecycle import cmd_doctor_lifecycle

        data = pa.load_project(ROOT)
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cmd_doctor_lifecycle(ROOT, data)
        self.assertEqual(rc, 0)
        out = buf.getvalue()
        self.assertIn("entries_missing_specs=0", out)
        for mid in ("character.PastelGirl", "character.SunlitGirl", "scene.CelestialCity", "vfx.Nova"):
            self.assertNotIn(f"⚠️ {mid}", out)


class TestCopyIsolationMissingOldRoot(unittest.TestCase):
    def test_same_slug_missing_bound_root_isolates(self) -> None:
        """Same project_id + different bound_root that no longer exists must still isolate."""
        from improve.project_library import ensure_project_library_bound, slugify_project_id

        td = Path(tempfile.mkdtemp(prefix="pmem_iso_"))
        try:
            proj = td / "IsoProbe"
            mem = proj / ".memory-art"
            (mem / "entries" / "keep.Me").mkdir(parents=True)
            (mem / "entries" / "keep.Me" / "x.md").write_text("secret-leak\n", encoding="utf-8")
            (mem / "_profile").mkdir(parents=True)
            (mem / "_profile" / "taste.json").write_text(
                json.dumps({"banned_habits": ["old-habit-leak"], "version": 1}, ensure_ascii=False),
                encoding="utf-8",
            )
            (mem / "modules.yaml").write_text("modules: {}\n", encoding="utf-8")
            (mem / "config.yaml").write_text("project_name: IsoProbe\n", encoding="utf-8")
            pid = slugify_project_id(proj.name)
            meta = {
                "project_id": pid,
                "project_slug": pid,
                "project_name": "IsoProbe",
                "bound_root": str(td / "does_not_exist" / "IsoProbe"),
                "origin_root": str(td / "does_not_exist" / "IsoProbe"),
                "library_dir": f".memory-art/projects/{pid}",
                "created_at": "2020-01-01 00:00:00 UTC+8",
                "updated_at": "2020-01-01 00:00:00 UTC+8",
            }
            (mem / "active_project.json").write_text(
                json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            buf = io.StringIO()
            with redirect_stdout(buf), redirect_stderr(buf):
                ensure_project_library_bound(proj)
            out = buf.getvalue()
            self.assertIn("拷贝隔离", out)
            self.assertFalse((mem / "entries" / "keep.Me").exists())
            taste = json.loads((mem / "_profile" / "taste.json").read_text(encoding="utf-8"))
            self.assertNotIn("old-habit-leak", taste.get("banned_habits") or [])
            new_meta = json.loads((mem / "active_project.json").read_text(encoding="utf-8"))
            self.assertEqual(new_meta.get("bound_root"), str(proj.resolve()))
        finally:
            shutil.rmtree(td, ignore_errors=True)


class TestPathGlobNoOverlap(unittest.TestCase):
    def test_floating_ruins_and_arcane_globs_do_not_cover_siblings(self) -> None:
        import pmem_art as pa

        mods = (pa.load_yaml(DEMO_MODULES.read_text(encoding="utf-8")) or {}).get("modules", {})
        fr = (mods.get("scene.FloatingRuins") or {}).get("paths") or []
        slash = (mods.get("vfx.ArcaneSlash") or {}).get("paths") or []
        self.assertTrue(fr)
        self.assertTrue(slash)
        self.assertNotIn("assets/scene/**", fr)
        self.assertNotIn("assets/vfx/**", slash)
        self.assertTrue(any("floating" in p for p in fr))
        self.assertTrue(any("arcane" in p for p in slash))


if __name__ == "__main__":
    unittest.main()
