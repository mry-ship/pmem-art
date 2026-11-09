"""Alpha / isolation background policy by image engine."""
from __future__ import annotations

import unittest

from skills_kit.alpha_policy import (
    bg_prompt_clause,
    engine_supports_alpha,
    isolation_mode,
    post_key_allowed,
    policy_summary,
)
from skills_kit.reasonableness_gate import _heuristic_issues


class AlphaPolicyTests(unittest.TestCase):
    def test_cursor_opaque_only(self) -> None:
        self.assertFalse(engine_supports_alpha("cursor.GenerateImage"))
        self.assertFalse(engine_supports_alpha("Cursor"))
        self.assertEqual(isolation_mode("cursor.GenerateImage"), "opaque_isolation")
        clause = bg_prompt_clause("cursor.GenerateImage")
        self.assertIn("不透明隔离底", clause)
        self.assertIn("禁止", clause)

    def test_gpt_image_true_alpha(self) -> None:
        self.assertTrue(engine_supports_alpha("gpt-image"))
        self.assertTrue(engine_supports_alpha("gpt-image-1.5"))
        self.assertEqual(isolation_mode("gpt-image"), "true_alpha")
        clause = bg_prompt_clause("gpt-image")
        self.assertIn("真 alpha", clause)

    def test_post_key_never_default(self) -> None:
        self.assertFalse(post_key_allowed("cursor.GenerateImage"))
        self.assertFalse(post_key_allowed("gpt-image"))

    def test_policy_summary_keys(self) -> None:
        s = policy_summary("cursor.GenerateImage")
        self.assertEqual(s["isolation_mode"], "opaque_isolation")
        self.assertFalse(s["supports_alpha"])
        self.assertFalse(s["post_key_allowed"])


class IconCIsolationGateTests(unittest.TestCase):
    def test_accepts_solid_isolation(self) -> None:
        issues = _heuristic_issues(
            "icon.c",
            "药水图标",
            "厚剪影治疗药水，纯黑隔离底，棚拍主光，无字无场景，1:1。",
        )
        self.assertFalse(any("缺底隔离" in x or "缺透明底" in x for x in issues))

    def test_accepts_transparent_wording(self) -> None:
        issues = _heuristic_issues(
            "icon.c",
            "药水图标",
            "厚剪影治疗药水，transparent alpha 透明底，棚拍主光，无字。",
        )
        self.assertFalse(any("缺底隔离" in x for x in issues))

    def test_rejects_missing_bg(self) -> None:
        issues = _heuristic_issues(
            "icon.c",
            "药水图标",
            "厚剪影治疗药水，棚拍主光，无字无场景，居中。",
        )
        self.assertTrue(any("缺底隔离" in x for x in issues))




class ExportModeCOpaqueTests(unittest.TestCase):
    def test_default_keeps_opaque_rgb(self) -> None:
        import sys
        import tempfile
        from pathlib import Path as P

        from PIL import Image

        import skills_kit.export_mode_c_icon as mod
        from skills_kit.export_mode_c_icon import as_delivery_rgba

        im = Image.new("RGB", (64, 64), (0, 0, 0))
        for x in range(16, 48):
            for y in range(16, 48):
                im.putpixel((x, y), (200, 40, 40))
        rgba = as_delivery_rgba(im, key_flat_bg=False)
        self.assertEqual(rgba.getchannel("A").getextrema()[0], 255)

        with tempfile.TemporaryDirectory() as td:
            src = P(td) / "master.png"
            im.save(src)
            out = P(td) / "out"
            old = sys.argv
            try:
                sys.argv = ["export_mode_c_icon.py", str(src), "--out-dir", str(out), "--stem", "t"]
                mod.main()
            finally:
                sys.argv = old
            with Image.open(out / "t_master.png") as master:
                self.assertEqual(master.mode, "RGB")
            self.assertTrue((out / "t_256.png").is_file())


if __name__ == "__main__":
    unittest.main()
