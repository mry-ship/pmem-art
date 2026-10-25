"""AppleDouble / junk sidecars, medium SSS module gate, taste phrase clipping."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestJunkSidecarSkip(unittest.TestCase):
    def test_iter_md_skips_appledouble(self) -> None:
        from lifecycle import is_junk_sidecar_name, iter_md_files

        self.assertTrue(is_junk_sidecar_name("._ok.md"))
        self.assertFalse(is_junk_sidecar_name("ok.md"))
        td = Path(tempfile.mkdtemp())
        (td / "ok.md").write_text("# hi", encoding="utf-8")
        (td / "._ok.md").write_bytes(bytes([0x00, 0x05, 0x16, 0x07]) + b"\xff\xfe" + bytes(range(64)))
        names = [p.name for p in iter_md_files(td, recursive=False)]
        self.assertEqual(names, ["ok.md"])

    def test_list_image_files_skips_appledouble_jpg(self) -> None:
        from lifecycle import list_image_files

        td = Path(tempfile.mkdtemp())
        assets = td / "assets" / "x"
        assets.mkdir(parents=True)
        real = assets / "hero.jpg"
        real.write_bytes(b"\xff\xd8\xff\xd9")  # minimal JPEG markers
        junk = assets / "._hero.jpg"
        junk.write_bytes(bytes([0x00, 0x05, 0x16, 0x07]) + b"\xff\xfe" + bytes(32))
        found = [p.name for p in list_image_files(td, ["assets"])]
        self.assertEqual(found, ["hero.jpg"])

    def test_load_project_survives_appledouble_in_specs(self) -> None:
        import pmem_art

        td = Path(tempfile.mkdtemp())
        mem = td / ".memory-art"
        (mem / "entries" / "x").mkdir(parents=True)
        (mem / "specs" / "ui").mkdir(parents=True)
        (mem / "config.yaml").write_text("project:\n  name: t\n", encoding="utf-8")
        (mem / "modules.yaml").write_text("modules: {}\n", encoding="utf-8")
        (mem / "entries" / "x" / "ok.md").write_text(
            "---\nid: a\nmodule: brand.X\nkind: recipe\nsummary: s\n---\nbody\n",
            encoding="utf-8",
        )
        (mem / "entries" / "x" / "._ok.md").write_bytes(
            bytes([0x00, 0x05, 0x16, 0x07]) + b"\xff\xfe" + bytes(range(200))
        )
        (mem / "specs" / "ui" / "._spec.md").write_bytes(
            bytes([0x00, 0x05, 0x16, 0x07]) + b"\xff\xfe" + bytes(range(200))
        )
        (mem / "specs" / "ui" / "spec.md").write_text("# ok", encoding="utf-8")
        data = pmem_art.load_project(td)
        self.assertIn("ui", data.get("specs") or {})
        self.assertEqual(data["specs"]["ui"].get("spec"), "# ok")
        self.assertNotIn("._spec", data["specs"]["ui"])


class TestMediumNoSssForUiPixel(unittest.TestCase):
    def test_ui_and_pixel_skip_sss(self) -> None:
        from skills_kit import get_converge_scale_profile

        ui = get_converge_scale_profile("medium", module="ui.HUD", goal="血条")
        self.assertNotIn("次表面散射", ui["prompt_directive"])
        self.assertIn("色块", ui["prompt_directive"])
        pix = get_converge_scale_profile("medium", module="prop.pixel_icon", goal="像素道具")
        self.assertNotIn("次表面散射", pix["prompt_directive"])
        portrait = get_converge_scale_profile(
            "medium",
            module="character.Sunlit",
            goal="窗边肖像",
            ref_image="style_ref_03_sunlit_portrait.png",
        )
        self.assertIn("次表面散射", portrait["prompt_directive"])

    def test_static_medium_table_does_not_claim_sss(self) -> None:
        """Reading CONVERGE_SCALE_PROFILES directly must not imply every medium run gets SSS."""
        from skills_kit.prompt_scale import CONVERGE_SCALE_PROFILES

        static = CONVERGE_SCALE_PROFILES["medium"]["prompt_directive"]
        self.assertNotIn("次表面散射", static)
        self.assertNotIn("SSS", static.upper())


class TestTasteClipPhrase(unittest.TestCase):
    def test_clip_at_punctuation(self) -> None:
        from improve.taste_profile import clip_phrase

        long = "保持侧逆光与纸纹飞白，不要平光证件照构图，另外背景再拉开一点空气层次与冷暖对比。继续补体积光。"
        clipped = clip_phrase(long, 18)
        self.assertLessEqual(len(clipped), 18)
        self.assertIn("飞白", clipped)
        self.assertNotIn("证件照", clipped)  # break at first comma when budget is tight
        self.assertEqual(clip_phrase(long, 80), long)  # under budget → unchanged
        self.assertEqual(clip_phrase("短句", 80), "短句")


if __name__ == "__main__":
    unittest.main()
