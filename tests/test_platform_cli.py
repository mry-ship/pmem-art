"""Windows=pyw / macOS=python3 CLI packaging."""
from __future__ import annotations

import unittest
from unittest import mock

from art_cli import (
    cli_python_prefix,
    pmem_art_cli,
    rewrite_cli_invocations,
    rewrite_shell_to_windowless,
)


class TestPlatformCli(unittest.TestCase):
    def test_windows_prefix(self) -> None:
        self.assertEqual(cli_python_prefix(platform="win32"), "pyw -3 -u")
        self.assertEqual(pmem_art_cli(platform="win32"), "pyw -3 -u pmem_art.py")

    def test_posix_prefix(self) -> None:
        self.assertEqual(cli_python_prefix(platform="darwin"), "python3")
        self.assertEqual(pmem_art_cli(platform="linux"), "python3 pmem_art.py")

    def test_rewrite_normalizes_all_launchers(self) -> None:
        src = (
            "run python3 pmem_art.py a; "
            "python pmem_art.py b; "
            "py -3 pmem_art.py c; "
            "pyw -3 -u pmem_art.py d"
        )
        win = rewrite_cli_invocations(src, platform="win32")
        self.assertEqual(win.count("pyw -3 -u pmem_art.py"), 4)
        self.assertNotIn("python3 pmem_art.py", win)
        mac = rewrite_cli_invocations(src, platform="darwin")
        self.assertEqual(mac.count("python3 pmem_art.py"), 4)
        self.assertNotIn("pyw -3 -u pmem_art.py", mac)

    def test_install_render_uses_platform(self) -> None:
        from skills_kit.install import _render_agent_doc_block

        with mock.patch("skills_kit.install.pmem_art_cli", return_value="pyw -3 -u pmem_art.py"):
            block = _render_agent_doc_block()
        self.assertIn("pyw -3 -u pmem_art.py", block)
        self.assertNotIn("python3 pmem_art.py", block)

    def test_rewrite_shell_python_to_pyw(self) -> None:
        cmd = (
            'python pmem_art.py converge start; '
            'python3 image_gen.py --prompt x; '
            'py -3 -c "print(1)"'
        )
        out = rewrite_shell_to_windowless(cmd, platform="win32")
        assert out is not None
        self.assertIn("pyw -3 -u pmem_art.py", out)
        self.assertIn("pyw -3 -u image_gen.py", out)
        self.assertIn('pyw -3 -u -c "print(1)"', out)
        self.assertNotIn("python pmem_art", out)
        self.assertIsNone(rewrite_shell_to_windowless(cmd, platform="darwin"))
        self.assertIsNone(
            rewrite_shell_to_windowless("pyw -3 -u pmem_art.py converge", platform="win32")
        )


if __name__ == "__main__":
    unittest.main()
