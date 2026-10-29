from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from skills_kit.converge_loop import loop_followup, mark_active_session  # noqa: E402


class TestConvergeLoop(unittest.TestCase):
    def _write(self, td: Path, sid: str, sess: dict) -> None:
        folder = td / ".memory-art" / "converge"
        folder.mkdir(parents=True)
        (folder / f"{sid}.json").write_text(json.dumps(sess, ensure_ascii=False), encoding="utf-8")
        mark_active_session(td, sid)

    def test_pending_judge_blocks_stop(self) -> None:
        td = Path(tempfile.mkdtemp())
        self._write(td, "cell", {
            "status": "generated_pending_judge",
            "accept_threshold": 9.6,
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
            "accept_threshold": 9.6,
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
            "accept_threshold": 9.6,
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


if __name__ == "__main__":
    unittest.main()
