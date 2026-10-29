"""Lazy doctor: 24h throttle on spawn events, quiet report, whisper tip only on high signal."""
from __future__ import annotations

import json
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


class TestDoctorDueAndClaim(unittest.TestCase):
    def setUp(self) -> None:
        self.td = Path(tempfile.mkdtemp(prefix="pmem_doctor_"))
        (self.td / ".memory-art" / "_profile").mkdir(parents=True)

    def test_due_when_missing_state(self) -> None:
        from lifecycle import is_doctor_due

        self.assertTrue(is_doctor_due(self.td))

    def test_default_interval_is_24h(self) -> None:
        from lifecycle import DOCTOR_INTERVAL_HOURS

        self.assertEqual(DOCTOR_INTERVAL_HOURS, 24.0)

    def test_not_due_within_24h(self) -> None:
        from lifecycle import (
            _doctor_now_str,
            is_doctor_due,
            save_doctor_state,
        )

        save_doctor_state(self.td, {"last_run_at": _doctor_now_str(), "status": "ok"})
        self.assertFalse(is_doctor_due(self.td))

    def test_due_after_interval(self) -> None:
        from lifecycle import is_doctor_due, save_doctor_state
        from lifecycle import _doctor_now

        old = (_doctor_now() - timedelta(hours=25)).strftime("%Y-%m-%d %H:%M:%S UTC+8")
        save_doctor_state(self.td, {"last_run_at": old, "status": "ok"})
        self.assertTrue(is_doctor_due(self.td))

    def test_claim_blocks_double_spawn(self) -> None:
        from lifecycle import try_claim_lazy_doctor

        self.assertTrue(try_claim_lazy_doctor(self.td, interval_hours=48))
        self.assertFalse(try_claim_lazy_doctor(self.td, interval_hours=48))

    def test_spawn_failure_rolls_back_claim(self) -> None:
        from lifecycle import (
            doctor_claim_lock_path,
            load_doctor_state,
            spawn_lazy_doctor,
            try_claim_lazy_doctor,
        )

        self.assertTrue(try_claim_lazy_doctor(self.td, interval_hours=48))
        with mock.patch("subprocess.Popen", side_effect=OSError("boom")):
            self.assertFalse(spawn_lazy_doctor(self.td, source="hook:test"))
        state = load_doctor_state(self.td)
        self.assertEqual(state.get("status"), "spawn_failed")
        self.assertFalse(doctor_claim_lock_path(self.td).is_file())
        # No successful quiet run → still due; can re-claim after lock cleared
        self.assertTrue(try_claim_lazy_doctor(self.td, interval_hours=48))


class TestDoctorQuietAndTip(unittest.TestCase):
    def setUp(self) -> None:
        self.td = Path(tempfile.mkdtemp(prefix="pmem_doctor_q_"))
        (self.td / ".memory-art" / "_profile").mkdir(parents=True)
        (self.td / ".memory-art" / "entries" / "character.Demo").mkdir(parents=True)
        (self.td / "assets").mkdir(parents=True)
        self.entry = self.td / ".memory-art" / "entries" / "character.Demo" / "KEEP.md"
        self.entry.write_text("# keep me\nbody\n", encoding="utf-8")
        self.modules = self.td / ".memory-art" / "modules.yaml"
        self.modules.write_text("modules: {}\n", encoding="utf-8")

    def test_quiet_writes_state(self) -> None:
        from lifecycle import doctor_state_path, run_doctor_quiet

        data = {
            "config": {"project": {"lifecycle_mode": "young"}, "gate": {"mode": "warn"}, "bootstrap": {}},
            "modules": {},
            "entries": [],
            "stale_entries": [],
            "qa_issues": [],
        }
        summary = run_doctor_quiet(self.td, data, source="test", offer_tip=True)
        self.assertIn("coverage_pct", summary)
        state = json.loads(doctor_state_path(self.td).read_text(encoding="utf-8"))
        self.assertEqual(state.get("status"), "ok")
        self.assertTrue(state.get("last_run_at"))
        self.assertEqual(state.get("source"), "test")
        self.assertTrue(state.get("inspect_only"))

    def test_quiet_never_mutates_entries_or_modules(self) -> None:
        from lifecycle import run_doctor_quiet

        before_entry = self.entry.read_text(encoding="utf-8")
        before_mod = self.modules.read_text(encoding="utf-8")
        before_mtime = self.entry.stat().st_mtime_ns
        data = {
            "config": {"bootstrap": {"asset_roots": ["assets"]}, "project": {}, "gate": {}},
            "modules": {},
            "entries": [{"module": "character.Demo", "id": "x"}],
            "stale_entries": [{"id": "x"}],
            "qa_issues": ["edge"],
        }
        run_doctor_quiet(self.td, data, source="safe", offer_tip=False)
        self.assertEqual(self.entry.read_text(encoding="utf-8"), before_entry)
        self.assertEqual(self.modules.read_text(encoding="utf-8"), before_mod)
        self.assertEqual(self.entry.stat().st_mtime_ns, before_mtime)
        # still only profile artifacts
        profile_files = {p.name for p in (self.td / ".memory-art" / "_profile").iterdir()}
        self.assertIn("last_doctor.json", profile_files)
        self.assertTrue(self.entry.is_file())

    def test_strict_signals_fire_on_single_findings(self) -> None:
        from lifecycle import collect_doctor_summary

        # one orphan image under assets/
        orphan = self.td / "assets" / "loose.png"
        orphan.write_bytes(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
            b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        data = {
            "config": {"bootstrap": {"asset_roots": ["assets"]}, "project": {}, "gate": {}},
            "modules": {},
            "entries": [{"module": "character.Demo"}],
            "stale_entries": [{"id": "s1"}],
            "qa_issues": ["bad"],
        }
        summary = collect_doctor_summary(self.td, data)
        self.assertGreaterEqual(summary["orphans"], 1)
        self.assertTrue(summary["needs_attention"])
        joined = " ".join(summary["signals"])
        self.assertIn("孤儿", joined)
        self.assertIn("STALE", joined)
        self.assertIn("QA", joined)
        self.assertIn("缺specs", joined)

    def test_claim_preserves_prior_report_fields(self) -> None:
        from lifecycle import load_doctor_state, save_doctor_state, try_claim_lazy_doctor

        save_doctor_state(
            self.td,
            {
                "last_run_at": "",
                "status": "ok",
                "orphan_samples": ["assets/a.png"],
                "missing_specs": ["character.Demo"],
                "tip_line": "keep-me",
            },
        )
        self.assertTrue(try_claim_lazy_doctor(self.td, interval_hours=48))
        state = load_doctor_state(self.td)
        self.assertEqual(state.get("status"), "running")
        self.assertEqual(state.get("orphan_samples"), ["assets/a.png"])
        self.assertEqual(state.get("missing_specs"), ["character.Demo"])
        self.assertEqual(state.get("tip_line"), "keep-me")

    def test_tip_only_when_pending_and_budget(self) -> None:
        from lifecycle import consume_doctor_tip, save_doctor_state

        save_doctor_state(
            self.td,
            {
                "tip_pending": True,
                "needs_attention": True,
                "tip_line": "🩺 记忆医生：孤儿 3",
            },
        )
        with mock.patch("improve.try_consume_tip_budget", return_value=True):
            tip = consume_doctor_tip(self.td)
        self.assertEqual(tip, "🩺 记忆医生：孤儿 3")
        # second consume should be cleared
        with mock.patch("improve.try_consume_tip_budget", return_value=True):
            self.assertIsNone(consume_doctor_tip(self.td))

    def test_hook_spawns_when_due_and_stays_quiet(self) -> None:
        from lifecycle import maybe_lazy_doctor_on_hook, load_doctor_state

        with mock.patch("lifecycle.spawn_lazy_doctor", return_value=True) as sp:
            tip = maybe_lazy_doctor_on_hook(self.td, "pre-gen")
        self.assertIsNone(tip)
        sp.assert_called_once()
        state = load_doctor_state(self.td)
        self.assertEqual(state.get("status"), "running")

    def test_hook_skips_spawn_when_fresh(self) -> None:
        from lifecycle import _doctor_now_str, maybe_lazy_doctor_on_hook, save_doctor_state

        save_doctor_state(self.td, {"last_run_at": _doctor_now_str(), "status": "ok"})
        with mock.patch("lifecycle.spawn_lazy_doctor") as sp:
            maybe_lazy_doctor_on_hook(self.td, "pre-gen")
        sp.assert_not_called()

    def test_spawn_events_include_post_session_and_finish(self) -> None:
        from lifecycle import maybe_lazy_doctor_on_hook

        for event in ("post-asset", "post-tool", "session", "converge_finish"):
            with mock.patch("lifecycle.spawn_lazy_doctor", return_value=True) as sp:
                with mock.patch("lifecycle.try_claim_lazy_doctor", return_value=True):
                    maybe_lazy_doctor_on_hook(self.td, event)
            sp.assert_called_once()

    def test_unknown_event_only_consumes_tip(self) -> None:
        from lifecycle import maybe_lazy_doctor_on_hook

        with mock.patch("lifecycle.spawn_lazy_doctor") as sp:
            with mock.patch("lifecycle.try_claim_lazy_doctor") as claim:
                maybe_lazy_doctor_on_hook(self.td, "prompt")
        sp.assert_not_called()
        claim.assert_not_called()


class TestDoctorCliQuiet(unittest.TestCase):
    def test_doctor_quiet_cli_isolated(self) -> None:
        import shutil
        import subprocess
        import sys

        td = Path(tempfile.mkdtemp(prefix="pmem_doctor_cli_"))
        try:
            # Minimal mount so load_project works without touching repo profile
            mem = td / ".memory-art"
            (mem / "_profile").mkdir(parents=True)
            (mem / "entries").mkdir(parents=True)
            (td / "assets").mkdir(parents=True)
            (mem / "modules.yaml").write_text("modules: {}\n", encoding="utf-8")
            (mem / "library.json").write_text("[]\n", encoding="utf-8")
            proc = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "pmem_art.py"),
                    "--root",
                    str(td),
                    "doctor",
                    "--quiet",
                    "--source",
                    "unit",
                ],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual((proc.stdout or "").strip(), "")
            state_path = mem / "_profile" / "last_doctor.json"
            self.assertTrue(state_path.is_file())
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state.get("source"), "unit")
            self.assertEqual(state.get("status"), "ok")
        finally:
            shutil.rmtree(td, ignore_errors=True)

    def test_hook_agent_message_omits_doctor_dump(self) -> None:
        import io
        import shutil
        import sys
        from contextlib import redirect_stdout

        import pmem_art as pa
        from lifecycle import _doctor_now_str, save_doctor_state

        td = Path(tempfile.mkdtemp(prefix="pmem_doctor_hook_"))
        try:
            mem = td / ".memory-art"
            (mem / "_profile").mkdir(parents=True)
            (mem / "entries").mkdir(parents=True)
            (td / "assets").mkdir(parents=True)
            (mem / "modules.yaml").write_text("modules: {}\n", encoding="utf-8")
            (mem / "library.json").write_text("[]\n", encoding="utf-8")
            save_doctor_state(td, {"last_run_at": _doctor_now_str(), "status": "ok"})
            data = pa.load_project(td)
            old_stdin = sys.stdin
            sys.stdin = io.StringIO("{}")
            buf = io.StringIO()
            try:
                with redirect_stdout(buf):
                    pa.cmd_hook(td, data, "pre-gen")
            finally:
                sys.stdin = old_stdin
            out = json.loads(buf.getvalue())
            msg = out.get("agentMessage") or ""
            self.assertNotIn("lifecycle_mode", msg)
            self.assertNotIn("孤儿文件样本", msg)
            self.assertNotIn("Mode C 持续循环", msg)
            self.assertTrue(out.get("continue"))
        finally:
            shutil.rmtree(td, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
