"""交件闸：9.5、整表体量、Gossip Harbor 货柜、点名锁、同一张加边垫图。"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PIL import Image  # noqa: E402

from skills_kit.delivery_gates import (  # noqa: E402
    generate_prefix,
    is_delivery_pass,
    judge_gate_notes,
    overview_sheet_hints,
)
from skills_kit.local_locks import unresolved_named_locks  # noqa: E402
from skills_kit.merge_relation import (  # noqa: E402
    _cell_subject_height_ratio,
    audit_overview_sheet,
    merge_surface_lock_line,
)
from skills_kit.validate_params import validate_converge_params  # noqa: E402


def _sheet(path: Path, heights: list[int]) -> None:
    rows, cols = 2, 2
    cell_w, cell_h = 80, 80
    im = Image.new("RGB", (cell_w * cols, cell_h * rows), (24, 26, 28))
    px = im.load()
    for i, bh in enumerate(heights):
        r, c = divmod(i, cols)
        x0, y0 = c * cell_w, r * cell_h
        for y in range(y0 + 8, y0 + cell_h - 8):
            for x in range(x0 + 8, x0 + cell_w - 8):
                px[x, y] = (244, 244, 240)
        top = y0 + (cell_h - bh) // 2
        for y in range(top, top + bh):
            for x in range(x0 + 28, x0 + cell_w - 28):
                px[x, y] = (210, 80, 70)
    im.save(path)


class DeliveryGateTests(unittest.TestCase):
    def test_pass_line_is_9_5_for_everyone(self) -> None:
        self.assertFalse(is_delivery_pass(8.5))
        self.assertFalse(is_delivery_pass(9.0))
        self.assertTrue(is_delivery_pass(9.5))

    def test_merge_without_style_is_gossip_harbor(self) -> None:
        line = merge_surface_lock_line("甜品八档合成梯", "")
        self.assertIn("Gossip Harbor", line)
        self.assertIn("玩具货柜", line)
        self.assertIn("写实摄影", line)
        self.assertIn("美食棚拍", line)
        self.assertEqual(merge_surface_lock_line("写实甜品摄影", ""), "")
        # 仅点名 GH 不够：仍须注入完整禁写实硬句
        still = merge_surface_lock_line("merge.DewberryJam", "Gossip Harbor glossy cartoon 3D juice mousse")
        self.assertIn("美食棚拍", still)
        # Warm-Start 零散命中「棋盘缩略 / 产品静物」不得整句跳过
        diluted = merge_surface_lock_line(
            "merge.DewberryJam",
            "配方：棋盘缩略一眼可认；红线：避免产品静物拼贴；Gossip Harbor glossy cartoon 3D",
        )
        self.assertIn("材质锁死", diluted)
        self.assertIn("写实摄影", diluted)
        # 完整硬句已在文中才跳过
        full = (
            "休闲 merge 货柜默认气质：Gossip Harbor 玩具货柜卡通——"
            "光泽卡通 3D、圆润厚实、无硬描边、暖饱和、柔光渐变、糖釉玩具高光、棋盘缩略一眼可认。"
            "材质锁死为卡通玩具/糖釉道具，不是实物。"
            "禁止：写实摄影、美食棚拍、产品静物、玻璃真实折射、木纹指纹、果汁乳浊摄影感、"
            "微距毛孔、油光金属、暗沉旧塑料。"
        )
        self.assertEqual(merge_surface_lock_line("merge.Jam", full), "")
        # taste「避开赛博霓虹」在 prompt 里不得误关锁；goal 真点名水彩/写实仍留空
        cyber_taste = (
            "个人禁用习惯：廉价塑料感/油腻高光；赛博霓虹/霓虹紫；白底不可接受"
        )
        locked = merge_surface_lock_line(
            goal="露莓果酱八档合成梯整表",
            prompt=cyber_taste,
        )
        self.assertIn("材质锁死", locked)
        self.assertIn("写实摄影", locked)
        prefixed = generate_prefix(
            {"route_ids": ["merge.ladder"], "goal": "露莓果酱八档合成梯整表"},
            cyber_taste,
        )
        self.assertTrue(prefixed.startswith("休闲 merge"), prefixed[:80])
        self.assertEqual(merge_surface_lock_line(goal="水彩甜品合成梯", prompt=cyber_taste), "")
        self.assertEqual(merge_surface_lock_line(goal="写实果酱货柜", prompt=""), "")
        prompt = generate_prefix(
            {"route_ids": ["merge.ladder"], "goal": "甜品合成梯 2×4"},
            "Gossip Harbor glossy cartoon 3D juice glass wood spoon",
        )
        self.assertIn("Gossip Harbor", prompt)
        self.assertIn("美食棚拍", prompt)
        self.assertIn("玩具货柜", prompt)
        self.assertTrue(prompt.startswith("休闲 merge"))
        notes = judge_gate_notes(
            {"route_ids": ["merge.ladder"], "goal": "甜品合成梯"},
            defects="玻璃真实折射、木纹指纹偏棚拍",
            strengths="构图整齐",
        )
        self.assertTrue(any("偏写实" in n for n in notes), notes)

    def test_no_ref_strips_keep_original_style_identity(self) -> None:
        from skills_kit.prompt_scale import compose_style_first_prompt, get_converge_scale_profile

        prof = get_converge_scale_profile(
            "medium",
            goal="露莓果酱八档合成梯整表",
            module="merge.DewberryJam",
            ref_image="",
        )
        self.assertTrue(
            str(prof.get("prompt_directive") or "").startswith("品类默认画风优先"),
            prof.get("prompt_directive"),
        )
        blob = "\n".join(str(x) for x in (prof.get("forbidden_changes") or []))
        self.assertNotIn("保持原图画风", blob)
        self.assertNotIn("性别、物种、年龄段", blob)
        self.assertIn("禁止回落写实", blob)
        text = compose_style_first_prompt("八格果酱货柜", prof)
        self.assertNotIn("保持原图画风", text)
        self.assertNotIn("性别、物种、年龄段", text)
        self.assertIn("禁止回落写实", text)
        # 有垫图时仍保留角色改图锁
        with_ref = get_converge_scale_profile(
            "medium",
            goal="露莓果酱",
            module="merge.DewberryJam",
            ref_image="assets/refs/jam.png",
        )
        ref_blob = "\n".join(str(x) for x in (with_ref.get("forbidden_changes") or []))
        self.assertIn("保持原图画风", ref_blob)

    def test_overview_volume_flat_neighbors_are_soft_hints(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            flat = Path(tmp) / "flat.png"
            shrunk = Path(tmp) / "shrunk.png"
            grown = Path(tmp) / "grown.png"
            # 近邻框高接近：提示，但不过闸失败（对标 GH 咖啡链）。
            _sheet(flat, [48, 50, 49, 52])
            # 末档明显矮于前档：硬伤。
            _sheet(shrunk, [56, 52, 48, 24])
            _sheet(grown, [16, 28, 40, 56])
            ok_flat, flat_issues = audit_overview_sheet(flat, rows=2, cols=2)
            self.assertTrue(ok_flat, flat_issues)
            self.assertTrue(any(item.startswith("提示：") for item in flat_issues))
            ok_shrunk, shrunk_issues = audit_overview_sheet(shrunk, rows=2, cols=2)
            self.assertFalse(ok_shrunk)
            self.assertTrue(any("末档明显小于" in item for item in shrunk_issues))
            ok_grown, grown_issues = audit_overview_sheet(grown, rows=2, cols=2)
            self.assertTrue(ok_grown, grown_issues)
            sess = {"merge_delivery": "overview_sheet", "goal": "2×2 甜品"}
            notes_flat = judge_gate_notes(
                sess,
                image=str(flat),
                defects="",
                strengths="",
            )
            self.assertFalse(any("提示：" in note for note in notes_flat))
            hints = overview_sheet_hints(sess, image=str(flat))
            self.assertTrue(any(h.startswith("提示：") for h in hints))
            notes_shrunk = judge_gate_notes(
                sess,
                image=str(shrunk),
                defects="",
                strengths="",
            )
            self.assertTrue(any("末档明显小于" in note for note in notes_shrunk))

    def test_cream_card_height_measures_object_not_card(self) -> None:
        """浅色圆角卡整表：框高必须量物件，不能把卡高量成 ≈1.0。"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cream_card.png"
            # 桃色格缝 + 奶油卡 + 居中洋红莓（约占格高 0.55）
            cell = 160
            im = Image.new("RGB", (cell * 2, cell * 2), (253, 211, 172))
            px = im.load()
            for r in range(2):
                for c in range(2):
                    x0, y0 = c * cell, r * cell
                    for y in range(y0 + 10, y0 + cell - 10):
                        for x in range(x0 + 10, x0 + cell - 10):
                            px[x, y] = (255, 236, 214)
                    top = y0 + int(cell * 0.22)
                    bot = y0 + int(cell * 0.78)
                    for y in range(top, bot):
                        for x in range(x0 + 55, x0 + cell - 55):
                            px[x, y] = (210, 70, 130)
            im.save(path)
            import numpy as np

            arr = np.array(im)
            h0 = _cell_subject_height_ratio(arr[0:cell, 0:cell])
            self.assertGreater(h0, 0.45, h0)
            self.assertLess(h0, 0.78, h0)
            ok, issues = audit_overview_sheet(path, rows=2, cols=2)
            self.assertTrue(ok, issues)
            # 不应再出现「四格全是 0.95+ 卡片框高」那种假平坦
            self.assertFalse(
                all("0.9" in item and "→" in item for item in issues if item.startswith("提示：邻档")),
            )

    def test_verify_sheet_r1_peels_cream_cards(self) -> None:
        """真跑 sheet_r1：剥卡+去暖色投影后 L2/L8 落在物件带；整表可过软提示。"""
        sheet = ROOT / "assets/skill_20261110_verify/merge_jam/sheet_r1.jpg"
        if not sheet.is_file():
            self.skipTest("缺少验证整表 sheet_r1.jpg")
        import numpy as np

        arr = np.array(Image.open(sheet).convert("RGB"))
        h, w = arr.shape[:2]
        rows, cols = 4, 2
        heights: list[float] = []
        for r in range(rows):
            for c in range(cols):
                cell = arr[h * r // rows : h * (r + 1) // rows, w * c // cols : w * (c + 1) // cols]
                heights.append(_cell_subject_height_ratio(cell))
        # L2 盘+莓、L8 布丁+盘：投影不得把框高撑到贴卡底。
        self.assertGreaterEqual(heights[1], 0.65, heights)
        self.assertLessEqual(heights[1], 0.85, heights)
        self.assertGreaterEqual(heights[7], 0.65, heights)
        self.assertLessEqual(heights[7], 0.85, heights)
        ok, issues = audit_overview_sheet(sheet, rows=4, cols=2)
        self.assertTrue(ok, issues)

    def test_wind_collage_final_still_rejected(self) -> None:
        """旧管乐拼贴终稿必须继续 ok=False（L6 一类贴边残片不可因剥卡漏检）。"""
        sheet = ROOT / "assets/skill_20261110_gh_portrait_v2/merge_wind/final.jpg"
        if not sheet.is_file():
            self.skipTest("缺少管乐 final.jpg")
        ok, issues = audit_overview_sheet(sheet, rows=4, cols=2)
        self.assertFalse(ok, issues)
        self.assertTrue(any("残片" in item for item in issues), issues)

    def test_jam_collage_final_still_rejected(self) -> None:
        """旧果酱拼贴终稿必须继续 ok=False。"""
        sheet = ROOT / "assets/skill_20261110_gh_portrait_v2/merge_jam/final.jpg"
        if not sheet.is_file():
            self.skipTest("缺少果酱 final.jpg")
        ok, issues = audit_overview_sheet(sheet, rows=4, cols=2)
        self.assertFalse(ok, issues)
        self.assertTrue(any("残片" in item for item in issues), issues)

    def test_overview_rejects_cut_fragment_collage(self) -> None:
        # 抠格拼贴会在格底留一条被切平的半截物件；干净整表没有。
        with tempfile.TemporaryDirectory() as tmp:
            clean = Path(tmp) / "clean.png"
            collage = Path(tmp) / "collage.png"
            _sheet(clean, [30, 40, 50, 60])
            _sheet(collage, [30, 40, 50, 60])
            im = Image.open(collage)
            px = im.load()
            for y in range(72, 78):
                for x in range(28, 52):
                    px[x, y] = (90, 30, 140)
            im.save(collage)
            ok_clean, clean_issues = audit_overview_sheet(clean, rows=2, cols=2)
            self.assertTrue(ok_clean, clean_issues)
            ok_bad, bad_issues = audit_overview_sheet(collage, rows=2, cols=2)
            self.assertFalse(ok_bad)
            self.assertTrue(any("残片" in item for item in bad_issues), bad_issues)
            notes = judge_gate_notes(
                {"merge_delivery": "overview_sheet", "goal": "2×2 甜品"},
                image=str(collage),
                defects="",
                strengths="",
            )
            self.assertTrue(any("残片" in note for note in notes))

    def test_named_lock_needs_its_own_acceptance(self) -> None:
        self.assertTrue(unresolved_named_locks(["嘴改成小圆"], "嘴仍是竖椭圆", "眼睛不错"))
        self.assertEqual(unresolved_named_locks(["嘴改成小圆"], "", "嘴已是小圆"), [])
        notes = judge_gate_notes(
            {
                "goal": "这个妖精嘴改小",
                "understanding_contract": {"l1": {"locks": ["嘴改成小圆"]}},
            },
            defects="整张还行",
            strengths="光影不错",
        )
        self.assertTrue(any("点名锁" in note for note in notes))

    def test_aspect_pad_is_the_only_reference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "fairy.png"
            Image.new("RGB", (30, 60), (12, 18, 16)).save(src)
            first = validate_converge_params(
                session_id="clone-pad",
                aspect_ratio="3:4",
                reference_image_paths=[str(src)],
                root=Path(tmp),
            )
            second = validate_converge_params(
                session_id="clone-pad",
                aspect_ratio="3:4",
                reference_image_paths=[str(src)],
                root=Path(tmp),
            )
            pad = first["reference_image_paths"][0]
            self.assertTrue(pad.endswith("__ar_3x4.png"))
            self.assertEqual(pad, first["reference_image"])
            self.assertEqual(first["reference_image_paths"], second["reference_image_paths"])
            self.assertTrue(Path(pad).is_file())

    def test_portrait_pad_cannot_be_filled_into_landscape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "phone.png"
            Image.new("RGB", (40, 90), (20, 40, 80)).save(src)
            with self.assertRaises(ValueError) as caught:
                validate_converge_params(
                    session_id="merge-pad",
                    aspect_ratio="4:3",
                    reference_image_paths=[str(src)],
                    root=Path(tmp),
                )
            self.assertIn("不能加边填成", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
