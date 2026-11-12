from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from skills_kit.merge_relation import (
    cell_to_equal_square,
    has_inset_card,
    judge_relation_rows,
    load_phase1,
    parse_rows,
    photo_microdetail_hits,
    place_subject_on_square,
    split_sheet_grid,
    square_grid_boxes,
)


class MergeRelationTests(unittest.TestCase):
    def test_canonical_phase1_passes(self) -> None:
        yaml_path = (
            Path(__file__).resolve().parents[1]
            / "docs/showcase/skill_full_modes_1027/merge_phase1_canonical.yaml"
        )
        if not yaml_path.is_file():
            self.skipTest(f"showcase yaml missing: {yaml_path}")
        data = load_phase1(yaml_path)
        for tid in ("kitchen", "valentine", "stationery"):
            track = data["tracks"][tid]
            rows = parse_rows(track)
            ok, issues = judge_relation_rows(rows, track=track)
            self.assertTrue(ok, f"{tid}: {issues}")

    def test_non_monotonic_pct_allowed(self) -> None:
        """对标 GH 咖啡：体量可不单调；邻档剪影仍须可分。"""
        pcts = [0.83, 0.87, 0.87, 1.00, 0.83, 0.87, 0.92, 0.94]
        rows = parse_rows(
            {
                "rows": [
                    {
                        "level": i,
                        "name": f"x{i}",
                        "silhouette": f"s{i}",
                        "scale_pct": pcts[i - 1],
                        "parts_add": "p" if i > 1 else "—",
                    }
                    for i in range(1, 9)
                ]
            }
        )
        ok, issues = judge_relation_rows(rows)
        self.assertTrue(ok, issues)

    def test_effect_only_parts_fail(self) -> None:
        rows = parse_rows(
            {
                "rows": [
                    {
                        "level": i,
                        "name": f"x{i}",
                        "silhouette": f"s{i}",
                        "scale_pct": 0.55 + i * 0.03,
                        "parts_add": "加光" if i == 2 else ("p" if i > 1 else "—"),
                    }
                    for i in range(1, 9)
                ]
            }
        )
        ok, issues = judge_relation_rows(rows)
        self.assertFalse(ok)
        self.assertTrue(any("L02" in it and "说不通" in it for it in issues))

    def test_l1_too_small_fails(self) -> None:
        rows = parse_rows(
            {
                "rows": [
                    {
                        "level": i,
                        "name": f"x{i}",
                        "silhouette": f"s{i}",
                        "scale_pct": 0.40 + i * 0.03,
                        "parts_add": "p" if i > 1 else "—",
                    }
                    for i in range(1, 9)
                ]
            }
        )
        ok, issues = judge_relation_rows(rows)
        self.assertFalse(ok)
        self.assertTrue(any("L1" in it and "过低" in it for it in issues))

    def test_track_arg_ignored_by_light_gate(self) -> None:
        track = {
            "rows": [
                {
                    "level": i,
                    "name": f"x{i}",
                    "silhouette": f"s{i}",
                    "scale_pct": 0.55 + i * 0.03,
                    "parts_add": "p" if i > 1 else "—",
                }
                for i in range(1, 9)
            ]
        }
        rows = parse_rows(track)
        ok, issues = judge_relation_rows(rows, track=track)
        self.assertTrue(ok, issues)

    def test_species_change_with_concrete_parts_passes(self) -> None:
        names = ["鱼苗", "孔雀鱼", "金鱼", "锦鲤", "神仙鱼", "狮子鱼", "龙鱼", "旗鱼"]
        track = {
            "rows": [
                {
                    "level": i,
                    "name": names[i - 1],
                    "silhouette": f"s{i}",
                    "scale_pct": 0.55 + i * 0.03,
                    "parts_add": "新鳍" if i > 1 else "—",
                }
                for i in range(1, 9)
            ],
        }
        rows = parse_rows(track)
        ok, issues = judge_relation_rows(rows, track=track)
        self.assertTrue(ok, issues)

    def test_shop_ladder_levels_six_needs_evolve_and_why(self) -> None:
        track = {
            "chain_mode": "shop_ladder",
            "levels": 6,
            "rows": [
                {
                    "level": i,
                    "name": f"n{i}",
                    "silhouette": f"s{i}",
                    "scale_pct": 0.58 + (i - 1) * 0.04,
                    "evolve_to": f"e{i}",
                    "merge_why": "两件合成具体下一档" if i > 1 else "—",
                    "parts_add": "—",
                }
                for i in range(1, 7)
            ],
        }
        rows = parse_rows(track)
        ok, issues = judge_relation_rows(rows, track=track)
        self.assertTrue(ok, issues)
        bad = dict(track)
        bad["rows"] = [dict(r) for r in track["rows"]]
        bad["rows"][2]["merge_why"] = "更华丽"
        ok2, issues2 = judge_relation_rows(parse_rows(bad), track=bad)
        self.assertFalse(ok2)
        self.assertTrue(any("merge_why" in it for it in issues2), issues2)

    def test_overview_grid_levels_fifteen_allowed(self) -> None:
        """5×3 atlas reference: levels=15 must parse and pass species_change gate."""
        track = {
            "chain_mode": "species_change",
            "levels": 15,
            "rows": [
                {
                    "level": i,
                    "name": f"n{i}",
                    "silhouette": f"s{i}",
                    "scale_pct": 0.55 + (i - 1) * 0.015,
                    "evolve_to": f"e{i}",
                    "merge_why": "两件合成具体下一档" if i > 1 else "—",
                    "parts_add": "—",
                }
                for i in range(1, 16)
            ],
        }
        rows = parse_rows(track)
        self.assertEqual(len(rows), 15)
        ok, issues = judge_relation_rows(rows, track=track)
        self.assertTrue(ok, issues)

    def test_duplicate_silhouette_fails(self) -> None:
        rows = parse_rows(
            {
                "rows": [
                    {
                        "level": i,
                        "name": f"x{i}",
                        "silhouette": "same",
                        "scale_pct": 0.55 + i * 0.03,
                        "parts_add": "p" if i > 1 else "—",
                    }
                    for i in range(1, 9)
                ]
            }
        )
        ok, issues = judge_relation_rows(rows)
        self.assertFalse(ok)
        self.assertTrue(any("剪影家族" in it for it in issues))

    def test_family_fields_not_required(self) -> None:
        track = {
            "family": {"hue": "青绿"},
            "rows": [
                {
                    "level": i,
                    "name": f"x{i}",
                    "silhouette": f"s{i}",
                    "scale_pct": 0.55 + i * 0.03,
                    "parts_add": "p" if i > 1 else "—",
                }
                for i in range(1, 9)
            ],
        }
        rows = parse_rows(track)
        ok, issues = judge_relation_rows(rows, track=track)
        self.assertTrue(ok, issues)

    def test_base_body_locks_mother_mesh(self) -> None:
        """Same-object ladders may declare base_body; reinventing the mother fails."""
        good = {
            "chain_mode": "same_object",
            "base_body": "透明切面短药瓶",
            "rows": [
                {
                    "level": i,
                    "name": f"药{i}",
                    "silhouette": f"透明切面短药瓶档{i}",
                    "scale_pct": 0.55 + i * 0.03,
                    "parts_add": "塞" if i > 1 else "—",
                }
                for i in range(1, 9)
            ],
        }
        ok, issues = judge_relation_rows(parse_rows(good), track=good)
        self.assertTrue(ok, issues)
        bad = {
            "chain_mode": "same_object",
            "base_body": "透明切面短药瓶",
            "rows": [
                {
                    "level": i,
                    "name": f"宝石{i}",
                    "silhouette": f"实心宝石锥塔{i}",
                    "scale_pct": 0.55 + i * 0.03,
                    "parts_add": "尖" if i > 1 else "—",
                }
                for i in range(1, 9)
            ],
        }
        ok2, issues2 = judge_relation_rows(parse_rows(bad), track=bad)
        self.assertFalse(ok2)
        self.assertTrue(any("未锁母体" in it for it in issues2), issues2)

    def test_same_object_rejects_gift_box_subject_swap(self) -> None:
        # 剪影主语即换货（parts 不是「丝带礼盒」也应拦；不用依赖 parts_add）
        track = {
            "chain_mode": "same_object",
            "base_body": "strawberry soft candy",
            "rows": [
                {
                    "level": 1,
                    "name": "裸草莓软糖",
                    "silhouette": "圆润草莓软糖单颗",
                    "scale_pct": 0.58,
                    "parts_add": "—",
                },
                {
                    "level": 2,
                    "name": "礼盒草莓",
                    "silhouette": "开盖礼盒盛草莓糖",
                    "scale_pct": 0.62,
                    "parts_add": "小金冠",
                },
            ]
            + [
                {
                    "level": i,
                    "name": f"草莓{i}",
                    "silhouette": f"草莓软糖加饰{i}",
                    "scale_pct": 0.58 + i * 0.03,
                    "parts_add": "小金冠",
                }
                for i in range(3, 9)
            ],
        }
        ok, issues = judge_relation_rows(parse_rows(track), track=track)
        self.assertFalse(ok)
        self.assertTrue(any("换货" in it or "礼盒" in it for it in issues), issues)
        trophy = {
            "chain_mode": "same_object",
            "base_body": "草莓软糖",
            "rows": [
                {
                    "level": i,
                    "name": f"草莓软糖{i}",
                    "silhouette": (
                        "金色奖杯盛草莓软糖" if i == 5 else f"圆润草莓软糖档{i}"
                    ),
                    "scale_pct": 0.55 + i * 0.03,
                    "parts_add": "小蒂叶" if i > 1 else "—",
                }
                for i in range(1, 9)
            ],
        }
        ok2, issues2 = judge_relation_rows(parse_rows(trophy), track=trophy)
        self.assertFalse(ok2)
        self.assertTrue(any("奖杯" in it or "换货" in it for it in issues2), issues2)

    def test_en_base_body_matches_zh_silhouette(self) -> None:
        """英文 base_body 应对上中文剪影里的草莓/软糖，不因语言差误杀。"""
        track = {
            "chain_mode": "same_object",
            "base_body": "strawberry soft candy",
            "rows": [
                {
                    "level": i,
                    "name": f"草莓软糖{i}",
                    "silhouette": f"圆润草莓软糖档{i}",
                    "scale_pct": 0.55 + i * 0.03,
                    "parts_add": "小蒂叶" if i > 1 else "—",
                }
                for i in range(1, 9)
            ],
        }
        ok, issues = judge_relation_rows(parse_rows(track), track=track)
        self.assertTrue(ok, issues)

    def test_l8_too_large_fails(self) -> None:
        rows = parse_rows(
            {
                "rows": [
                    {
                        "level": i,
                        "name": f"x{i}",
                        "silhouette": f"s{i}",
                        "scale_pct": 0.70 + (i - 1) * 0.05,
                        "parts_add": "p" if i > 1 else "—",
                    }
                    for i in range(1, 9)
                ]
            }
        )
        # L8 = 0.70 + 0.35 = 1.05 → 超框硬伤（阈值 0.98）
        ok, issues = judge_relation_rows(rows)
        self.assertFalse(ok)
        self.assertTrue(any("L8" in it and "过高" in it for it in issues))

    def test_span_too_extreme_fails(self) -> None:
        rows = parse_rows(
            {
                "rows": [
                    {
                        "level": i,
                        "name": f"x{i}",
                        "silhouette": f"s{i}",
                        "scale_pct": 0.40 + (i - 1) * 0.055,
                        "parts_add": "p" if i > 1 else "—",
                    }
                    for i in range(1, 9)
                ]
            }
        )
        ok, issues = judge_relation_rows(rows)
        self.assertFalse(ok)
        self.assertTrue(any(("过低" in it) or ("过高" in it) for it in issues))

    def test_photo_microdetail_in_silhouette_blocked(self) -> None:
        hits0 = photo_microdetail_hits("盘上烤鱼可见焦斑与柠檬片")
        self.assertTrue(any(h in hits0 for h in ("焦斑", "可见焦斑")), hits0)
        self.assertIn("柠檬片", hits0)
        track = {
            "chain_mode": "shop_ladder",
            "levels": 8,
            "surface": "Gossip Harbor 玩具货柜，禁写实摄影与美食棚拍",
            "rows": [
                {
                    "level": i,
                    "name": f"海鲜{i}",
                    "silhouette": (
                        "盘上一条烤熟整鱼，可见焦斑与柠檬片"
                        if i == 3
                        else f"糖釉玩具海鲜剪影{i}"
                    ),
                    "scale_pct": 0.55 + (i - 1) * 0.05,
                    "parts_add": "—",
                    "evolve_to": f"Tier{i}",
                    "merge_why": "两件合成下一档完整货" if i > 1 else "—",
                }
                for i in range(1, 9)
            ],
        }
        ok, issues = judge_relation_rows(parse_rows(track), track=track)
        self.assertFalse(ok)
        self.assertTrue(any("美食摄影质感词" in it and "L03" in it for it in issues), issues)

        clean = dict(track)
        clean["rows"] = [
            {
                **row,
                "silhouette": f"糖釉玩具海鲜剪影{row['level']}，整块色可读",
            }
            for row in track["rows"]
        ]
        ok2, issues2 = judge_relation_rows(parse_rows(clean), track=clean)
        self.assertTrue(ok2, issues2)

        photo_ok = dict(clean)
        photo_ok["surface"] = "写实美食摄影棚拍静物"
        photo_ok["rows"] = list(track["rows"])  # 带焦斑
        ok3, issues3 = judge_relation_rows(parse_rows(photo_ok), track=photo_ok)
        self.assertTrue(ok3, issues3)

        # 垫 GH 真机：柠檬配菜可跟截图；焦斑仍拦
        gh = dict(clean)
        gh["surface"] = "垫 GH 真机截图锁画风；跟参考棋盘货"
        gh["rows"] = [
            {
                **row,
                "silhouette": (
                    "盘上熟鱼糖釉玩具加柠檬片"
                    if row["level"] == 3
                    else row["silhouette"]
                ),
            }
            for row in clean["rows"]
        ]
        ok4, issues4 = judge_relation_rows(parse_rows(gh), track=gh)
        self.assertTrue(ok4, issues4)
        gh_burn = dict(gh)
        gh_burn["rows"] = [
            {
                **row,
                "silhouette": (
                    "盘上熟鱼可见焦斑"
                    if row["level"] == 3
                    else row["silhouette"]
                ),
            }
            for row in gh["rows"]
        ]
        ok5, issues5 = judge_relation_rows(parse_rows(gh_burn), track=gh_burn)
        self.assertFalse(ok5)
        self.assertTrue(any("焦斑" in it for it in issues5), issues5)

    def test_place_subject_drops_inset_card(self) -> None:
        canvas = Image.new("RGB", (400, 400), (246, 239, 228))
        card = Image.new("RGB", (280, 280), (240, 232, 220))
        px = card.load()
        for y in range(90, 190):
            for x in range(90, 190):
                if (x - 140) ** 2 + (y - 140) ** 2 < 50 ** 2:
                    px[x, y] = (220, 80, 120)
        canvas.paste(card, (60, 60))
        raw = np.array(canvas)
        self.assertTrue(has_inset_card(raw))
        placed = np.array(place_subject_on_square(canvas, 0.60, 256))
        self.assertFalse(has_inset_card(placed))
        self.assertGreater(int((np.abs(placed.astype(int) - (220, 80, 120)).sum(axis=2) < 40).sum()), 200)

    def test_square_grid_boxes_are_equal_squares_in_16x9(self) -> None:
        boxes = square_grid_boxes(1600, 900, rows=2, columns=4)
        self.assertEqual(len(boxes), 8)
        sides = {(x1 - x0, y1 - y0) for x0, y0, x1, y1 in boxes}
        self.assertEqual(len(sides), 1)
        side_w, side_h = next(iter(sides))
        self.assertEqual(side_w, side_h)
        self.assertEqual(side_w, 400)
        self.assertEqual(boxes[0][1], boxes[1][1])
        self.assertEqual(boxes[0][0] + 400, boxes[1][0])

    def test_cell_to_equal_square_centers_subject(self) -> None:
        cell = Image.new("RGB", (400, 400), (210, 210, 210))
        px = cell.load()
        for y in range(20, 120):
            for x in range(20, 120):
                px[x, y] = (40, 160, 80)
        out = cell_to_equal_square(cell, 200)
        self.assertEqual(out.size, (200, 200))
        arr = np.array(out)
        green = np.abs(arr.astype(int) - (40, 160, 80)).sum(axis=2) < 50
        ys, xs = np.where(green)
        self.assertGreater(len(ys), 200)
        self.assertAlmostEqual(float(ys.mean()) / 200, 0.5, delta=0.12)
        self.assertAlmostEqual(float(xs.mean()) / 200, 0.5, delta=0.12)

    def test_split_sheet_centers_each_cell_once(self) -> None:
        sheet = Image.new("RGB", (400, 200), (210, 210, 210))
        px = sheet.load()
        for y in range(10, 40):
            for x in range(10, 40):
                px[x, y] = (40, 160, 80)
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "sheet.jpg"
            out = Path(td) / "cells"
            sheet.save(src, quality=95)
            paths = split_sheet_grid(src, out, rows=2, columns=4, size=80)
            self.assertEqual(len(paths), 8)
            once = cell_to_equal_square(Image.open(src).crop((5, 5, 95, 95)), 80)
            got = Image.open(paths[0])
            self.assertEqual(got.size, once.size)
            self.assertLess(float(np.abs(np.array(got).astype(int) - np.array(once).astype(int)).mean()), 8.0)


if __name__ == "__main__":
    unittest.main()
