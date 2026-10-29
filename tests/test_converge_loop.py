from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from skills_kit.converge_loop import (  # noqa: E402
    active_owner_conversation_id,
    claim_active_conversation,
    followup_allowed_for_conversation,
    loop_followup,
    mark_active_session,
)
import pmem_art as pa  # noqa: E402


class TestConvergeLoop(unittest.TestCase):
    def _write(self, td: Path, sid: str, sess: dict, conversation_id: str = "") -> None:
        folder = td / ".memory-art" / "converge"
        folder.mkdir(parents=True)
        (folder / f"{sid}.json").write_text(json.dumps(sess, ensure_ascii=False), encoding="utf-8")
        mark_active_session(td, sid, conversation_id=conversation_id)

    def test_pending_judge_blocks_stop(self) -> None:
        td = Path(tempfile.mkdtemp())
        self._write(td, "cell", {
            "status": "generated_pending_judge",
            "accept_threshold": 9.5,
            "max_rounds": 4,
            "rounds": [{"round": 1, "image": "r1.jpg", "judged": False}],
        })
        hit = loop_followup(td)
        self.assertEqual(hit["reason"], "pending_judge")
        self.assertIn("judge", hit["message"])

    def test_under_threshold_needs_next_round(self) -> None:
        td = Path(tempfile.mkdtemp())
        self._write(td, "cell", {
            "status": "continue",
            "accept_threshold": 9.5,
            "max_rounds": 4,
            "rounds": [{"round": 1, "image": "r1.jpg", "judged": True, "score": 8.3}],
        })
        hit = loop_followup(td)
        self.assertEqual(hit["reason"], "need_next_round")
        self.assertIn("第 2 轮", hit["message"])

    def test_four_rounds_asks_finish(self) -> None:
        td = Path(tempfile.mkdtemp())
        self._write(td, "cell", {
            "status": "max_rounds_reached",
            "accept_threshold": 9.5,
            "max_rounds": 4,
            "rounds": [
                {"round": i, "image": f"r{i}.jpg", "judged": True, "score": 8.5}
                for i in range(1, 5)
            ],
        })
        hit = loop_followup(td)
        self.assertEqual(hit["reason"], "need_finish")

    def test_idle_start_does_not_block(self) -> None:
        td = Path(tempfile.mkdtemp())
        self._write(td, "cell", {"status": "running", "rounds": []})
        self.assertIsNone(loop_followup(td))

    def test_owner_claim_and_mismatch(self) -> None:
        td = Path(tempfile.mkdtemp())
        self._write(td, "cell", {
            "status": "generated_pending_judge",
            "rounds": [{"round": 1, "image": "r1.jpg", "judged": False}],
        })
        self.assertEqual(claim_active_conversation(td, "conv-draw"), "conv-draw")
        self.assertEqual(active_owner_conversation_id(td), "conv-draw")
        self.assertTrue(followup_allowed_for_conversation(td, "conv-draw"))
        self.assertFalse(followup_allowed_for_conversation(td, "conv-other"))
        # 错窗不能把归属抢走
        self.assertEqual(active_owner_conversation_id(td), "conv-draw")

    def test_new_session_clears_stale_owner(self) -> None:
        td = Path(tempfile.mkdtemp())
        folder = td / ".memory-art" / "converge"
        folder.mkdir(parents=True)
        mark_active_session(td, "old", conversation_id="conv-a")
        mark_active_session(td, "new")
        self.assertEqual(active_owner_conversation_id(td), "")
        self.assertEqual(claim_active_conversation(td, "conv-b"), "conv-b")

    def test_latest_to_named_clears_stale_owner(self) -> None:
        td = Path(tempfile.mkdtemp())
        (td / ".memory-art" / "converge").mkdir(parents=True)
        mark_active_session(td, "latest", conversation_id="conv-a")
        mark_active_session(td, "named-cell")
        self.assertEqual(active_owner_conversation_id(td), "")

    def test_stop_does_not_claim_when_owner_empty(self) -> None:
        td = Path(tempfile.mkdtemp())
        self._write(td, "cell", {
            "status": "generated_pending_judge",
            "accept_threshold": 9.5,
            "max_rounds": 4,
            "rounds": [{"round": 1, "image": "r1.jpg", "judged": False}],
        })
        self.assertEqual(active_owner_conversation_id(td), "")
        self.assertFalse(followup_allowed_for_conversation(td, "conv-bystander"))
        self.assertEqual(active_owner_conversation_id(td), "")
        # 真出图窗仍可认领
        self.assertEqual(claim_active_conversation(td, "conv-draw"), "conv-draw")
        self.assertTrue(followup_allowed_for_conversation(td, "conv-draw"))
        self.assertFalse(followup_allowed_for_conversation(td, "conv-bystander"))

    def test_stop_hook_no_conversation_id_still_followup(self) -> None:
        td = Path(tempfile.mkdtemp())
        self._write(
            td,
            "cell",
            {
                "status": "generated_pending_judge",
                "accept_threshold": 9.5,
                "max_rounds": 4,
                "rounds": [{"round": 1, "image": "r1.jpg", "judged": False}],
            },
            conversation_id="conv-draw",
        )
        payload = json.dumps({"status": "completed", "loop_count": 0})
        buf = io.StringIO()
        with mock.patch("sys.stdin", io.StringIO(payload)), redirect_stdout(buf):
            rc = pa.cmd_hook(td, {"entries": []}, "stop")
        self.assertEqual(rc, 0)
        out = json.loads(buf.getvalue())
        self.assertIn("还没审图", str(out.get("followup_message") or ""))

    def test_pre_gen_generate_image_claims_owner(self) -> None:
        td = Path(tempfile.mkdtemp())
        self._write(td, "cell", {
            "status": "running",
            "module": "character.SunlitGirl",
            "goal": "变体",
            "rounds": [],
        })
        payload = json.dumps({
            "conversation_id": "conv-draw",
            "tool_name": "GenerateImage",
            "tool_input": {"description": "girl smile", "filename": "r1.jpg"},
        })
        buf = io.StringIO()
        with mock.patch("sys.stdin", io.StringIO(payload)), redirect_stdout(buf):
            rc = pa.cmd_hook(td, {"entries": []}, "pre-gen")
        self.assertEqual(rc, 0)
        self.assertEqual(active_owner_conversation_id(td), "conv-draw")

    def test_pre_gen_edit_heuristic_does_not_claim(self) -> None:
        td = Path(tempfile.mkdtemp())
        self._write(td, "cell", {"status": "running", "rounds": []})
        payload = json.dumps({
            "conversation_id": "conv-other",
            "tool_name": "Edit",
            "tool_input": {
                "description": "looks like image args",
                "filename": "r1.jpg",
                "aspect_ratio": "1:1",
            },
        })
        buf = io.StringIO()
        with mock.patch("sys.stdin", io.StringIO(payload)), redirect_stdout(buf):
            rc = pa.cmd_hook(td, {"entries": []}, "pre-gen")
        self.assertEqual(rc, 0)
        self.assertEqual(active_owner_conversation_id(td), "")

    def test_pre_tool_generate_image_does_not_claim(self) -> None:
        td = Path(tempfile.mkdtemp())
        self._write(td, "cell", {"status": "running", "rounds": []})
        payload = json.dumps({
            "conversation_id": "conv-draw",
            "tool_name": "GenerateImage",
            "tool_input": {"description": "girl", "filename": "r1.jpg"},
        })
        buf = io.StringIO()
        with mock.patch("sys.stdin", io.StringIO(payload)), redirect_stdout(buf):
            rc = pa.cmd_hook(td, {"entries": []}, "pre-tool")
        self.assertEqual(rc, 0)
        self.assertEqual(active_owner_conversation_id(td), "")

    def test_stop_with_only_session_id_still_followup(self) -> None:
        """Host session_id must not be treated as conversation_id (清单4)."""
        td = Path(tempfile.mkdtemp())
        self._write(
            td,
            "cell",
            {
                "status": "generated_pending_judge",
                "accept_threshold": 9.5,
                "max_rounds": 4,
                "rounds": [{"round": 1, "image": "r1.jpg", "judged": False}],
            },
            conversation_id="conv-draw",
        )
        payload = json.dumps({
            "session_id": "host-session-not-composer",
            "status": "completed",
            "loop_count": 0,
        })
        buf = io.StringIO()
        with mock.patch("sys.stdin", io.StringIO(payload)), redirect_stdout(buf):
            rc = pa.cmd_hook(td, {"entries": []}, "stop")
        self.assertEqual(rc, 0)
        out = json.loads(buf.getvalue())
        self.assertIn("还没审图", str(out.get("followup_message") or ""))

    def test_pre_gen_write_does_not_claim_owner(self) -> None:
        td = Path(tempfile.mkdtemp())
        self._write(td, "cell", {
            "status": "running",
            "module": "character.SunlitGirl",
            "goal": "变体",
            "rounds": [],
        })
        payload = json.dumps({
            "conversation_id": "conv-other",
            "tool_name": "Write",
            "tool_input": {"path": "README.md", "contents": "x"},
        })
        buf = io.StringIO()
        with mock.patch("sys.stdin", io.StringIO(payload)), redirect_stdout(buf):
            rc = pa.cmd_hook(td, {"entries": []}, "pre-gen")
        self.assertEqual(rc, 0)
        self.assertEqual(active_owner_conversation_id(td), "")

    def test_stop_hook_empty_owner_does_not_write_owner(self) -> None:
        td = Path(tempfile.mkdtemp())
        self._write(td, "cell", {
            "status": "generated_pending_judge",
            "accept_threshold": 9.5,
            "max_rounds": 4,
            "rounds": [{"round": 1, "image": "r1.jpg", "judged": False}],
        })
        payload = json.dumps({
            "conversation_id": "conv-bystander",
            "status": "completed",
            "loop_count": 0,
        })
        buf = io.StringIO()
        with mock.patch("sys.stdin", io.StringIO(payload)), redirect_stdout(buf):
            rc = pa.cmd_hook(td, {"entries": []}, "stop")
        self.assertEqual(rc, 0)
        self.assertEqual(active_owner_conversation_id(td), "")
        out = json.loads(buf.getvalue())
        # owner 空：Cursor 窗不催办、不写入归属（等 GenerateImage 认领）
        self.assertFalse(out.get("followup_message"))
        self.assertNotIn("还没审图", str(out.get("agentMessage") or ""))

    def test_stop_hook_does_not_hijack_other_conversation(self) -> None:
        td = Path(tempfile.mkdtemp())
        self._write(
            td,
            "cell",
            {
                "status": "generated_pending_judge",
                "accept_threshold": 9.5,
                "max_rounds": 4,
                "rounds": [{"round": 1, "image": "r1.jpg", "judged": False}],
            },
            conversation_id="conv-draw",
        )
        payload = json.dumps({
            "conversation_id": "conv-other",
            "status": "completed",
            "loop_count": 0,
        })
        buf = io.StringIO()
        with mock.patch("sys.stdin", io.StringIO(payload)), redirect_stdout(buf):
            rc = pa.cmd_hook(td, {"entries": []}, "stop")
        self.assertEqual(rc, 0)
        out = json.loads(buf.getvalue())
        self.assertFalse(out.get("followup_message"))
        self.assertNotIn("还没审图", str(out.get("agentMessage") or ""))
        self.assertTrue(out.get("continue"))

    def test_stop_hook_followup_only_for_owner(self) -> None:
        td = Path(tempfile.mkdtemp())
        self._write(
            td,
            "cell",
            {
                "status": "generated_pending_judge",
                "accept_threshold": 9.5,
                "max_rounds": 4,
                "rounds": [{"round": 1, "image": "r1.jpg", "judged": False}],
            },
            conversation_id="conv-draw",
        )
        payload = json.dumps({
            "conversation_id": "conv-draw",
            "status": "completed",
            "loop_count": 0,
        })
        buf = io.StringIO()
        with mock.patch("sys.stdin", io.StringIO(payload)), redirect_stdout(buf):
            rc = pa.cmd_hook(td, {"entries": []}, "stop")
        self.assertEqual(rc, 0)
        out = json.loads(buf.getvalue())
        self.assertIn("还没审图", str(out.get("followup_message") or ""))
        self.assertFalse(out.get("continue"))


if __name__ == "__main__":
    unittest.main()
