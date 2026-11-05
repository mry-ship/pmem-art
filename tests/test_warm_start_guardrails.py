"""Warm-start injection guardrails: domain taste, keeps, off-topic recipes, redline cap."""
from __future__ import annotations

import unittest
from pathlib import Path

from improve.warm_start import (
    build_warm_start_pack,
    entry_on_topic_for_task,
    filter_habits_for_task,
    filter_keeps_for_task,
    habit_relevant_for_task,
)


class TestTasteDomainFilter(unittest.TestCase):
    def test_candy_merge_ban_does_not_leak_into_ui(self) -> None:
        habit = "黑底整表OK；糖果勿焊蛋糕；加强L1锁与气球档差"
        self.assertFalse(habit_relevant_for_task(habit, "ui.MainMenu", "休闲主菜单 HUD"))
        self.assertFalse(habit_relevant_for_task(habit, "prop.BuildingsMerge.Cute", "建筑合成梯"))

    def test_merge_ladder_species_ban_does_not_leak_into_ui(self) -> None:
        habit = "白底不可接受，要和L1一样透明/黑空底；档差要一眼可辨且体量递增；禁止换物种；零件必须累计"
        self.assertFalse(habit_relevant_for_task(habit, "ui.MainMenu", "主菜单"))
        self.assertTrue(habit_relevant_for_task(habit, "prop.FestivalMerge", "合成梯整表"))

    def test_universal_ban_always_applies(self) -> None:
        self.assertTrue(habit_relevant_for_task("赛博霓虹/霓虹紫", "ui.MainMenu", "主菜单"))
        self.assertTrue(habit_relevant_for_task("廉价塑料感/油腻高光", "prop.BuildingsMerge.Cute", "木屋"))

    def test_candy_ban_kept_for_festival_merge(self) -> None:
        habit = "黑底整表OK；糖果勿焊蛋糕；加强L1锁与气球档差"
        self.assertTrue(habit_relevant_for_task(habit, "prop.FestivalMerge", "糖果合成梯整表"))
        packed = filter_habits_for_task(
            [
                habit,
                "赛博霓虹/霓虹紫",
                "过曝高光",
                "漏抠/黑底/毛边",
                "脏暗阴影/脏色",
                "廉价塑料感/油腻高光",
            ],
            "prop.FestivalMerge",
            "糖果合成梯整表",
            limit=5,
        )
        self.assertTrue(any("糖果" in h for h in packed))

    def test_filter_habits_cap_and_order(self) -> None:
        habits = [
            "黑底整表OK；糖果勿焊蛋糕；加强L1锁与气球档差",
            "赛博霓虹/霓虹紫",
            "过曝高光",
            "漏抠/黑底/毛边",
            "脏暗阴影/脏色",
            "廉价塑料感/油腻高光",
            "错误头身比/头过大",
        ]
        out = filter_habits_for_task(habits, "ui.MainMenu", "主菜单", limit=5)
        self.assertTrue(all("糖果" not in h and "气球" not in h for h in out))
        self.assertLessEqual(len(out), 5)
        # Tail-prefer: newest universal bans survive; candy domain ban is dropped.
        self.assertTrue(any("过曝" in h or "油腻" in h or "头身" in h for h in out))


class TestKeepPhrases(unittest.TestCase):
    def test_keeps_prefer_on_topic(self) -> None:
        keeps = [
            "五链合成：不必每档保留L1原件/母体锁死；同域合理升级、档差明显即可",
            "软塑胶干净分层：宽柔高光+边缘散射，不要油腻镜面",
            "UI顶栏资源与设置同排单行；设置放右上更易点",
        ]
        ui_keeps = filter_keeps_for_task(keeps, "ui.MainMenu", "主菜单概念")
        self.assertTrue(any("顶栏" in k for k in ui_keeps))
        self.assertFalse(any("五链合成" in k for k in ui_keeps))


class TestOffTopicEntries(unittest.TestCase):
    def test_christmas_icon_recipe_dropped_for_softcandy_icon(self) -> None:
        entry = {
            "summary": "[收敛胜出 9.64分] STUNNING 1024 Christmas App Icon remake ginger-braid 暴雪呵气",
            "body": "冰晶碎玻璃+体积暴雪",
            "module": "icon.AppIcon",
        }
        self.assertFalse(
            entry_on_topic_for_task(entry, "icon.AppIcon", "草莓软糖 App Icon 满幅直角")
        )

    def test_softcandy_recipe_kept_for_softcandy_goal(self) -> None:
        entry = {
            "summary": "半透明软糖SSS、宽柔高光、边缘暖散射、籽粒浅凹",
            "body": "草莓软糖黑底居中",
            "module": "prop.CasualBattery",
        }
        self.assertTrue(
            entry_on_topic_for_task(entry, "prop.CasualBattery", "草莓软糖普通图")
        )


class TestBuildPackIntegration(unittest.TestCase):
    def test_pack_filters_bleed_and_caps_redlines(self) -> None:
        root = Path(__file__).resolve().parents[1]
        data = {
            "modules": {"ui.MainMenu": {}, "icon.AppIcon": {}},
            "entries": [
                {
                    "id": "R_XMAS",
                    "kind": "recipe",
                    "module": "icon.AppIcon",
                    "status": "active",
                    "summary": "1024 Christmas App Icon ginger 暴雪呵气 冰晶碎玻璃",
                    "score": 9.64,
                },
                {
                    "id": "R_SOFT",
                    "kind": "recipe",
                    "module": "icon.AppIcon",
                    "status": "active",
                    "summary": "草莓软糖 App Icon 满幅直角 SSS 高饱和",
                    "score": 9.2,
                },
                *[
                    {
                        "id": f"RL{i}",
                        "kind": "style_redline",
                        "module": "ui.MainMenu",
                        "status": "active",
                        "summary": f"主菜单HUD顶栏底栏红线{i}",
                    }
                    for i in range(8)
                ],
            ],
        }
        # Write a temp taste via monkeypatch load? Use real taste filter path by
        # injecting through build with module ui — taste comes from disk.
        # For icon goal, christmas recipe must not appear.
        pack_icon = build_warm_start_pack(
            root, data, module="icon.AppIcon", goal="草莓软糖 App Icon 满幅"
        )
        ids = {r["id"] for r in pack_icon["top_recipes"]}
        self.assertNotIn("R_XMAS", ids)
        self.assertIn("R_SOFT", ids)

        pack_ui = build_warm_start_pack(
            root, data, module="ui.MainMenu", goal="休闲主菜单概念稿"
        )
        self.assertLessEqual(len(pack_ui["top_redlines"]), 3)
        block = pack_ui["prompt_block"]
        self.assertNotIn("糖果勿焊蛋糕", block)
        self.assertNotIn("气球档差", block)
        # constructive keeps section should exist when taste has keeps
        self.assertIn("正向保留", block)


if __name__ == "__main__":
    unittest.main()
