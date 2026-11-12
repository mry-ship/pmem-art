"""Warm-start injection guardrails: domain taste, keeps, off-topic recipes, redline cap."""
from __future__ import annotations

import unittest
from pathlib import Path

from improve.warm_start import (
    build_warm_start_pack,
    collapse_opposed_prefs,
    entry_on_topic_for_task,
    filter_habits_for_task,
    filter_keeps_for_task,
    habit_relevant_for_task,
    merge_conflict_taste_phrase,
    stale_merge_inject_summary,
    _soft_goal_overlap_ok,
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


class TestMergeConflictTaste(unittest.TestCase):
    def test_conflict_phrase_detector(self) -> None:
        self.assertTrue(merge_conflict_taste_phrase("廉价塑料感/油腻高光"))
        self.assertTrue(merge_conflict_taste_phrase("档差要一眼可辨且体量递增"))
        self.assertTrue(merge_conflict_taste_phrase("白底不可接受，要和L1一样透明/黑空底"))
        self.assertTrue(merge_conflict_taste_phrase("不要油腻镜面"))
        self.assertTrue(merge_conflict_taste_phrase("确认作为货柜正向锚点：手绘软渐变糖釉平面货柜感"))
        self.assertTrue(merge_conflict_taste_phrase("黏土渲染休闲手游"))
        self.assertTrue(merge_conflict_taste_phrase("Gossip Harbor 光泽卡通 3D 圆润厚实"))
        self.assertFalse(merge_conflict_taste_phrase("赛博霓虹/霓虹紫"))
        self.assertFalse(merge_conflict_taste_phrase("脏暗阴影/脏色"))
        self.assertFalse(
            merge_conflict_taste_phrase(
                "确认作为货柜正向锚点：软立体糖釉玩具货柜，圆润厚实柔光釉面；不要哑光黏土/软塑胶UI。"
            )
        )

    def test_merge_module_drops_anti_gh_bans(self) -> None:
        habits = [
            "白底不可接受，要和L1一样透明/黑空底；档差要一眼可辨且体量递增；禁止换物种；零件必须累计",
            "廉价塑料感/油腻高光",
            "赛博霓虹/霓虹紫",
            "过曝高光",
            "脏暗阴影/脏色",
        ]
        packed = filter_habits_for_task(
            habits, "merge.GardenWater", "庭院浇水合成梯整表", limit=5
        )
        blob = "｜".join(packed)
        self.assertNotIn("体量递增", blob)
        self.assertNotIn("黑空底", blob)
        self.assertNotIn("廉价塑料", blob)
        self.assertNotIn("油腻高光", blob)
        self.assertTrue(any("赛博" in h or "过曝" in h or "脏暗" in h for h in packed))

    def test_non_merge_keeps_oil_ban(self) -> None:
        packed = filter_habits_for_task(
            ["廉价塑料感/油腻高光", "赛博霓虹/霓虹紫"],
            "ui.MainMenu",
            "主菜单",
            limit=5,
        )
        self.assertTrue(any("油腻" in h for h in packed))

    def test_merge_keeps_drop_matte_satin_and_oil_mirror(self) -> None:
        keeps = [
            "软塑胶干净分层：宽柔高光+边缘散射，不要油腻镜面",
            "哑光缎面；Q版小动物角色",
            "圆润厚实糖釉玩具高光可读",
            "确认作为货柜正向锚点：手绘软渐变糖釉平面货柜感，不要黏土软塑胶立体图标。",
            "确认作为货柜正向锚点：软立体糖釉玩具货柜，圆润厚实柔光釉面；不要哑光黏土/软塑胶UI。",
        ]
        out = filter_keeps_for_task(keeps, "merge.HarborOrange", "Gossip Harbor 货柜")
        blob = "｜".join(out)
        self.assertNotIn("油腻镜面", blob)
        self.assertNotIn("哑光缎面", blob)
        self.assertNotIn("平面货柜", blob)
        self.assertTrue(any("软立体糖釉" in k for k in out))
        self.assertTrue(any("糖釉" in k for k in out))


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

    def test_merge_drops_fairy_garden_keeps(self) -> None:
        keeps = [
            "确认作为风格正向锚点：妖精花园样张可复用日晒草绿#A1B041与叶面绿#658C55铺满草地和巨叶",
            "确认作为货柜正向锚点：合成宣传图里的道具是圆润厚实的糖釉卡通3D。",
            "五链合成：不必每档保留L1原件/母体锁死；同域合理升级、档差明显即可",
        ]
        out = filter_keeps_for_task(keeps, "merge.HarborOrange", "水果合成梯整表一组八档")
        blob = "｜".join(out)
        self.assertNotIn("妖精花园", blob)
        self.assertNotIn("日晒草绿", blob)
        self.assertTrue(any("糖釉" in k or "五链合成" in k for k in out))

    def test_merge_drops_foreign_sku_and_legacy_gloss(self) -> None:
        keeps = [
            "HarborHotCocoa L1 empty thin paper cup 链序留作正向",
            "确认作为货柜正向锚点：光泽卡通 3D、圆润厚实",
            "五链合成：同域合理升级、档差明显即可",
            "软立体糖釉玩具货柜，圆润厚实柔光釉面",
        ]
        out = filter_keeps_for_task(keeps, "merge.HarborOrange", "水果合成梯整表一组八档")
        blob = "｜".join(out)
        self.assertNotIn("HarborHotCocoa", blob)
        self.assertNotIn("光泽卡通 3D", blob)
        self.assertTrue(any("五链合成" in k or "软立体糖釉" in k for k in out))


class TestCollapseOpposedPrefs(unittest.TestCase):
    def test_cold_warm_lighting_keeps_newest_pole(self) -> None:
        vals = ["冷光源", "柔光", "暖光"]
        out = collapse_opposed_prefs(vals, limit=3)
        self.assertTrue(any("暖" in v for v in out))
        self.assertFalse(any(v == "冷光源" for v in out))

    def test_single_pole_unchanged(self) -> None:
        vals = ["柔光", "暖光"]
        out = collapse_opposed_prefs(vals, limit=3)
        self.assertEqual(out, ["柔光", "暖光"])


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

    def test_prop_icon_mushroom_dropped_for_watercolor_portrait(self) -> None:
        entry = {
            "summary": "[收敛胜出 9.36分] prop icon transparent mushroom cheese platter — 真alpha四角透明",
            "body": "厚剪影；红菇芝士果盘身份完整无字",
            "module": "brand.WorldStyle",
        }
        self.assertFalse(
            entry_on_topic_for_task(
                entry, "brand.WorldStyle", "验收出图：画一张窗边水彩半身女孩，缺风格走商业对标"
            )
        )
        # Same recipe stays when the task is actually a prop icon.
        self.assertTrue(
            entry_on_topic_for_task(
                entry, "prop.InstrumentMerge", "prop icon transparent mushroom platter"
            )
        )

    def test_merge_overview_redline_dropped_for_watercolor(self) -> None:
        entry = {
            "summary": "[收敛踩坑红线] merge overview_sheet mushroom ：避免「L2草甸略增景」",
            "body": "",
            "module": "brand.WorldStyle",
        }
        self.assertFalse(
            entry_on_topic_for_task(entry, "brand.WorldStyle", "窗边水彩半身女孩")
        )

    def test_stale_merge_volume_summary_flagged(self) -> None:
        stale = {
            "module": "merge.GardenWater",
            "summary": "[收敛胜出 9.23分] 庭院浇水…保持L3长嘴 只拉开框高0.40 框高阶梯末档最大 纯黑隔离底",
        }
        # 旧闸数字/回退句：原先词表只拦「框高阶梯」整词，漏掉「机读框高约…」「框高L4→」
        measured = {
            "module": "merge.DewberryJam",
            "summary": "[收敛踩坑红线] 避免「机读框高约0.30/0.69/0.81/1.00」",
        }
        regress = {
            "module": "merge.GardenWind",
            "summary": "[收敛踩坑红线] 避免「框高L4→L5回退」",
        }
        keep = {
            "module": "merge.GardenWater",
            "summary": "[收敛胜出 8.9分] 庭院浇水 L3长嘴可读 无书包 浅色圆角卡",
        }
        other = {
            "module": "ui.MainMenu",
            "summary": "主菜单 框高阶梯末档最大 纯黑隔离底",
        }
        self.assertTrue(stale_merge_inject_summary(stale))
        self.assertTrue(stale_merge_inject_summary(measured))
        self.assertTrue(stale_merge_inject_summary(regress))
        self.assertFalse(stale_merge_inject_summary(keep))
        self.assertFalse(stale_merge_inject_summary(other))

    def test_soft_overlap_keeps_generic_redline(self) -> None:
        entry = {
            "summary": "禁止偏离样张画风：霓虹赛博、脏暗阴影",
            "body": "",
            "module": "brand.WorldStyle",
        }
        self.assertTrue(
            _soft_goal_overlap_ok(entry, "窗边水彩半身女孩", module="brand.WorldStyle")
        )

    def test_soft_overlap_drops_scored_foreign_artifact(self) -> None:
        entry = {
            "summary": "[收敛胜出 9.7分] STUNNING 1024 App Icon remake full-bleed",
            "body": "满幅直角商店图标",
            "module": "brand.WorldStyle",
        }
        self.assertFalse(
            _soft_goal_overlap_ok(entry, "窗边水彩半身女孩", module="brand.WorldStyle")
        )
        self.assertTrue(
            _soft_goal_overlap_ok(entry, "做一个 1024 App Icon", module="icon.AppIcon")
        )

    def test_soft_overlap_drops_unscored_foreign_artifact(self) -> None:
        entry = {
            "summary": "下次别再做成 HUD 九宫格顶栏底栏那套",
            "body": "",
            "module": "brand.WorldStyle",
        }
        self.assertFalse(
            _soft_goal_overlap_ok(entry, "窗边水彩半身女孩", module="brand.WorldStyle")
        )

    def test_habit_foreign_artifact_dropped_for_portrait(self) -> None:
        self.assertFalse(
            habit_relevant_for_task(
                "保持 App Icon 满幅直角可读",
                "brand.WorldStyle",
                "窗边水彩半身女孩",
            )
        )
        self.assertTrue(
            habit_relevant_for_task(
                "保持 App Icon 满幅直角可读",
                "icon.AppIcon",
                "1024 App Icon",
            )
        )

    def test_merge_family_habit_not_foreign_to_merge_module(self) -> None:
        habit = "合成梯整表邻档要一眼可辨"
        self.assertTrue(
            habit_relevant_for_task(habit, "merge.DewberryJam", "Gossip Harbor jam ladder")
        )

    def test_keep_foreign_hud_dropped_for_watercolor(self) -> None:
        keeps = filter_keeps_for_task(
            ["主菜单 HUD 顶栏资源条留白", "柔光水彩纸纹"],
            "brand.WorldStyle",
            "窗边水彩半身女孩",
            limit=4,
        )
        self.assertTrue(any("水彩" in k for k in keeps))
        self.assertFalse(any("HUD" in k or "主菜单" in k for k in keeps))


class TestBuildPackIntegration(unittest.TestCase):
    def test_stale_merge_volume_recipe_not_injected(self) -> None:
        root = Path(__file__).resolve().parents[1]
        data = {
            "modules": {"merge.GardenWater": {}},
            "entries": [
                {
                    "id": "R_STALE_VOL",
                    "kind": "recipe",
                    "module": "merge.GardenWater",
                    "status": "active",
                    "summary": "[收敛胜出 9.23分] 庭院浇水 纯黑隔离底 框高阶梯末档最大",
                    "score": 9.23,
                },
                {
                    "id": "R_KEEP",
                    "kind": "recipe",
                    "module": "merge.GardenWater",
                    "status": "active",
                    "summary": "[收敛胜出 8.9分] 庭院浇水 L3长嘴可读 无书包 浅色圆角卡",
                    "score": 8.9,
                },
                {
                    "id": "RL_STALE",
                    "kind": "style_redline",
                    "module": "merge.GardenWater",
                    "status": "active",
                    "summary": "[收敛踩坑红线] 避免「邻档主体框高没有递增」",
                },
                {
                    "id": "RL_STALE_MEASURED",
                    "kind": "style_redline",
                    "module": "merge.GardenWater",
                    "status": "active",
                    "summary": "[收敛踩坑红线] 避免「机读框高约0.30/0.69/0.81/1.00」",
                },
                {
                    "id": "RL_KEEP",
                    "kind": "style_redline",
                    "module": "merge.GardenWater",
                    "status": "active",
                    "summary": "[收敛踩坑红线] 避免「左上变成按压喷瓶」",
                },
            ],
        }
        pack = build_warm_start_pack(
            root,
            data,
            module="merge.GardenWater",
            goal="庭院浇水合成梯整表",
        )
        recipe_ids = {r["id"] for r in pack["top_recipes"]}
        redline_ids = {r["id"] for r in pack["top_redlines"]}
        self.assertNotIn("R_STALE_VOL", recipe_ids)
        self.assertIn("R_KEEP", recipe_ids)
        self.assertNotIn("RL_STALE", redline_ids)
        self.assertNotIn("RL_STALE_MEASURED", redline_ids)
        self.assertIn("RL_KEEP", redline_ids)
        # recipes stay on pack for confidence, but must not enter prompt as「优先复用」
        self.assertNotIn("优先复用定稿方向", pack["prompt_block"])
        self.assertNotIn("R_KEEP", pack["prompt_block"])
        self.assertIn("旧 recipe 只参与置信", pack["prompt_block"])

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
        # constructive keeps section only when on-disk taste still has keep_phrases
        from improve.taste_profile import load_taste
        from improve.warm_start import filter_keeps_for_task

        keeps = filter_keeps_for_task(
            (load_taste(root).get("keep_phrases") or []),
            "ui.MainMenu",
            "休闲主菜单概念稿",
        )
        if keeps:
            self.assertIn("正向保留", block)
        else:
            self.assertNotIn("正向保留", block)


if __name__ == "__main__":
    unittest.main()
