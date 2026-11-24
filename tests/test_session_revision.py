"""Same-session writers must not cover a newer revision."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from skills_kit.converge import _write_session_json  # noqa: E402
from skills_kit.session_lock import SessionRevisionConflict  # noqa: E402


class SessionRevisionTests(unittest.TestCase):
    def test_stale_writer_does_not_drop_the_newer_round(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sf = Path(tmp) / "same.json"
            _write_session_json(sf, {"session_id": "same", "status": "running", "rounds": []})
            first = json.loads(sf.read_text(encoding="utf-8"))
            second = json.loads(sf.read_text(encoding="utf-8"))
            first["rounds"] = [{"round": 1, "image": "r1.png"}]
            second["goal"] = "被盖掉的目标"
            _write_session_json(sf, first)
            with self.assertRaises(SessionRevisionConflict):
                _write_session_json(sf, second)
            disk = json.loads(sf.read_text(encoding="utf-8"))
            self.assertEqual(disk["rounds"][0]["image"], "r1.png")
            self.assertNotIn("goal", disk)
            self.assertGreater(int(disk["_rev"]), int(second["_rev"]))

    def test_replace_session_may_open_over_the_same_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sf = Path(tmp) / "reopen.json"
            _write_session_json(sf, {"session_id": "reopen", "status": "continue", "rounds": [{"round": 1}]})
            fresh = {"session_id": "reopen", "status": "running", "rounds": []}
            _write_session_json(sf, fresh, replace_session=True)
            disk = json.loads(sf.read_text(encoding="utf-8"))
            self.assertEqual(disk["rounds"], [])
            self.assertEqual(disk["status"], "running")
            self.assertGreaterEqual(int(disk["_rev"]), 2)

    def test_same_object_can_write_twice(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sf = Path(tmp) / "twice.json"
            sess = {"session_id": "twice", "status": "running"}
            _write_session_json(sf, sess)
            sess["status"] = "continue"
            _write_session_json(sf, sess)
            disk = json.loads(sf.read_text(encoding="utf-8"))
            self.assertEqual(disk["status"], "continue")
            self.assertEqual(int(disk["_rev"]), 2)
            self.assertTrue(sf.with_name(sf.name + ".lock").is_file() or os.path.exists(sf.with_name(sf.name + ".lock")))

    def test_stale_contract_does_not_cover_a_newer_contract(self) -> None:
        """重读最新会话再贴旧合同，不能靠新的 _rev 把新合同盖掉。"""
        from skills_kit.understanding_contract import save_session_contract

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sf = root / ".memory-art" / "converge" / "c1.json"
            sf.parent.mkdir(parents=True)
            _write_session_json(
                sf,
                {
                    "session_id": "c1",
                    "status": "running",
                    "rounds": [],
                    "understanding_contract": {"grid": {"keep": ["原合同"]}},
                },
            )
            base = json.loads(sf.read_text(encoding="utf-8"))
            base_rev = int(base["_rev"])
            save_session_contract(
                root,
                "c1",
                {"grid": {"keep": ["B 的新合同"]}},
                base_rev=base_rev,
            )
            newer = json.loads(sf.read_text(encoding="utf-8"))
            newer["rounds"] = [{"round": 1, "image": "r1.png"}]
            _write_session_json(sf, newer)
            held_rev = int(json.loads(sf.read_text(encoding="utf-8"))["_rev"])
            with self.assertRaises(SessionRevisionConflict):
                save_session_contract(
                    root,
                    "c1",
                    {"grid": {"keep": ["A 的旧草稿"]}},
                    base_rev=base_rev,
                )
            disk = json.loads(sf.read_text(encoding="utf-8"))
            self.assertEqual(disk["understanding_contract"]["grid"]["keep"], ["B 的新合同"])
            self.assertEqual(disk["rounds"][0]["image"], "r1.png")
            self.assertEqual(int(disk["_rev"]), held_rev)

    def test_contract_save_matches_the_rev_from_the_read(self) -> None:
        from skills_kit.understanding_contract import save_session_contract

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sf = root / ".memory-art" / "converge" / "c2.json"
            sf.parent.mkdir(parents=True)
            _write_session_json(
                sf,
                {
                    "session_id": "c2",
                    "status": "running",
                    "rounds": [{"round": 1, "image": "keep.png"}],
                    "understanding_contract": {"grid": {"keep": ["原合同"]}},
                },
            )
            base_rev = int(json.loads(sf.read_text(encoding="utf-8"))["_rev"])
            save_session_contract(
                root,
                "c2",
                {"grid": {"keep": ["这一次的合同"]}},
                base_rev=base_rev,
            )
            disk = json.loads(sf.read_text(encoding="utf-8"))
            self.assertEqual(disk["understanding_contract"]["grid"]["keep"], ["这一次的合同"])
            self.assertEqual(disk["rounds"][0]["image"], "keep.png")
            self.assertEqual(int(disk["_rev"]), base_rev + 1)


if __name__ == "__main__":
    unittest.main()
