"""atlas 写入：跨进程文件锁路径存在，且 atlas 与 refresh 共用 write_atlas_html。"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pmem_art  # noqa: E402


class AtlasWriteLockTests(unittest.TestCase):
    def test_write_atlas_html_uses_lock_and_atomic_replace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".memory-art").mkdir(parents=True, exist_ok=True)
            fake_data = {"config": {"project": {"name": "t"}}, "modules": {}, "assets": {}, "entries": [], "index_images": []}

            def _fake_generate(_data: dict, out_file: Path) -> None:
                Path(out_file).write_text("<html>ok</html>\n", encoding="utf-8")

            with mock.patch("build_atlas.generate_atlas_html", side_effect=_fake_generate):
                out = pmem_art.write_atlas_html(root, out_name="art-atlas.html", data=fake_data)
            self.assertTrue(out.is_file())
            self.assertIn("ok", out.read_text(encoding="utf-8"))
            lock = root / ".memory-art" / "art-atlas.write.lock"
            self.assertTrue(lock.is_file())

    def test_refresh_atlas_silent_delegates_to_write_atlas_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            called: list[str] = []

            def _fake_write(r: Path, out_name: str = "art-atlas.html", **kwargs: object) -> Path:
                called.append(out_name)
                p = Path(r) / out_name
                p.write_text("x", encoding="utf-8")
                return p

            with mock.patch.object(pmem_art, "write_atlas_html", side_effect=_fake_write):
                got = pmem_art.refresh_atlas_silent(root)
            self.assertEqual(called, ["art-atlas.html"])
            self.assertIsNotNone(got)


if __name__ == "__main__":
    unittest.main()
