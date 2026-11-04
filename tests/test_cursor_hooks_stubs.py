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

    def test_windows_uses_pyw(self) -> None:
        from lifecycle import _hook_python_prefix

        with mock.patch("lifecycle.sys.platform", "win32"):
            self.assertEqual(_hook_python_prefix(), "pyw -3 -u")
        with mock.patch("lifecycle.sys.platform", "darwin"):
            self.assertEqual(_hook_python_prefix(), "python3")


if __name__ == "__main__":
    unittest.main()
