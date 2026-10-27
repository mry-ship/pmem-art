from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from skills_kit.merge_relation import (
    has_inset_card,
    judge_relation_rows,
    load_phase1,
    parse_rows,
    place_subject_on_square,
)


class MergeRelationTests(unittest.TestCase):
    def test_canonical_phase1_passes(self) -> None:
        yaml_path = (
            Path(__file__).resolve().parents[1]
            / "docs/showcase/skill_full_modes_1027/merge_phase1_canonical.yaml"
        )
        data = load_phase1(yaml_path)
        for tid in ("kitchen", "valentine", "stationery"):
            rows = parse_rows(data["tracks"][tid])
            ok, issues = judge_relation_rows(rows)
            self.assertTrue(ok, f"{tid}: {issues}")

    def test_monotonic_pct_required(self) -> None:
        rows = parse_rows(
            {
                "rows": [
                    {"level": i, "name": f"x{i}", "silhouette": f"s{i}", "scale_pct": 0.6 + i * 0.02, "parts_add": "p" if i > 1 else "—"}
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
                        "scale_pct": 0.6 + i * 0.02,
                        "parts_add": "加光" if i == 2 else ("p" if i > 1 else "—"),
                    }
                    for i in range(1, 9)
                ]
            }
        )
        ok, issues = judge_relation_rows(rows)
        self.assertFalse(ok)
        self.assertTrue(any("L02" in it and "说不通" in it for it in issues))

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


if __name__ == "__main__":
    unittest.main()
