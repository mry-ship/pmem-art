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
        self.assertIn("deleteViaBridge", html)
        self.assertIn("renderPromptTraceHtml", html)
        self.assertIn("setBatchMode", html)
        self.assertIn("批量删除", html)
        self.assertIn("pmem-atlas-reveal", html)
        self.assertIn("upgradeFileOriginToHttp", html)
        self.assertIn("btnOpenHttpWorkbench", html)
        self.assertIn("downloadStartWorkbenchHelper", html)
        self.assertIn("connectOrOfferWorkbenchLauncher", html)
        self.assertIn("启动工作台服务", html)
        self.assertIn("waitForRevealBridge", html)
        self.assertTrue((self.td / "打开工作台.cmd").is_file())
        self.assertTrue((self.td / "打开工作台.command").is_file())
        launcher = (self.td / "打开工作台.cmd").read_text(encoding="utf-8")
        self.assertIn("ensure_reveal_daemon", launcher)
        self.assertIn("Path('.').resolve()", launcher)
        self.assertIn("art-atlas.html", launcher)
        self.assertIn("移入垃圾桶失败", html)
        self.assertIn("location.protocol === \"file:\"", html)
        self.assertIn("syncTrashFilterIntoData", html)
        self.assertIn("stripTrashedAssetsFromData", html)
        self.assertIn("详情 · 进化对照", html)
        self.assertIn("openAssetDetail", html)
        self.assertIn('id="detailModal"', html)
        self.assertIn("renderDetailMain", html)
        self.assertIn("resolveMediaSrc", html)
        self.assertIn('loading="eager"', html)
        self.assertIn("info.exists !== false", html)
        self.assertIn("data-full", html)
        self.assertIn("并列参考图", html)
        self.assertIn("promoteAsFinal", html)
        self.assertIn("isWorkbenchHiddenAsset", html)
        self.assertIn("viewerStep", html)
        self.assertIn("setViewerNav", html)
        self.assertIn("teachNavAndMeta", html)
        self.assertIn("renderViewerMeta", html)
        self.assertIn("stripPrevCritiqueFromPrompt", html)
        self.assertIn("formatOwnCritiqueHtml", html)
        self.assertIn("本图不足", html)
        self.assertIn("原图不足", html)
        self.assertIn("为何要出下一张", html)
        self.assertIn("enrichOriginalMeta", html)
        self.assertIn("extractRefCritiqueFromPrompt", html)
        self.assertIn("据此开跑", html)
        self.assertIn("原图分析", html)
        self.assertIn("pathMetaKeyMatch", html)
        self.assertIn("评分摘要", html)
        self.assertIn("Prompt / 不足 / 改点", html)
        self.assertIn("_viewerIgnoreCloseUntil", html)
        self.assertIn('id="ivMetaPanel"', html)
        self.assertIn("iv-meta-score", html)
        self.assertIn("fromTeach", html)
        self.assertIn("btnTeach", html)
        self.assertIn("openTeach", html)
        self.assertIn("openTrashFolder", html)
        self.assertIn("openTeachFolder", html)
        self.assertIn("teachStep", html)
        self.assertIn("btnOpenTrash", html)
        self.assertIn("workbench_guide", html)
        self.assertIn("teach-samples", html)
        self.assertIn("teach-dims", html)
        self.assertIn("teachSetAsFinal", html)
        self.assertIn("设置为最终交稿", html)
        self.assertIn("总分", html)
        self.assertIn("原图", html)
        self.assertIn("z-index: 580", html)
        self.assertIn("formatDimsHtml", html)
        self.assertIn("openViewer", html)
        self.assertIn("id=\"imgViewer\"", html)
        self.assertIn("showImgCtxMenu", html)
        self.assertIn("在文件夹中显示", html)
        self.assertNotIn("window.open(pathToFileUrl(dir)", html)
        self.assertIn("function bindGalleryActions", html)
        self.assertIn("function lookupAsset", html)
        self.assertIn('class="btn-folder"', html)
        self.assertIn("role-chip", html)
        self.assertNotIn("onclick=\"openViewer(${JSON.stringify(a.path)})\"", html)
        self.assertNotIn("revealInFolder(${JSON.stringify(a.path)})", html)
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
        self.assertIn("VIRT_ROW_BUFFER = 8", html)
        self.assertIn("overflow-anchor: none", html)
        self.assertIn("keepScroll", html)
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

    def test_windows_reveal_uses_select_comma_arg(self) -> None:
        from unittest.mock import patch

        from atlas_reveal import reveal_path

        target = self.td / "assets" / "scene" / "demo" / "formal.png"
        _tiny_png(target)
        with patch("atlas_reveal.sys.platform", "win32"), patch("atlas_reveal.subprocess.Popen") as popen:
            self.assertTrue(reveal_path(target))
            popen.assert_called_once()
            args = popen.call_args[0][0]
            self.assertEqual(args[0], "explorer")
            self.assertEqual(args[1], "/select,")

    def test_converge_prompt_trace_attached_to_assets(self) -> None:
        from pmem_art import load_project

        img = self.td / "assets" / "scene" / "demo" / "r1.png"
        _tiny_png(img)
        sess = {
            "session_id": "demo-trace",
            "goal": "trace test",
            "module": "scene.Demo",
            "threshold": 9.5,
            "status": "finished",
            "rounds": [
                {
                    "round": 1,
                    "round_label": "第 1 轮初稿",
                    "score": 8.2,
                    "passed": False,
                    "prompt": "round1 prompt alpha",
                    "next_fix": "fix lighting",
                    "defects": "too dark",
                    "strengths": "clear subject",
                    "image": "assets/scene/demo/r1.png",
                    "generated_at": "12:00:00",
                },
                {
                    "round": 2,
                    "round_label": "第 2 轮",
                    "score": 9.6,
                    "passed": True,
                    "prompt": "round2 prompt beta",
                    "next_fix": "",
                    "defects": "",
                    "strengths": "ok",
                    "image": "assets/scene/demo/r1.png",
                    "generated_at": "12:01:00",
                },
            ],
        }
        (self.td / ".memory-art" / "converge" / "demo-trace.json").write_text(
            json.dumps(sess, ensure_ascii=False), encoding="utf-8"
        )
        data = load_project(self.td, embed_images=False)
        self.assertIn("demo-trace", data.get("converge_sessions") or {})
        asset = data["assets"]["assets/scene/demo/r1.png"]
        self.assertEqual(asset.get("converge_session_id"), "demo-trace")
        self.assertEqual(asset.get("converge_round"), 2)
        self.assertIn("round2 prompt beta", asset.get("prompt") or "")

    def test_delete_paths_only_images_under_root(self) -> None:
        from atlas_reveal import TRASH_REL, delete_paths

        img = self.td / "assets" / "scene" / "demo" / "kill.png"
        _tiny_png(img)
        other = self.td / "assets" / "scene" / "demo" / "notes.txt"
        other.write_text("nope", encoding="utf-8")
        out = delete_paths(self.td, ["assets/scene/demo/kill.png", "assets/scene/demo/notes.txt"])
        self.assertIn("assets/scene/demo/kill.png", out["deleted"])
        self.assertEqual(out.get("mode"), "trash")
        self.assertFalse(img.exists())
        trash_img = self.td / TRASH_REL / "assets" / "scene" / "demo" / "kill.png"
        self.assertTrue(trash_img.is_file(), "deleted image should land in trash")
        self.assertTrue(other.exists())
        self.assertTrue(any(e.get("error") == "not an image" for e in out["errors"]))
        # 刷新扫描不应再看到原路径
        from atlas_index import scan_project_images

        paths = {i["path"] for i in scan_project_images(self.td)}
        self.assertNotIn("assets/scene/demo/kill.png", paths)
        self.assertTrue(all("/_trash/" not in p for p in paths))

    def test_delete_purges_atlas_sidecar_so_refresh_stays_gone(self) -> None:
        """删进垃圾桶后必须踢掉 atlas_data.json，否则网页刷新会把图又加载回来。"""
        from atlas_reveal import delete_paths

        img = self.td / "assets" / "scene" / "demo" / "refresh_back.png"
        _tiny_png(img)
        side = self.td / ".memory-art" / "atlas_data.json"
        side.write_text(
            json.dumps(
                {
                    "assets": {
                        "assets/scene/demo/refresh_back.png": {
                            "path": "assets/scene/demo/refresh_back.png",
                            "exists": True,
                            "plate": "final",
                        },
                        "assets/scene/demo/keep.png": {
                            "path": "assets/scene/demo/keep.png",
                            "exists": True,
                            "plate": "final",
                        },
                    },
                    "index_images": [
                        {"path": "assets/scene/demo/refresh_back.png"},
                        {"path": "assets/scene/demo/keep.png"},
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        out = delete_paths(self.td, ["assets/scene/demo/refresh_back.png"])
        self.assertIn("assets/scene/demo/refresh_back.png", out["deleted"])
        payload = json.loads(side.read_text(encoding="utf-8"))
        self.assertNotIn("assets/scene/demo/refresh_back.png", payload.get("assets") or {})
        self.assertIn("assets/scene/demo/keep.png", payload.get("assets") or {})
        idx_paths = [x.get("path") for x in (payload.get("index_images") or [])]
        self.assertNotIn("assets/scene/demo/refresh_back.png", idx_paths)

    def test_scan_skips_trash_and_workbench_guide(self) -> None:
        from atlas_index import scan_project_images

        guide = self.td / "docs" / "workbench_guide" / "merge-ladder"
        trash = self.td / ".memory-art" / "_trash" / "assets" / "scene" / "demo"
        _tiny_png(guide / "final.jpg")
        _tiny_png(trash / "kill.png")
        _tiny_png(self.td / "assets" / "scene" / "demo" / "keep.png")
        paths = {i["path"] for i in scan_project_images(self.td)}
        self.assertIn("assets/scene/demo/keep.png", paths)
        self.assertTrue(all("workbench_guide" not in p for p in paths))
        self.assertTrue(
            all("/_trash/" not in p and not p.startswith(".memory-art/_trash/") for p in paths)
        )

    def test_delete_rejects_protected_teaching_assets(self) -> None:
        from atlas_reveal import delete_paths

        guide = self.td / "docs" / "workbench_guide" / "draw-ordinary"
        img = guide / "final.jpg"
        _tiny_png(img)
        out = delete_paths(self.td, ["docs/workbench_guide/draw-ordinary/final.jpg"])
        self.assertEqual(out.get("deleted") or [], [])
        self.assertTrue(img.is_file())
        self.assertTrue(any(e.get("error") == "protected teaching asset" for e in out["errors"]))

    def test_repo_catalog_prompts_match_lesson_images(self) -> None:
        """教学文案必须贴合样例图题材，禁止皮箱/水滴等串课话术。"""
        cat_path = Path(__file__).resolve().parents[1] / "docs" / "workbench_guide" / "catalog.json"
        if not cat_path.is_file():
            self.skipTest("repo catalog missing")
        doc = json.loads(cat_path.read_text(encoding="utf-8"))
        by_id = {str(l.get("id")): l for l in (doc.get("lessons") or []) if isinstance(l, dict)}
        ordinary = json.dumps(by_id.get("draw-ordinary") or {}, ensure_ascii=False)
        self.assertIn("蘑菇", ordinary)
        self.assertNotIn("皮箱", ordinary)
        self.assertNotIn("箱角", ordinary)
        variant = json.dumps(by_id.get("draw-variant") or {}, ensure_ascii=False)
        self.assertIn("果篮", variant)
        self.assertNotIn("举手态", variant)
        icon_a = json.dumps(by_id.get("icon-a") or {}, ensure_ascii=False)
        self.assertIn("仙女", icon_a)
        self.assertNotIn("水滴符号", icon_a)
        icon_c = json.dumps(by_id.get("icon-c") or {}, ensure_ascii=False)
        self.assertIn("爆米花", icon_c)
        merge = json.dumps(by_id.get("merge-ladder") or {}, ensure_ascii=False)
        self.assertIn("海船", merge)
        self.assertIn("乐器", merge)

    def test_load_workbench_guide_marks_existing_examples(self) -> None:
        from build_atlas import load_workbench_guide

        cat = {
            "version": 1,
            "base_dir": "docs/workbench_guide",
            "lessons": [
                {
                    "id": "demo",
                    "skill": "/pmem-draw",
                    "title": "Demo",
                    "when": "test",
                    "how": ["a"],
                    "examples": [
                        {"role": "final", "label": "终稿", "path": "demo/final.jpg"},
                        {"role": "ref", "label": "缺", "path": "demo/missing.jpg"},
                    ],
                }
            ],
        }
        guide_dir = self.td / "docs" / "workbench_guide" / "demo"
        _tiny_png(guide_dir / "final.jpg")
        (self.td / "docs" / "workbench_guide" / "catalog.json").write_text(
            json.dumps(cat, ensure_ascii=False), encoding="utf-8"
        )
        doc = load_workbench_guide(self.td)
        self.assertEqual(len(doc["lessons"]), 1)
        ex = doc["lessons"][0]["examples"]
        self.assertEqual(ex[0]["path"], "docs/workbench_guide/demo/final.jpg")
        self.assertTrue(ex[0]["exists"])
        self.assertFalse(ex[1]["exists"])

    def test_reveal_creates_empty_trash_dir(self) -> None:
        from atlas_reveal import TRASH_REL, RevealHandler

        handler = RevealHandler.__new__(RevealHandler)
        handler.root = self.td.resolve()
        trash = self.td / TRASH_REL
        self.assertFalse(trash.exists())
        target = handler._resolve_reveal_target(TRASH_REL)
        self.assertIsNotNone(target)
        self.assertTrue(trash.is_dir())

    def test_reveal_serves_workbench_html_over_http(self) -> None:
        """工作台需由 reveal 用 http 托管，避免 file:// 下删除 POST 被浏览器拦截。"""
        import socket
        import threading
        import urllib.request
        from http.server import ThreadingHTTPServer

        from atlas_reveal import RevealHandler

        html = self.td / "art-atlas.html"
        html.write_text("<html>workbench-ok</html>", encoding="utf-8")
        (self.td / "assets" / "scene" / "demo").mkdir(parents=True, exist_ok=True)
        img = self.td / "assets" / "scene" / "demo" / "keep.png"
        _tiny_png(img)

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", 0))
        port = int(s.getsockname()[1])
        s.close()

        RevealHandler.root = self.td.resolve()
        httpd = ThreadingHTTPServer(("127.0.0.1", port), RevealHandler)
        t = threading.Thread(target=httpd.serve_forever, daemon=True)
        t.start()
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/art-atlas.html", timeout=2) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                self.assertEqual(resp.status, 200)
                self.assertIn("workbench-ok", body)
            with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/assets/scene/demo/keep.png", timeout=2
            ) as resp:
                self.assertEqual(resp.status, 200)
                self.assertGreater(len(resp.read()), 10)
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/ping", timeout=2) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
                self.assertTrue(payload.get("ok"))
                self.assertIn("static", payload.get("apis") or [])
                self.assertIn("/art-atlas.html", payload.get("workbench") or "")
        finally:
            httpd.shutdown()

    def test_promote_final_copies_over_slot_and_keeps_session(self) -> None:
        from atlas_reveal import promote_final

        src = self.td / "assets" / "scene" / "demo" / "shot_r2.png"
        final = self.td / "assets" / "scene" / "demo" / "shot_final.png"
        _tiny_png(src)
        _tiny_png(final)
        old = final.read_bytes()
        new = src.read_bytes()
        self.assertNotEqual(old, new) if False else None  # same tiny png; still copy
        # make source distinct
        src.write_bytes(new + b"\x00\x01")
        sess = {
            "session_id": "promo-demo",
            "winner_image": "assets/scene/demo/shot_final.png",
            "rounds": [{"round": 2, "image": "assets/scene/demo/shot_r2.png", "prompt": "keep me"}],
        }
        (self.td / ".memory-art" / "converge" / "promo-demo.json").write_text(
            json.dumps(sess, ensure_ascii=False), encoding="utf-8"
        )
        out = promote_final(
            self.td,
            source_path="assets/scene/demo/shot_r2.png",
            final_path="assets/scene/demo/shot_final.png",
            session_id="promo-demo",
            round_num=2,
        )
        self.assertTrue(out.get("ok"), out)
        self.assertEqual(final.read_bytes(), src.read_bytes())
        updated = json.loads(
            (self.td / ".memory-art" / "converge" / "promo-demo.json").read_text(encoding="utf-8")
        )
        self.assertEqual(updated.get("winner_image"), "assets/scene/demo/shot_final.png")
        self.assertEqual(updated.get("promoted_from"), "assets/scene/demo/shot_r2.png")
        self.assertEqual(updated.get("rounds")[0].get("prompt"), "keep me")


if __name__ == "__main__":
    unittest.main()
