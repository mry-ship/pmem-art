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
                    {"level": i, "name": f"x{i}", "silhouette": f"s{i}", "scale_pct": 0.55 + i * 0.03, "parts_add": "p" if i > 1 else "—"}
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

    def test_l8_too_large_fails(self) -> None:
        rows = parse_rows(
            {
                "rows": [
                    {
                        "level": i,
                        "name": f"x{i}",
                        "silhouette": f"s{i}",
                        "scale_pct": 0.58 + i * 0.04,
                        "parts_add": "p" if i > 1 else "—",
                    }
                    for i in range(1, 9)
                ]
            }
        )
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
