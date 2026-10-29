"""Skill runs must auto-read pmem-art memory; Warm-Start is not a hand-paste step."""
from __future__ import annotations

import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from improve import WARM_START_MARK, merge_warm_start_prompt
from pmem_art import cmd_hook, image_gen_arg_view, parse_hook_payload
from skills_kit.converge import cmd_converge
from skills_kit.converge_loop import mark_active_session
from skills_kit.skill_specs import SKILL_SPECS


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


def _data() -> dict:
    return {
        "config": {},
        "modules": {
            "prop.Candy": {"status": "active"},
            "brand.WorldStyle": {"status": "active"},
            "ui.HUD": {"status": "active"},
        },
        "entries": [
            {
                "id": "REDLINE1",
                "kind": "style_redline",
                "module": "prop.Candy",
                "status": "active",
                "summary": "禁止把蜜桃糖焊进蛋糕",
            }
        ],
    }


def _project(td: Path) -> dict:
    mem = td / ".memory-art"
    (mem / "entries").mkdir(parents=True)
    (mem / "_profile").mkdir(parents=True)
    (mem / "config.yaml").write_text("project:\n  name: recall-test\n", encoding="utf-8")
    (mem / "modules.yaml").write_text(
        "modules:\n"
        "  prop.Candy:\n"
        "    status: active\n"
        "  brand.WorldStyle:\n"
        "    status: active\n"
        "  ui.HUD:\n"
        "    status: active\n",
        encoding="utf-8",
    )
    return _data()


class TestMergeWarmStart(unittest.TestCase):
    def test_prepends_once(self) -> None:
        pack = {"prompt_block": f"{WARM_START_MARK}】\n- 红线: 禁止霓虹"}
        once = merge_warm_start_prompt("a candy bottle on white", pack)
        self.assertTrue(once.startswith(WARM_START_MARK))
        self.assertIn("a candy bottle on white", once)
        self.assertEqual(once, merge_warm_start_prompt(once, pack))

    def test_empty_block_passthrough(self) -> None:
        self.assertEqual(merge_warm_start_prompt("keep", {}), "keep")
        self.assertEqual(merge_warm_start_prompt("keep", None), "keep")


class TestInferModule(unittest.TestCase):
    def test_candy_merge_hits_prop_not_brand(self) -> None:
        from feedback import infer_module_from_text

        data = _data()
        self.assertEqual(infer_module_from_text("合成梯糖果药瓶", data), "prop.Candy")
        self.assertEqual(infer_module_from_text("peach candy merge ladder", data), "prop.Candy")

    def test_ui_still_ui(self) -> None:
        from feedback import infer_module_from_text

        self.assertEqual(infer_module_from_text("主菜单 HUD 九宫格弹窗", _data()), "ui.HUD")


class TestHookPayload(unittest.TestCase):
    def test_cursor_tool_name_and_tool_input(self) -> None:
        tool, args, msg = parse_hook_payload(
            {
                "tool_name": "GenerateImage",
                "tool_input": {"description": "peach candy icon", "aspect_ratio": "1:1"},
                "user_message": "画糖果",
            }
        )
        self.assertEqual(tool, "GenerateImage")
        self.assertEqual(args["description"], "peach candy icon")
        self.assertEqual(msg, "画糖果")
        kind, view = image_gen_arg_view(tool, args)
        self.assertEqual(kind, "flat")
        self.assertEqual(view["description"], "peach candy icon")

    def test_nested_call_dynamic_tool(self) -> None:
        kind, view = image_gen_arg_view(
            "CallDynamicTool",
            {
                "namespace": "cursor",
                "toolName": "GenerateImage",
                "arguments": {"description": "inner prompt", "filename": "x.png"},
            },
        )
        self.assertEqual(kind, "nested")
        self.assertEqual(view["description"], "inner prompt")

    def test_write_is_not_image_gen(self) -> None:
        kind, view = image_gen_arg_view("Write", {"path": "a.py", "contents": "x = 1"})
        self.assertEqual(kind, "")
        self.assertEqual(view, {})


class TestHookInjectsGenerateImage(unittest.TestCase):
    def test_updated_input_prepends_session_warm_start(self) -> None:
        td = Path(tempfile.mkdtemp(prefix="pmem_recall_hook_"))
        try:
            data = _project(td)
            conv = td / ".memory-art" / "converge"
            conv.mkdir(parents=True)
            block = f"{WARM_START_MARK}】\n- 必须避开红线:\n  · 禁止把蜜桃糖焊进蛋糕"
            sess = {
                "session_id": "auto_recall_hook",
                "module": "prop.Candy",
                "goal": "合成梯糖果",
                "warm_start": {"prompt_block": block, "module": "prop.Candy"},
            }
            (conv / "auto_recall_hook.json").write_text(
                json.dumps(sess, ensure_ascii=False), encoding="utf-8"
            )
            mark_active_session(td, "auto_recall_hook")
            payload = {
                "tool_name": "GenerateImage",
                "tool_input": {
                    "description": "peach candy bottle game icon square",
                    "aspect_ratio": "1:1",
                },
            }
            old_stdin = sys.stdin
            sys.stdin = io.StringIO(json.dumps(payload, ensure_ascii=False))
            buf = io.StringIO()
            try:
                with redirect_stdout(buf):
                    rc = cmd_hook(td, data, "pre-gen")
            finally:
                sys.stdin = old_stdin
            self.assertEqual(rc, 0)
            out = json.loads(buf.getvalue())
            self.assertEqual(out.get("permission"), "allow")
            updated = out.get("updated_input") or {}
            desc = str(updated.get("description") or "")
            self.assertTrue(desc.startswith(WARM_START_MARK), desc[:80])
            self.assertIn("peach candy bottle game icon square", desc)
            self.assertIn("蜜桃糖焊进蛋糕", desc)
            msg = str(out.get("agent_message") or out.get("agentMessage") or "")
            self.assertIn("【pmem-art记忆】", msg)
            self.assertIn("prop.Candy", msg)
        finally:
            shutil.rmtree(td, ignore_errors=True)

    def test_write_does_not_get_updated_input(self) -> None:
        td = Path(tempfile.mkdtemp(prefix="pmem_recall_write_"))
        try:
            data = _project(td)
            payload = {
                "tool_name": "Write",
                "tool_input": {"path": "notes.md", "contents": "hello"},
            }
            old_stdin = sys.stdin
            sys.stdin = io.StringIO(json.dumps(payload))
            buf = io.StringIO()
            try:
                with redirect_stdout(buf):
                    cmd_hook(td, data, "pre-gen")
            finally:
                sys.stdin = old_stdin
            out = json.loads(buf.getvalue())
            self.assertNotIn("updated_input", out)
        finally:
            shutil.rmtree(td, ignore_errors=True)


class TestGenerateMergesMemory(unittest.TestCase):
    def test_generate_prompt_contains_warm_start(self) -> None:
        td = Path(tempfile.mkdtemp(prefix="pmem_recall_gen_"))
        try:
            data = _project(td)
            sid = "auto_recall_candy"
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc_start = cmd_converge(
                    td,
                    data,
                    "start",
                    session_id=sid,
                    goal="合成梯糖果药瓶",
                    module="prop.Candy",
                    scale="medium",
                )
            self.assertEqual(rc_start, 0)
            self.assertIn("会自动并入提示词", buf.getvalue())
            img = _noisy_png(td / "out.png")
            gen_buf = io.StringIO()
            with redirect_stdout(gen_buf):
                rc_gen = cmd_converge(
                    td,
                    data,
                    "generate",
                    session_id=sid,
                    round_num=1,
                    prompt="peach candy bottle game icon square",
                    image=str(img),
                    apply_memory=True,
                )
            self.assertEqual(rc_gen, 0, gen_buf.getvalue())
            self.assertIn("已自动并入记忆", gen_buf.getvalue())
            sess = json.loads(
                (td / ".memory-art" / "converge" / f"{sid}.json").read_text(encoding="utf-8")
            )
            prompt = str((sess.get("rounds") or [{}])[0].get("prompt") or "")
            self.assertIn(WARM_START_MARK, prompt)
            self.assertIn("蜜桃糖焊进蛋糕", prompt)
        finally:
            shutil.rmtree(td, ignore_errors=True)


class TestSkillSpecForbidsHandPaste(unittest.TestCase):
    def test_draw_spec_says_auto_inject(self) -> None:
        body = next(s["body"] for s in SKILL_SPECS if s["name"] == "pmem-draw")
        self.assertIn("自动把 Warm-Start", body)
        self.assertIn("updated_input", body)
        self.assertNotIn("完整并入第 1 轮 Prompt", body)


if __name__ == "__main__":
    unittest.main()
