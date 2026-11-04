"""Gallery plate rules: finals only; process/ref stay in evolution panel."""
from __future__ import annotations

import unittest

from atlas_index import classify_plate


class TestClassifyPlateGallery(unittest.TestCase):
    def test_round_suffix_is_process(self) -> None:
        for name in (
            "assets/x/r1.png",
            "assets/x/r2_916.png",
            "assets/x/r3_sq.png",
            "assets/x/concept_r1_916.png",
            "assets/x/popcorn_r2.png",
            "assets/x/r1_1024.png",
        ):
            self.assertEqual(classify_plate(name), "process", name)

    def test_style_and_ref_are_reference(self) -> None:
        for name in (
            "assets/skill_battery_20261103/01_style.png",
            "assets/skill_battery_20261103/02_character.png",
            "assets/prop/instrumentmerge/ref_boat_5x3_user.jpg",
            "assets/prop/instrumentmerge/overview_5x3_cursor_refpad.jpg",
            "docs/showcase/x/refs/ref_candy_style.jpg",
        ):
            self.assertEqual(classify_plate(name), "reference", name)

    def test_true_finals_stay_final(self) -> None:
        for name in (
            "assets/scene/merge/L5.png",
            "assets/character/bird/bird_wink_final.png",
            "assets/ui/kit/components_final.png",
            "assets/scene/mergesameobject/L1_final.png",
        ):
            self.assertEqual(classify_plate(name, source="module"), "final", name)

    def test_work_draft_is_process(self) -> None:
        self.assertEqual(
            classify_plate("assets/prop/celadoncandypotionmerge/L1_work.png"),
            "process",
        )


if __name__ == "__main__":
    unittest.main()
