"""ensure_cursor_stubs must keep stop followup for converge auto-continue."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


class TestCursorHooksStubs(unittest.TestCase):
    def test_stop_hook_present_and_generate_image_only(self) -> None:
        from lifecycle import ensure_cursor_stubs

        td = Path(tempfile.mkdtemp(prefix="pmem_hooks_"))
        with mock.patch("lifecycle.install_skills_and_agent_configs", create=True):
            # install is imported inside the function; stub the skills_kit path
            with mock.patch.dict(sys.modules, {"skills_kit": mock.MagicMock()}):
                ensure_cursor_stubs(td)

        data = json.loads((td / ".cursor" / "hooks.json").read_text(encoding="utf-8"))
        hooks = data["hooks"]
        self.assertEqual(hooks["preToolUse"][0]["matcher"], "GenerateImage")
        self.assertEqual(hooks["postToolUse"][0]["matcher"], "GenerateImage")
        stop = hooks["stop"]
        self.assertEqual(len(stop), 1)
        self.assertIn("hook stop", stop[0]["command"])
        self.assertEqual(stop[0]["loop_limit"], 8)
        # 不得再出现会弹黑框的 || 回退链
        for section in hooks.values():
            for item in section:
                self.assertNotIn("||", item.get("command", ""))


    def test_preserves_pmem_rd_hooks_on_refresh(self) -> None:
        from lifecycle import ensure_cursor_stubs

        td = Path(tempfile.mkdtemp(prefix="pmem_hooks_keep_"))
        cursor = td / ".cursor"
        cursor.mkdir(parents=True)
        (cursor / "hooks.json").write_text(
            json.dumps(
                {
                    "version": 1,
                    "hooks": {
                        "preToolUse": [
                            {
                                "command": "pmemw hook pre-tool",
                                "matcher": "Write|Shell",
                                "failClosed": False,
                            }
                        ],
                        "sessionStart": [{"command": ".memory/bin/pmem-hook session"}],
                        "stop": [{"command": "pmemw hook stop", "loop_limit": 1}],
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        with mock.patch.dict(sys.modules, {"skills_kit": mock.MagicMock()}):
            ensure_cursor_stubs(td)

        hooks = json.loads((cursor / "hooks.json").read_text(encoding="utf-8"))["hooks"]
        pre_cmds = [h["command"] for h in hooks["preToolUse"]]
        self.assertTrue(any(c.endswith("pmem_art.py hook pre-gen") for c in pre_cmds))
        self.assertIn("pmemw hook pre-tool", pre_cmds)
        self.assertEqual(hooks["sessionStart"][0]["command"], ".memory/bin/pmem-hook session")
        stop_cmds = [h["command"] for h in hooks["stop"]]
        self.assertTrue(any(c.endswith("pmem_art.py hook stop") for c in stop_cmds))
        self.assertIn("pmemw hook stop", stop_cmds)


    def test_windows_uses_pyw(self) -> None:
        from lifecycle import _hook_python_prefix

        with mock.patch("lifecycle.sys.platform", "win32"):
            self.assertEqual(_hook_python_prefix(), "pyw -3 -u")
        with mock.patch("lifecycle.sys.platform", "darwin"):
            self.assertEqual(_hook_python_prefix(), "python3")

    def test_windows_adds_pre_shell_rewriter(self) -> None:
        from lifecycle import ensure_cursor_stubs

        td = Path(tempfile.mkdtemp(prefix="pmem_hooks_preshell_"))
        with mock.patch("lifecycle.sys.platform", "win32"):
            with mock.patch.dict(sys.modules, {"skills_kit": mock.MagicMock()}):
                ensure_cursor_stubs(td)
        hooks = json.loads((td / ".cursor" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
        shell_hooks = [
            h for h in hooks["preToolUse"] if h.get("matcher") == "Shell"
        ]
        self.assertEqual(len(shell_hooks), 1)
        self.assertIn("art_shell_hook.py", shell_hooks[0]["command"])
        self.assertTrue(shell_hooks[0]["command"].startswith("pyw"))

    def test_windows_strips_shell_from_pmem_pretool_matcher(self) -> None:
        from lifecycle import ensure_cursor_stubs

        td = Path(tempfile.mkdtemp(prefix="pmem_hooks_noshell_"))
        cursor = td / ".cursor"
        cursor.mkdir(parents=True)
        (cursor / "hooks.json").write_text(
            json.dumps(
                {
                    "version": 1,
                    "hooks": {
                        "preToolUse": [
                            {
                                "command": "pmemw hook pre-tool",
                                "matcher": "Write|Shell|MCP|search_memory",
                                "failClosed": False,
                            }
                        ],
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        with mock.patch("lifecycle.sys.platform", "win32"):
            with mock.patch.dict(sys.modules, {"skills_kit": mock.MagicMock()}):
                ensure_cursor_stubs(td)
        hooks = json.loads((cursor / "hooks.json").read_text(encoding="utf-8"))["hooks"]
        pre = [h for h in hooks["preToolUse"] if "pmemw hook pre-tool" in h["command"]][0]
        self.assertNotIn("Shell", pre["matcher"])
        # 写 md 也走 Write：Windows 上匹配 Write 仍会经 PowerShell 弹窗，一并去掉
        self.assertNotIn("Write", pre["matcher"])
        self.assertIn("MCP", pre["matcher"])
        self.assertIn("search_memory", pre["matcher"])

    def test_rewrites_python3_art_launcher_to_pyw_on_windows(self) -> None:
        from lifecycle import ensure_cursor_stubs

        td = Path(tempfile.mkdtemp(prefix="pmem_hooks_pyw_"))
        cursor = td / ".cursor"
        cursor.mkdir(parents=True)
        (cursor / "hooks.json").write_text(
            json.dumps(
                {
                    "version": 1,
                    "hooks": {
                        "preToolUse": [
                            {
                                "command": "python3 pmem_art.py hook pre-gen",
                                "matcher": "GenerateImage",
                                "failClosed": False,
                            },
                            {
                                "command": "pmemw hook pre-tool",
                                "matcher": "Write|Shell",
                                "failClosed": False,
                            },
                        ],
                        "postToolUse": [
                            {
                                "command": "python3 pmem_art.py hook post-asset",
                                "matcher": "GenerateImage",
                            }
                        ],
                        "stop": [
                            {
                                "command": "python3 pmem_art.py hook stop",
                                "loop_limit": 8,
                            }
                        ],
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        with mock.patch("lifecycle.sys.platform", "win32"):
            with mock.patch.dict(sys.modules, {"skills_kit": mock.MagicMock()}):
                ensure_cursor_stubs(td)
        hooks = json.loads((cursor / "hooks.json").read_text(encoding="utf-8"))["hooks"]
        for section in ("preToolUse", "postToolUse", "stop"):
            for item in hooks[section]:
                cmd = item["command"]
                if "pmem_art.py" in cmd:
                    self.assertTrue(cmd.startswith("pyw -3 -u "), cmd)
                    self.assertNotIn("python3 ", cmd)
        self.assertIn("pmemw hook pre-tool", [h["command"] for h in hooks["preToolUse"]])


if __name__ == "__main__":
    unittest.main()
