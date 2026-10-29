from __future__ import annotations

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
    place_subject_on_square,
    square_grid_boxes,
)


class MergeRelationTests(unittest.TestCase):
    def test_canonical_phase1_passes(self) -> None:
        yaml_path = (
            Path(__file__).resolve().parents[1]
            / "docs/showcase/skill_full_modes_1027/merge_phase1_canonical.yaml"
        )
        data = load_phase1(yaml_path)
        for tid in ("kitchen", "valentine", "stationery"):
            track = data["tracks"][tid]
            rows = parse_rows(track)
            ok, issues = judge_relation_rows(rows, track=track)
            self.assertTrue(ok, f"{tid}: {issues}")

    def test_monotonic_pct_required(self) -> None:
        rows = parse_rows(
            {
                "rows": [
                    {"level": i, "name": f"x{i}", "silhouette": f"s{i}", "scale_pct": 0.53 + i * 0.03, "parts_add": "p" if i > 1 else "—"}
                    for i in range(1, 9)
                ]
            }
        )
        ok, _ = judge_relation_rows(rows)
        self.assertTrue(ok)

    def test_effect_only_parts_fail(self) -> None:
        rows = parse_rows(
            {
                "rows": [
                    {
                        "level": i,
                        "name": f"x{i}",
                        "silhouette": f"s{i}",
                        "scale_pct": 0.53 + i * 0.03,
                        "parts_add": "加光" if i == 2 else ("p" if i > 1 else "—"),
                    }
                    for i in range(1, 9)
                ]
            }
        )
        ok, issues = judge_relation_rows(rows)
        self.assertFalse(ok)
        self.assertTrue(any("L02" in it and "说不通" in it for it in issues))

    def test_l1_too_large_fails(self) -> None:
        rows = parse_rows(
            {
                "rows": [
                    {
                        "level": i,
                        "name": f"x{i}",
                        "silhouette": f"s{i}",
                        "scale_pct": 0.70 + i * 0.02,
                        "parts_add": "p" if i > 1 else "—",
                    }
                    for i in range(1, 9)
                ]
            }
        )
        ok, issues = judge_relation_rows(rows)
        self.assertFalse(ok)
        self.assertTrue(any("L1" in it and "过大" in it for it in issues))

    def test_family_and_why_required_on_track(self) -> None:
        track = {
            "rows": [
                {
                    "level": i,
                    "name": f"x{i}",
                    "silhouette": f"s{i}",
                    "scale_pct": 0.53 + i * 0.03,
                    "parts_add": "p" if i > 1 else "—",
                }
                for i in range(1, 9)
            ]
        }
        rows = parse_rows(track)
        ok, issues = judge_relation_rows(rows, track=track)
        self.assertFalse(ok)
        self.assertTrue(any("family" in it for it in issues))
        self.assertTrue(any("merge_why" in it for it in issues))

    def test_species_change_with_similarity_passes(self) -> None:
        names = ["鱼苗", "孔雀鱼", "金鱼", "锦鲤", "神仙鱼", "狮子鱼", "龙鱼", "旗鱼"]
        looks = [
            "半透明银灰鱼苗",
            "虹彩帆尾孔雀鱼",
            "橙红圆腹金鱼",
            "白底红黑斑锦鲤",
            "银身黑条神仙鱼",
            "红白条刺鳍狮子鱼",
            "金属金鳞龙鱼",
            "藏青旗鳍旗鱼",
        ]
        track = {
            "family": {"type": "鱼", "style": "卡通侧视"},
            "rows": [
                {
                    "level": i,
                    "name": names[i - 1],
                    "silhouette": f"s{i}",
                    "scale_pct": 0.53 + i * 0.03,
                    "parts_add": "新鳍" if i > 1 else "—",
                    "look": looks[i - 1],
                    "merge_why": "两件上一档合成这一档，同属鱼类" if i > 1 else "",
                    "role": "入门件" if i == 1 else ("展陈件" if i == 8 else "换件"),
                }
                for i in range(1, 9)
            ],
        }
        rows = parse_rows(track)
        ok, issues = judge_relation_rows(rows, track=track)
        self.assertTrue(ok, issues)

    def test_type_only_family_passes(self) -> None:
        track = {
            "family": {"type": "甜点"},
            "rows": [
                {
                    "level": i,
                    "name": f"甜{i}",
                    "silhouette": f"s{i}",
                    "scale_pct": 0.53 + i * 0.03,
                    "parts_add": "新层" if i > 1 else "—",
                    "look": f"本色材质件{i}",
                    "merge_why": "两件上一档合成这一件，同属甜点" if i > 1 else "",
                    "role": "入门件" if i == 1 else ("展陈件" if i == 8 else "换件"),
                }
                for i in range(1, 9)
            ],
        }
        rows = parse_rows(track)
        ok, issues = judge_relation_rows(rows, track=track)
        self.assertTrue(ok, issues)

    def test_family_missing_type_fails(self) -> None:
        track = {
            "family": {"hue": "青绿", "style": "卡通"},
            "rows": [
                {
                    "level": i,
                    "name": f"x{i}",
                    "silhouette": f"s{i}",
                    "scale_pct": 0.53 + i * 0.03,
                    "parts_add": "p" if i > 1 else "—",
                    "merge_why": "两件上一档合成这一件，颜色相似" if i > 1 else "",
                    "role": "入门件" if i == 1 else ("展陈件" if i == 8 else "换件"),
                }
                for i in range(1, 9)
            ],
        }
        rows = parse_rows(track)
        ok, issues = judge_relation_rows(rows, track=track)
        self.assertFalse(ok)
        self.assertTrue(any("type" in it for it in issues))

    def test_same_hue_look_wash_fails(self) -> None:
        track = {
            "family": {"type": "鱼", "hue": "青绿"},
            "rows": [
                {
                    "level": i,
                    "name": f"鱼{i}",
                    "silhouette": f"s{i}",
                    "scale_pct": 0.53 + i * 0.03,
                    "parts_add": "鳍" if i > 1 else "—",
                    "look": "青绿黏土鱼",
                    "merge_why": "两件上一档合成这一件，同属鱼" if i > 1 else "",
                    "role": "入门件" if i == 1 else ("展陈件" if i == 8 else "换件"),
                }
                for i in range(1, 9)
            ],
        }
        rows = parse_rows(track)
        ok, issues = judge_relation_rows(rows, track=track)
        self.assertFalse(ok)
        self.assertTrue(any("同一色" in it or "look 相同" in it for it in issues))

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
        self.assertTrue(any("过大" in it for it in issues))

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


if __name__ == "__main__":
    unittest.main()
