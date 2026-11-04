"""Module path matching must prefer specific globs over broad scaffolds."""
from __future__ import annotations

import unittest

from atlas_index import match_module, path_pattern_score


class ModulePathMatchTests(unittest.TestCase):
    def test_specific_beats_broad_scene_glob(self) -> None:
        modules = {
            "scene.MainArea": {
                "status": "scaffold",
                "paths": ["assets/scene/**"],
                "specs": {"resolution": "1024x576"},
            },
            "scene.CelestialCity": {
                "status": "active",
                "paths": ["assets/scene/celestialcity/**", "assets/scene/celestial_night_city/**"],
                "specs": {"resolution": "720x1280"},
            },
        }
        self.assertEqual(
            match_module("assets/scene/celestial_night_city/e2e_cyber_alley_r1.jpg", modules),
            "scene.CelestialCity",
        )
        self.assertEqual(
            match_module("assets/scene/orphan/foo.jpg", modules),
            "scene.MainArea",
        )

    def test_active_child_beats_parent_same_glob(self) -> None:
        modules = {
            "ui.HUD": {
                "status": "active",
                "paths": ["assets/ui/hud/**", "assets/ui/mainmenu/**"],
            },
            "ui.MainMenu": {
                "status": "active",
                "paths": ["assets/ui/mainmenu/**"],
            },
        }
        self.assertEqual(match_module("assets/ui/mainmenu/r1.jpg", modules), "ui.MainMenu")

    def test_path_pattern_score_orders_specificity(self) -> None:
        self.assertGreater(path_pattern_score("assets/scene/celestialcity/**"), path_pattern_score("assets/scene/**"))


if __name__ == "__main__":
    unittest.main()
