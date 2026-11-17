"""converge generate --emit-prompt: final prompt without image / round register."""
from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("PMEM_ART_ALLOW_GATE_SKIP", "1")

from skills_kit.converge import cmd_converge, _session_file  # noqa: E402
from skills_kit.final_prompt_gate import final_prompt_sha1  # noqa: E402
from skills_kit.reasonableness_gate import (  # noqa: E402
    apply_review_to_session,
    default_checklist_template,
    review_reasonableness,
)


def _noisy_png(path: Path, size: int = 128) -> Path:
    from PIL import Image

    img = Image.new("RGB", (size, size))
    px = img.load()
    for y in range(size):
        for x in range(size):
            px[x, y] = ((x * 13 + y * 7) % 256, (x * 3) % 256, (y * 11) % 256)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    return path


def _seed_session(root: Path, sid: str = "emit-test") -> str:
    data: dict = {"config": {"converge": {}}, "modules": {}, "entries": []}
    rc = cmd_converge(
        root,
        data,
        "start",
        session_id=sid,
        goal="青瓷小猫蹲坐捧茶盏",
        module="brand.WorldStyle",
        scale="medium",
        skip_route_gate=True,
        skip_reason="unit test emit-prompt",
    )
    assert rc == 0, "start failed"
    sf = _session_file(root, sid)
    sess = json.loads(sf.read_text(encoding="utf-8"))
    rev = (
        "青瓷小猫蹲坐捧茶盏，爪与盏接触清楚；背景最多一扇窗；"
        "竖构图无字；一眼失败是多爪或茶盏漂浮。"
    )
    review = review_reasonableness(
        skill="ordinary",
        draft="青瓷小猫",
        revised=rev,
        checklist_text=default_checklist_template("ordinary"),
    )
    assert review["passed"], review.get("issues")
    sess = apply_review_to_session(sess, review)
    sf.write_text(json.dumps(sess, ensure_ascii=False, indent=2), encoding="utf-8")
    return sid


class TestConvergeEmitPrompt(unittest.TestCase):
    def test_emit_without_image_prints_final_prompt_no_round(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data: dict = {"config": {"converge": {}}, "modules": {}, "entries": []}
            sid = _seed_session(root)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = cmd_converge(
                    root,
                    data,
                    "generate",
                    session_id=sid,
                    round_num=1,
                    emit_prompt=True,
                    skip_route_gate=True,
                    skip_reason="unit test emit-prompt",
                    apply_memory=False,
                )
            out = buf.getvalue()
            self.assertEqual(rc, 0, out)
            self.assertIn("FINAL_PROMPT_SHA1=", out)
            self.assertIn("最终 Prompt（出图须用这句）", out)
            self.assertIn("emit-prompt", out)
            sess = json.loads(_session_file(root, sid).read_text(encoding="utf-8"))
            self.assertEqual(sess.get("rounds") or [], [])
            self.assertTrue(str(sess.get("pending_final_prompt") or "").strip())
            self.assertEqual(int(sess.get("pending_final_prompt_round") or 0), 1)
            self.assertEqual(
                sess.get("pending_final_prompt_sha1"),
                final_prompt_sha1(sess["pending_final_prompt"]),
            )
            self.assertEqual(sess.get("ActionRequired"), "GENERATE_IMAGE_R1")

    def test_emit_with_image_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data: dict = {"config": {"converge": {}}, "modules": {}, "entries": []}
            sid = _seed_session(root)
            img = _noisy_png(root / "x.png")
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = cmd_converge(
                    root,
                    data,
                    "generate",
                    session_id=sid,
                    round_num=1,
                    emit_prompt=True,
                    image=str(img),
                    skip_route_gate=True,
                    skip_reason="unit test emit-prompt",
                    apply_memory=False,
                )
            self.assertEqual(rc, 1, buf.getvalue())
            self.assertIn("禁止与", buf.getvalue())

    def test_register_after_emit_reuses_pending_sha(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data: dict = {"config": {"converge": {}}, "modules": {}, "entries": []}
            sid = _seed_session(root)
            emit_buf = io.StringIO()
            with redirect_stdout(emit_buf):
                rc_emit = cmd_converge(
                    root,
                    data,
                    "generate",
                    session_id=sid,
                    round_num=1,
                    emit_prompt=True,
                    skip_route_gate=True,
                    skip_reason="unit test emit-prompt",
                    apply_memory=False,
                )
            self.assertEqual(rc_emit, 0, emit_buf.getvalue())
            sess = json.loads(_session_file(root, sid).read_text(encoding="utf-8"))
            pending_sha = sess.get("pending_final_prompt_sha1")
            pending_text = sess.get("pending_final_prompt")
            img = _noisy_png(root / "out.png")
            reg_buf = io.StringIO()
            with redirect_stdout(reg_buf):
                rc_reg = cmd_converge(
                    root,
                    data,
                    "generate",
                    session_id=sid,
                    round_num=1,
                    image=str(img),
                    prompt="",  # reuse pending
                    skip_route_gate=True,
                    skip_reason="unit test emit-prompt",
                    apply_memory=False,
                )
            out = reg_buf.getvalue()
            self.assertEqual(rc_reg, 0, out)
            sess2 = json.loads(_session_file(root, sid).read_text(encoding="utf-8"))
            rounds = sess2.get("rounds") or []
            self.assertEqual(len(rounds), 1)
            self.assertEqual(rounds[0].get("final_prompt_sha1"), pending_sha)
            self.assertEqual(rounds[0].get("prompt"), pending_text)
            self.assertNotIn("pending_final_prompt", sess2)
            self.assertIn("FINAL_PROMPT_SHA1=", out)


if __name__ == "__main__":
    unittest.main()
