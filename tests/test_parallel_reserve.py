"""Cross-process slot claims and prepare rollback."""
from __future__ import annotations

import json
import multiprocessing
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("PMEM_ART_ALLOW_GATE_SKIP", "1")

from skills_kit.parallel_slots import (  # noqa: E402
    RESERVE_TTL_SEC,
    assert_can_start,
    list_active_sessions,
    purge_expired_reservations,
    release_slot,
    reserve_slot,
)


def _race_reserve(root_s: str, sid: str, barrier: multiprocessing.Barrier, q: multiprocessing.Queue) -> None:
    project = Path(__file__).resolve().parents[1]
    if str(project) not in sys.path:
        sys.path.insert(0, str(project))
    barrier.wait(15)
    from skills_kit.parallel_slots import reserve_slot as claim

    ok, _msg = claim(
        Path(root_s),
        {"config": {"agent": {"max_parallel": 1}}},
        session_id=sid,
    )
    q.put(bool(ok))


class ReserveRaceTests(unittest.TestCase):
    def test_two_processes_cannot_both_take_the_last_slot(self) -> None:
        ctx = multiprocessing.get_context("spawn")
        with tempfile.TemporaryDirectory() as tmp:
            barrier = ctx.Barrier(2)
            queue: multiprocessing.Queue = ctx.Queue()
            procs = [
                ctx.Process(target=_race_reserve, args=(tmp, sid, barrier, queue))
                for sid in ("slot-a", "slot-b")
            ]
            for proc in procs:
                proc.start()
            for proc in procs:
                proc.join(20)
                self.assertFalse(proc.is_alive())
                self.assertEqual(proc.exitcode, 0, proc.exitcode)
            got = sorted(bool(queue.get(timeout=5)) for _ in range(2))
            self.assertEqual(got, [False, True])
            left = list((Path(tmp) / ".memory-art" / "converge" / "_slots").glob("*.reserve.json"))
            self.assertEqual(len(left), 1)

    def test_expired_reservation_does_not_hold_a_slot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = {"config": {"agent": {"max_parallel": 1}}}
            ok, _ = reserve_slot(root, data, session_id="old-claim")
            self.assertTrue(ok)
            path = next((root / ".memory-art" / "converge" / "_slots").glob("*.reserve.json"))
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["reserved_at"] = time.time() - RESERVE_TTL_SEC - 5
            path.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(purge_expired_reservations(root), 1)
            ok2, _ = assert_can_start(root, data, session_id="fresh")
            self.assertTrue(ok2)

    def test_release_lets_the_next_start_through(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = {"config": {"agent": {"max_parallel": 1}}}
            self.assertTrue(reserve_slot(root, data, session_id="held")[0])
            self.assertFalse(reserve_slot(root, data, session_id="other")[0])
            release_slot(root, "held")
            self.assertTrue(reserve_slot(root, data, session_id="other")[0])


def _prepare_kwargs(root: Path, session_id: str) -> dict:
    from skills_kit.reasonableness_gate import default_checklist_template

    revised = (
        "青瓷小猫蹲坐捧茶盏，爪与盏接触清楚；背景最多一扇窗；"
        "竖构图无字；一眼失败是多爪或茶盏漂浮。"
    )
    return dict(
        root=root,
        data={"config": {"agent": {"max_parallel": 2}, "converge": {}}, "modules": {}, "entries": []},
        session_id=session_id,
        goal="青瓷小猫蹲坐捧茶盏",
        module="brand.WorldStyle",
        scale="medium",
        skip_route_gate=True,
        skip_reason="unit test prepare abort",
        reason_skill="ordinary",
        reason_draft="青瓷小猫蹲坐捧茶盏",
        revised=revised,
        checklist=default_checklist_template("ordinary"),
    )


class PrepareAbortTests(unittest.TestCase):
    def _session(self, root: Path, session_id: str) -> dict:
        path = root / ".memory-art" / "converge" / f"{session_id}.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def _audit(self, root: Path, session_id: str) -> str:
        folder = root / ".memory-art" / "converge" / "_prepare_audit"
        return "\n".join(path.read_text(encoding="utf-8") for path in folder.glob("*.jsonl"))

    def test_each_stage_failure_releases_the_slot_and_keeps_one_session(self) -> None:
        from skills_kit.converge import cmd_converge, cmd_converge_prepare

        stages = (
            ("skills_kit.understanding_contract.cmd_contract", "contract"),
            ("skills_kit.reasonableness_gate.cmd_reasonableness_at_root", "reasonableness"),
        )
        for target, stage in stages:
            with self.subTest(stage=stage):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    kwargs = _prepare_kwargs(root, "prep-abort")
                    with patch(target, return_value=1):
                        rc = cmd_converge_prepare(**kwargs)
                    self.assertEqual(rc, 1)
                    sess = self._session(root, "prep-abort")
                    self.assertEqual(sess["status"], "prepare_aborted")
                    self.assertEqual(sess["prepare_failure"]["stage"], stage)
                    self.assertEqual(list_active_sessions(root, kwargs["data"]), [])
                    self.assertIn(stage, self._audit(root, "prep-abort"))
                    files = [
                        p.name
                        for p in (root / ".memory-art" / "converge").glob("*.json")
                        if not p.name.startswith("_")
                    ]
                    self.assertEqual(files, ["prep-abort.json"])

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            kwargs = _prepare_kwargs(root, "prep-emit")
            real = cmd_converge

            def _stop_generate(root_arg, data, action, **kw):
                if action == "generate":
                    return 1
                return real(root_arg, data, action, **kw)

            with patch("skills_kit.converge.cmd_converge", side_effect=_stop_generate):
                rc = cmd_converge_prepare(**kwargs)
            self.assertEqual(rc, 1)
            sess = self._session(root, "prep-emit")
            self.assertEqual(sess["status"], "prepare_aborted")
            self.assertEqual(sess["prepare_failure"]["stage"], "emit-prompt")
            self.assertEqual(list_active_sessions(root, kwargs["data"]), [])
            self.assertIn("emit-prompt", self._audit(root, "prep-emit"))

    def test_rerun_prepare_overwrites_the_aborted_session(self) -> None:
        from skills_kit.converge import cmd_converge_prepare

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            kwargs = _prepare_kwargs(root, "prep-again")
            with patch("skills_kit.understanding_contract.cmd_contract", return_value=1):
                self.assertEqual(cmd_converge_prepare(**kwargs), 1)
            self.assertEqual(self._session(root, "prep-again")["status"], "prepare_aborted")
            rc = cmd_converge_prepare(**kwargs)
            self.assertEqual(rc, 0, "second prepare should finish")
            sess = self._session(root, "prep-again")
            self.assertNotEqual(sess["status"], "prepare_aborted")
            names = [
                p.name
                for p in (root / ".memory-art" / "converge").glob("*.json")
                if not p.name.startswith("_")
            ]
            self.assertEqual(names, ["prep-again.json"])
            self.assertEqual(len(list_active_sessions(root, kwargs["data"])), 1)

    def test_abort_does_not_drop_a_session_that_already_has_a_plate(self) -> None:
        from skills_kit.converge import abort_prepare_session

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / ".memory-art" / "converge"
            folder.mkdir(parents=True)
            (folder / "drawn.json").write_text(
                json.dumps(
                    {
                        "session_id": "drawn",
                        "status": "continue",
                        "rounds": [{"round": 1, "image": "r1.png"}],
                    }
                ),
                encoding="utf-8",
            )
            abort_prepare_session(root, "drawn", stage="emit-prompt", rc=1)
            sess = json.loads((folder / "drawn.json").read_text(encoding="utf-8"))
            self.assertEqual(sess["status"], "continue")
            self.assertEqual(len(list_active_sessions(root, {"config": {}})), 1)

    def test_abort_leaves_a_newer_same_id_claim_in_place(self) -> None:
        from skills_kit.converge import abort_prepare_session
        from skills_kit.parallel_slots import list_reservations

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / ".memory-art" / "converge"
            folder.mkdir(parents=True)
            (folder / "same.json").write_text(
                json.dumps(
                    {
                        "session_id": "same",
                        "status": "running",
                        "started_at": "new-start",
                        "slot_token": "newer-token",
                        "rounds": [],
                    }
                ),
                encoding="utf-8",
            )
            self.assertTrue(
                reserve_slot(
                    root,
                    {"config": {"agent": {"max_parallel": 1}}},
                    session_id="same",
                    token="newer-token",
                )[0]
            )
            abort_prepare_session(
                root,
                "same",
                stage="contract",
                rc=1,
                started_at="old-start",
            )
            sess = json.loads((folder / "same.json").read_text(encoding="utf-8"))
            self.assertEqual(sess["status"], "running")
            self.assertEqual(
                [item["session_id"] for item in list_reservations(root)],
                ["same"],
            )
            release_slot(root, "same", token="old-token")
            self.assertEqual(len(list_reservations(root)), 1)
            release_slot(root, "same", token="newer-token")
            self.assertEqual(list_reservations(root), [])

    def test_abort_clears_only_the_matching_active_pointer(self) -> None:
        from skills_kit.converge import abort_prepare_session
        from skills_kit.converge_loop import active_session_id, mark_active_session

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / ".memory-art" / "converge"
            folder.mkdir(parents=True)
            (folder / "prep.json").write_text(
                json.dumps(
                    {
                        "session_id": "prep",
                        "status": "running",
                        "started_at": "this-start",
                        "slot_token": "",
                        "rounds": [],
                    }
                ),
                encoding="utf-8",
            )
            mark_active_session(root, "prep", conversation_id="conv-a", started_at="this-start")
            abort_prepare_session(root, "prep", stage="contract", rc=1, started_at="this-start")
            self.assertEqual(active_session_id(root), "")
            (folder / "prep.json").write_text(
                json.dumps(
                    {
                        "session_id": "prep",
                        "status": "running",
                        "started_at": "newer-start",
                        "rounds": [],
                    }
                ),
                encoding="utf-8",
            )
            mark_active_session(root, "prep", conversation_id="conv-b", started_at="newer-start")
            abort_prepare_session(root, "prep", stage="contract", rc=1, started_at="this-start")
            self.assertEqual(active_session_id(root), "prep")
            self.assertEqual(
                json.loads((folder / "prep.json").read_text(encoding="utf-8"))["status"],
                "running",
            )


if __name__ == "__main__":
    unittest.main()
