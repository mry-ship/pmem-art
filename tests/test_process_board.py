"""Finish writes a clickable process board, including discussion drafts."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from skills_kit.converge import cmd_converge
from skills_kit.process_board import write_process_board


class ProcessBoardTests(unittest.TestCase):
    def test_board_lists_rounds_and_discussion_and_opens_images(self):
        td = Path(tempfile.mkdtemp())
        real = ROOT / "comparison" / "scale_01_night_city_high.jpg"
        layout = td / "layout.png"
        ident = td / "identity.png"
        img = td / "r1.jpg"
        shutil.copy2(real, layout)
        shutil.copy2(real, ident)
        shutil.copy2(real, img)
        sess = {
            "session_id": "board-demo",
            "goal": "圣诞箱上下配套",
            "ref_analysis": "图1锁机位，图2锁箱子。",
            "ref_image": str(ident),
            "default_reference_image_paths": [str(layout), str(ident)],
            "discussions": [{
                "round": 1,
                "prompt": "八件关系稿",
                "defects": "第3行合成说不通",
                "next_fix": "只改第3行",
            }],
            "rounds": [{
                "round": 1,
                "score": 9.11,
                "dims": "构图9.3/光影9.1/透视8.7/质感9.2/风格9.2",
                "image": str(img),
                "strengths": "上关下开",
                "defects": "两态角度还没对齐",
                "next_fix": "打开态转到同一侧角",
            }],
            "winner": {"round": 1, "score": 9.11, "defects": "两态角度还没对齐"},
        }
        index = write_process_board(td, sess, winner=sess["winner"])
        page = index.read_text(encoding="utf-8")
        self.assertIn("参考图分析", page)
        self.assertIn("图1锁机位", page)
        self.assertIn("<b>图1</b>", page)
        self.assertIn("<b>图2</b>", page)
        self.assertIn("论述第 1 稿", page)
        self.assertIn("第3行合成说不通", page)
        self.assertIn("第 1 轮 · 9.11", page)
        self.assertIn("构图9.3/光影9.1/透视8.7/质感9.2/风格9.2", page)
        self.assertIn('class="card win"', page)
        self.assertIn('class="lightbox"', page)
        self.assertIn("两态角度还没对齐", page)
        self.assertIn("未到 9.60", page)
        self.assertTrue(any((index.parent / "images").glob("r1.*")))

    def test_discuss_is_stored_on_the_session(self):
        td = Path(tempfile.mkdtemp())
        mem = td / ".memory-art" / "converge"
        mem.mkdir(parents=True)
        sess = {"session_id": "talk", "goal": "关系", "rounds": [], "status": "running"}
        (mem / "talk.json").write_text(json.dumps(sess), encoding="utf-8")
        rc = cmd_converge(
            td, {"config": {}, "entries": [], "modules": {}}, "discuss",
            session_id="talk", round_num=2, prompt="第二稿八行",
            defects="第5行剪影太像", next_fix="只改第5行",
        )
        self.assertEqual(rc, 0)
        saved = json.loads((mem / "talk.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["discussions"][0]["round"], 2)
        self.assertIn("第5行剪影太像", saved["discussions"][0]["defects"])

    def test_finish_writes_the_board_and_puts_the_path_in_the_report(self):
        td = Path(tempfile.mkdtemp())
        mem = td / ".memory-art" / "converge"
        mem.mkdir(parents=True)
        img = td / "round.jpg"
        shutil.copy2(ROOT / "comparison" / "scale_01_night_city_high.jpg", img)
        sess = {
            "session_id": "fin-board",
            "goal": "检查过程板",
            "module": "prop.Check",
            "scale": "medium",
            "accept_threshold": 9.6,
            "threshold": 9.6,
            "max_rounds": 4,
            "status": "running",
            "rounds": [{
                "round": 1,
                "score": 8.5,
                "dims": "构图8.5/光影8.5/透视8.5/质感8.5/风格8.5",
                "image": str(img),
                "judged": True,
                "passed": False,
                "strengths": "清楚",
                "defects": "角度偏了",
                "next_fix": "转正",
                "prompt": "x",
            }],
        }
        (mem / "fin-board.json").write_text(json.dumps(sess, ensure_ascii=False), encoding="utf-8")
        rc = cmd_converge(
            td, {"config": {}, "entries": [], "modules": {}}, "finish",
            session_id="fin-board", apply_memory=False, silent=True,
        )
        self.assertEqual(rc, 0)
        page = (td / ".memory-art" / "converge" / "boards" / "fin-board" / "index.html").read_text(encoding="utf-8")
        report = (mem / "fin-board_report.md").read_text(encoding="utf-8")
        self.assertIn("第 1 轮 · 8.50", page)
        self.assertIn("未到 9.60", page)
        self.assertIn("boards/fin-board/index.html", report)


if __name__ == "__main__":
    unittest.main()
