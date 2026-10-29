#!/usr/bin/env python3
"""Atlas「所有图」可见索引：扫描范围、分桶、不污染正式记忆、无全量 data_uri。"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

CST = timezone(timedelta(hours=8))


def _tiny_png(path: Path) -> None:
    import base64

    raw = base64.b64decode(
        b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)


class AtlasAllImagesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.td = Path(tempfile.mkdtemp(prefix="pmem_atlas_all_"))
        mem = self.td / ".memory-art"
        mem.mkdir(parents=True)
        (mem / "config.yaml").write_text(
            "schema_version: 1\nproject:\n  name: atlas-test\n",
            encoding="utf-8",
        )
        (mem / "modules.yaml").write_text(
            "schema_version: 1\ncategories: {}\nmodules: {}\nsynonyms: []\n",
            encoding="utf-8",
        )
        (mem / "entries").mkdir()
        (self.td / "assets" / "scene" / "demo").mkdir(parents=True)
        (self.td / ".cursor" / "generated").mkdir(parents=True)
        (self.td / ".memory-art" / "converge" / "sess").mkdir(parents=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.td, ignore_errors=True)

    def test_scan_includes_watch_dirs_and_day_buckets(self) -> None:
        from atlas_index import day_bucket, scan_project_images, write_atlas_index

        today = datetime.now(CST)
        formal = self.td / "assets" / "scene" / "demo" / "formal.png"
        cursor = self.td / ".cursor" / "generated" / "cursor_today.png"
        old = self.td / ".memory-art" / "converge" / "sess" / "old.png"
        _tiny_png(formal)
        _tiny_png(cursor)
        _tiny_png(old)
        os.utime(formal, (today.timestamp(), today.timestamp()))
        os.utime(cursor, (today.timestamp(), today.timestamp()))
        os.utime(old, (today.timestamp() - 172800, today.timestamp() - 172800))

        imgs = scan_project_images(self.td)
        paths = {i["path"] for i in imgs}
        self.assertIn("assets/scene/demo/formal.png", paths)
        self.assertIn(".cursor/generated/cursor_today.png", paths)
        self.assertIn(".memory-art/converge/sess/old.png", paths)

        by_path = {i["path"]: i for i in imgs}
        self.assertEqual(by_path[".cursor/generated/cursor_today.png"]["source"], "cursor_generated")
        self.assertEqual(by_path["assets/scene/demo/formal.png"]["source"], "module")
        self.assertEqual(by_path[".cursor/generated/cursor_today.png"]["day_bucket"], "today")
        self.assertEqual(day_bucket(by_path[".memory-art/converge/sess/old.png"]["day"]), "earlier")
        self.assertEqual(by_path["assets/scene/demo/formal.png"]["plate"], "final")
        self.assertEqual(by_path[".cursor/generated/cursor_today.png"]["plate"], "process")
        self.assertEqual(by_path[".memory-art/converge/sess/old.png"]["plate"], "process")

        idx = write_atlas_index(self.td, imgs)
        self.assertTrue(idx.is_file())
        payload = json.loads(idx.read_text(encoding="utf-8"))
        self.assertEqual(payload["images_count"], 3)
        self.assertIn("visibility index only", payload.get("note", ""))

    def test_scan_does_not_write_recipe_entries(self) -> None:
        from atlas_index import scan_project_images, write_atlas_index

        _tiny_png(self.td / ".cursor" / "generated" / "loose.png")
        before = list((self.td / ".memory-art" / "entries").rglob("*.md"))
        scan_project_images(self.td)
        write_atlas_index(self.td)
        after = list((self.td / ".memory-art" / "entries").rglob("*.md"))
        self.assertEqual(before, after)

    def test_atlas_html_has_no_data_uri_and_includes_all_images_ui(self) -> None:
        import os

        from build_atlas import generate_atlas_html
        from pmem_art import load_project

        os.environ["PMEM_ATLAS_NO_REVEAL"] = "1"
        _tiny_png(self.td / "assets" / "scene" / "demo" / "a.png")
        _tiny_png(self.td / ".cursor" / "generated" / "b.png")
        data = load_project(self.td, embed_images=False)
        self.assertTrue(any(a.get("source") == "cursor_generated" for a in data["assets"].values()))
        for info in data["assets"].values():
            self.assertNotIn("data_uri", info)

        out = generate_atlas_html(data, self.td / "art-atlas.html")
        html = out.read_text(encoding="utf-8")
        self.assertNotIn("data:image/png;base64,", html)
        self.assertIn("所有图归总", html)
        self.assertIn("其他", html)
        self.assertIn("selectDayFilter", html)
        self.assertIn("selectPlateFilter", html)
        self.assertIn('plateFilter: "final"', html)
        self.assertIn("过程稿", html)
        self.assertIn("revealInFolder", html)
        self.assertIn("revealViaBridge", html)
        self.assertIn("openViewer", html)
        self.assertIn("id=\"imgViewer\"", html)
        self.assertIn("showImgCtxMenu", html)
        self.assertIn("在文件夹中显示", html)
        self.assertIn("另存为", html)
        self.assertIn("AUTO_REFRESH_MS = 10000", html)
        self.assertIn("⋯ 更多", html)
        self.assertNotIn("id=\"kpiStrip\"", html)
        self.assertNotIn("各类型资产画廊", html)
        self.assertIn("atlas_data.json", html)
        self.assertIn("paintVirtualGallery", html)
        self.assertIn("THUMB_MIN = 96", html)
        self.assertIn("THUMB_MAX = 360", html)
        self.assertIn("MAX_DECODE = 32", html)
        self.assertIn("VIRT_ROW_BUFFER = 6", html)
        self.assertIn("function thumbSrc", html)
        self.assertIn("thumbSrc(a)", html)
        self.assertLess(out.stat().st_size, 2_000_000)

        self.assertTrue((self.td / ".memory-art" / "atlas_data.json").is_file())
        self.assertTrue((self.td / ".memory-art" / "atlas_index.json").is_file())

    def test_gallery_thumbs_created_for_large_images(self) -> None:
        from PIL import Image

        from atlas_index import ensure_gallery_thumbs

        big = self.td / "assets" / "scene" / "demo" / "big.png"
        # 噪声图保证体积 >40KB，才会走 thumb 缓存（纯色 PNG 会被跳过）
        Image.effect_noise((1024, 1024), 48).convert("RGB").save(big, compress_level=1)
        assets = {
            "assets/scene/demo/big.png": {
                "path": "assets/scene/demo/big.png",
                "mtime": big.stat().st_mtime,
                "width": 1024,
                "height": 1024,
                "size_kb": round(big.stat().st_size / 1024, 1),
            }
        }
        stats = ensure_gallery_thumbs(self.td, assets)
        self.assertGreaterEqual(stats["created"] + stats["cached"], 1)
        self.assertIn("thumb", assets["assets/scene/demo/big.png"])
        thumb = self.td / assets["assets/scene/demo/big.png"]["thumb"]
        self.assertTrue(thumb.is_file())
        self.assertLess(thumb.stat().st_size, big.stat().st_size)


if __name__ == "__main__":
    unittest.main()
