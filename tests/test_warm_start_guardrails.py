"""Warm-start injection guardrails: domain taste, keeps, off-topic recipes, redline cap."""
from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from improve.warm_start import (
    build_warm_start_pack,
    collapse_opposed_prefs,
    conflicting_forbid_phrase,
    entry_on_topic_for_task,
    filter_habits_for_task,
    filter_keeps_for_task,
    filter_keeps_with_audit,
    habit_relevant_for_task,
    infer_keep_scopes,
    merge_conflict_taste_phrase,
    normalize_keep_item,
    stale_merge_inject_summary,
    tag_keep_phrase,
    _soft_goal_overlap_ok,
)

_GH_DOG_BLEED_KEEPS = [
    "确认作为货柜正向锚点：合成宣传图里的道具是软立体糖釉玩具货柜，圆润厚实柔光釉面；不要哑光黏土/软塑胶UI。",
    "确认作为渲染正向锚点：加载宣传图证明同一套圆润厚实、无硬描边、暖色辉光加冷色补光。釉面高光接近#FEFDFB。",
    "确认作为风格正向锚点：休闲merge海鲜货柜真机表面——圆润厚实软立体、暖饱和、块面釉面高光、无硬描边；龙虾/蟹/蚝等同店玩具货面；棋盘格可读；",
]


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

    def test_gh_cabinet_keeps_do_not_bleed_into_dog_collage(self) -> None:
        out = filter_keeps_for_task(
            _GH_DOG_BLEED_KEEPS,
            "character.DogCollage",
            "一张2x2多品种狗狗拼板；可爱休闲吉祥物立绘",
        )
        blob = "｜".join(out)
        self.assertEqual(out, [])
        self.assertNotIn("货柜", blob)
        self.assertNotIn("海鲜", blob)
        self.assertNotIn("龙虾", blob)
        self.assertNotIn("糖釉", blob)

    def test_gh_cabinet_keeps_still_ok_for_merge(self) -> None:
        out = filter_keeps_for_task(
            _GH_DOG_BLEED_KEEPS,
            "merge.HarborOrange",
            "Gossip Harbor 货柜合成梯",
        )
        self.assertTrue(any("软立体糖釉" in k or "货柜" in k or "釉面" in k for k in out))

    def test_structured_merge_keep_dropped_for_portrait(self) -> None:
        out = filter_keeps_for_task(
            [{"text": "休闲merge海鲜货柜真机表面", "scopes": ["merge_ladder"]}],
            "character.DogCollage",
            "狗狗拼板",
        )
        self.assertEqual(out, [])

    def test_short_universal_keep_survives_portrait(self) -> None:
        out = filter_keeps_for_task(
            ["柔光圆润", {"text": "干净棚光", "scopes": ["universal"]}],
            "character.DogCollage",
            "狗狗拼板",
        )
        self.assertTrue(any("柔光圆润" in k or "干净棚光" in k for k in out))

    def test_tag_keep_phrase_marks_gh_as_merge(self) -> None:
        tagged = tag_keep_phrase(_GH_DOG_BLEED_KEEPS[0])
        self.assertIn("merge_ladder", tagged.get("scopes") or [])
        self.assertIn("merge_ladder", infer_keep_scopes(_GH_DOG_BLEED_KEEPS[2]))

    def test_audit_reports_dropped_gh_keeps(self) -> None:
        kept, dropped = filter_keeps_with_audit(
            _GH_DOG_BLEED_KEEPS + ["柔光圆润"],
            "character.DogCollage",
            "狗狗拼板",
        )
        self.assertTrue(any("柔光圆润" in k for k in kept))
        self.assertGreaterEqual(len(dropped), 3)
        self.assertTrue(any("货柜" in d or "海鲜" in d or "釉面" in d for d in dropped))

    def test_normalize_keep_item_unions_explicit_and_inferred(self) -> None:
        text, scopes = normalize_keep_item(
            {"text": "柔光圆润休闲merge海鲜货柜", "scopes": ["universal"]}
        )
        self.assertIn("海鲜货柜", text)
        self.assertIn("merge_ladder", scopes)
        self.assertIn("universal", scopes)

    def test_instrument_merge_does_not_get_seafood_cabinet_keeps(self) -> None:
        out = filter_keeps_for_task(
            _GH_DOG_BLEED_KEEPS + ["五链合成：同域合理升级、档差明显即可"],
            "prop.InstrumentMerge",
            "吉他合成梯整表",
        )
        blob = "｜".join(out)
        self.assertNotIn("海鲜", blob)
        self.assertNotIn("龙虾", blob)
        self.assertNotIn("玩具货柜", blob)
        self.assertTrue(any("五链合成" in k for k in out))

    def test_instrument_merge_drops_volume_ladder_ban(self) -> None:
        packed = filter_habits_for_task(
            [
                "白底不可接受，要和L1一样透明/黑空底；档差要一眼可辨且体量递增；禁止换物种；零件必须累计",
                "赛博霓虹/霓虹紫",
            ],
            "prop.InstrumentMerge",
            "吉他合成梯整表",
            limit=5,
        )
        blob = "｜".join(packed)
        self.assertNotIn("体量递增", blob)
        self.assertNotIn("黑空底", blob)
        self.assertTrue(any("赛博" in h for h in packed))

    def test_festival_candy_merge_does_not_get_seafood_keeps(self) -> None:
        out = filter_keeps_for_task(
            _GH_DOG_BLEED_KEEPS + ["五链合成：同域合理升级、档差明显即可"],
            "prop.FestivalMerge",
            "糖果合成梯整表",
        )
        blob = "｜".join(out)
        self.assertNotIn("海鲜", blob)
        self.assertNotIn("龙虾", blob)
        self.assertNotIn("玩具货柜", blob)
        self.assertTrue(any("五链合成" in k for k in out))


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
        self.assertNotIn("RL_KEEP", redline_ids)
        excluded_ids = {
            row.get("id") for row in (pack.get("inject_trace") or {}).get("excluded") or []
        }
        self.assertIn("RL_KEEP", excluded_ids)
        self.assertNotIn("按压喷瓶", pack["prompt_block"])
        # recipes stay on pack for confidence, but must not enter prompt as「优先复用」
        self.assertNotIn("优先复用定稿方向", pack["prompt_block"])
        self.assertNotIn("R_KEEP", pack["prompt_block"])
        self.assertIn("旧 recipe 只参与置信", pack["prompt_block"])

    def test_verified_redline_drops_old_goal(self) -> None:
        root = Path(__file__).resolve().parents[1]
        data = {
            "modules": {"prop.Chest": {}},
            "entries": [
                {
                    "id": "RL_OLD",
                    "kind": "style_redline",
                    "module": "prop.Chest",
                    "status": "active",
                    "trust": "verified",
                    "summary": "[收敛踩坑红线] 金色木箱拱门：避免「塑料高光」",
                }
            ],
        }
        pack = build_warm_start_pack(
            root,
            data,
            module="prop.Chest",
            goal="同风格蓝色品质宝箱",
        )
        block = pack["prompt_block"]
        self.assertIn("避免「塑料高光」", block)
        self.assertNotIn("金色木箱拱门", block)
        self.assertNotIn("优先复用定稿方向", block)

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

    def test_dog_collage_pack_drops_on_disk_gh_keeps(self) -> None:
        """Regression: real taste.json GH cabinet keeps must not enter portrait prompt_block."""
        root = Path(__file__).resolve().parents[1]
        pack = build_warm_start_pack(
            root,
            {"modules": {"character.DogCollage": {}}, "entries": []},
            module="character.DogCollage",
            goal="一张2x2多品种狗狗拼板；可爱休闲游戏吉祥物立绘；无垫图",
        )
        block = pack.get("prompt_block") or ""
        self.assertNotIn("海鲜货柜", block)
        self.assertNotIn("龙虾", block)
        self.assertNotIn("玩具货柜", block)
        self.assertNotIn("#FEFDFB", block)
        self.assertIn("inject_summary", pack)
        self.assertIn("不拦截", pack.get("inject_summary") or "")
        # If disk still has GH keeps, audit must report drops (not silent lose without summary).
        from improve.taste_profile import load_taste

        raw = load_taste(root).get("keep_phrases") or []
        blob = "｜".join(
            (x.get("text") if isinstance(x, dict) else str(x)) for x in raw
        )
        if "货柜" in blob or "海鲜" in blob or "#FEFDFB" in blob:
            self.assertGreaterEqual(len(pack.get("dropped_keeps") or []), 1)


class TestMemoryPollutionTrace(unittest.TestCase):
    """污染记忆要留下排除原因，并且不能进入最终提示词。"""

    def _pack(self, contract: dict | None = None):
        root = Path(__file__).resolve().parents[1]
        data = {
            "modules": {"ui.MainMenu": {}, "merge.Harbor": {}},
            "entries": [
                {
                    "id": "RL_NOTRUST",
                    "kind": "style_redline",
                    "module": "ui.MainMenu",
                    "status": "active",
                    "summary": "[收敛踩坑红线] 旧主菜单金币条：避免「硬描边」",
                },
                {
                    "id": "RL_CAND",
                    "kind": "style_redline",
                    "module": "ui.MainMenu",
                    "status": "active",
                    "trust": "candidate",
                    "summary": "[收敛踩坑红线] 皇家三消骨架：避免「中心圆盘」",
                },
                {
                    "id": "RL_DEAD",
                    "kind": "style_redline",
                    "module": "ui.MainMenu",
                    "status": "superseded",
                    "trust": "verified",
                    "summary": "[收敛踩坑红线] 已废止：主菜单必须留厚金边",
                },
                {
                    "id": "RL_OK",
                    "kind": "style_redline",
                    "module": "ui.MainMenu",
                    "status": "active",
                    "trust": "verified",
                    "summary": "[收敛踩坑红线] 避免「按钮没有按下态」",
                },
                {
                    "id": "AD_OTHER",
                    "kind": "art_decision",
                    "module": "merge.Harbor",
                    "status": "active",
                    "trust": "verified",
                    "summary": "合成梯缺省表面写成港湾货柜缺省句",
                },
                {
                    "id": "AD_FORBID",
                    "kind": "art_decision",
                    "module": "ui.MainMenu",
                    "status": "active",
                    "trust": "verified",
                    "summary": "主菜单骨架直接铺宣传海报",
                },
                {
                    "id": "R_FAIL",
                    "kind": "recipe",
                    "module": "ui.MainMenu",
                    "status": "active",
                    "summary": "失败经验：主菜单沿用旧入口排法",
                },
                {
                    "id": "R_OLD",
                    "kind": "recipe",
                    "module": "ui.MainMenu",
                    "status": "active",
                    "trust": "verified",
                    "summary": "旧档序：主菜单从左到右排八个入口",
                },
            ],
        }
        return build_warm_start_pack(
            root,
            data,
            module="ui.MainMenu",
            goal="休闲主菜单概念稿",
            contract=contract,
        )

    def _reasons(self, pack: dict) -> dict[str, str]:
        return {
            str(row.get("id") or ""): str(row.get("reason") or "")
            for row in (pack.get("inject_trace") or {}).get("excluded") or []
        }

    def test_pollution_cases_stay_out_of_prompt(self) -> None:
        pack = self._pack(
            {"grid": {"keep": [], "vary": [], "forbid": ["宣传海报"], "spec": []}}
        )
        block = pack["prompt_block"]
        reasons = self._reasons(pack)
        self.assertIn("未人工确认", reasons["RL_NOTRUST"])
        self.assertIn("未人工确认", reasons["RL_CAND"])
        self.assertIn("已作废或停用", reasons["RL_DEAD"])
        self.assertIn("其他模块", reasons["AD_OTHER"])
        self.assertIn("宣传海报", reasons["AD_FORBID"])
        self.assertIn("未人工确认", reasons["R_FAIL"])
        self.assertIn("不进提示词", reasons["R_OLD"])
        for token in (
            "旧主菜单金币条",
            "皇家三消",
            "中心圆盘",
            "厚金边",
            "港湾货柜缺省句",
            "宣传海报",
            "失败经验",
            "旧入口排法",
            "从左到右排八个入口",
        ):
            self.assertNotIn(token, block, token)
        self.assertIn("避免「按钮没有按下态」", block)
        self.assertIn("R_OLD", {row["id"] for row in pack["top_recipes"]})
        self.assertNotIn("R_OLD", block)
        self.assertIn("命中 1 条 verified/canonical recipe", pack["confidence_reasons"])
        self.assertNotIn("优先复用定稿方向", block)

    def test_forbid_uses_affirming_clause(self) -> None:
        self.assertEqual(conflicting_forbid_phrase("避免「硬描边」", ["硬描边"]), "")
        self.assertEqual(conflicting_forbid_phrase("严禁硬描边", ["硬描边"]), "")
        self.assertEqual(conflicting_forbid_phrase("别加硬描边", ["硬描边"]), "")
        self.assertEqual(conflicting_forbid_phrase("特别硬描边", ["硬描边"]), "硬描边")
        self.assertEqual(conflicting_forbid_phrase("不要留白要硬描边", ["硬描边"]), "硬描边")
        self.assertEqual(conflicting_forbid_phrase("按钮加硬描边（避免塑料感）", ["硬描边"]), "硬描边")
        self.assertEqual(conflicting_forbid_phrase("避免留白、铺宣传海报", ["宣传海报"]), "宣传海报")
        self.assertEqual(conflicting_forbid_phrase("铺宣传海报，禁止留白", ["宣传海报"]), "宣传海报")
        self.assertEqual(conflicting_forbid_phrase("主菜单按钮加硬描边", ["硬描边"]), "硬描边")
        root = Path(__file__).resolve().parents[1]
        data = {
            "modules": {"ui.MainMenu": {}},
            "entries": [
                {
                    "id": "AD_MIX",
                    "kind": "art_decision",
                    "module": "ui.MainMenu",
                    "status": "active",
                    "trust": "verified",
                    "summary": "铺宣传海报，禁止留白",
                },
                {
                    "id": "RL_ALIGN",
                    "kind": "style_redline",
                    "module": "ui.MainMenu",
                    "status": "active",
                    "trust": "verified",
                    "summary": "[收敛踩坑红线] 避免「硬描边」",
                },
            ],
        }
        contract = {"grid": {"forbid": ["宣传海报", "硬描边"]}}
        with patch(
            "improve.warm_start.load_taste",
            return_value={"keep_phrases": ["主菜单要铺宣传海报"], "banned_habits": []},
        ), patch(
            "improve.knowledge.recall_layered_knowledge_cards",
            return_value=[
                {
                    "id": "CARD_POSTER",
                    "title": "禁止留白",
                    "body": "中心直接铺宣传海报",
                    "layer_scope": "private",
                }
            ],
        ):
            pack = build_warm_start_pack(
                root,
                data,
                module="ui.MainMenu",
                goal="休闲主菜单概念稿",
                contract=contract,
            )
        block = pack["prompt_block"]
        reasons = self._reasons(pack)
        self.assertNotIn("宣传海报", block)
        self.assertIn("宣传海报", reasons["AD_MIX"])
        self.assertIn("宣传海报", reasons["keep:主菜单要铺宣传海报"])
        self.assertIn("宣传海报", reasons["CARD_POSTER"])
        self.assertIn("避免「硬描边」", block)

    def test_missing_grid_does_not_apply_forbid(self) -> None:
        open_pack = self._pack(None)
        self.assertIn("宣传海报", open_pack["prompt_block"])
        self.assertNotIn("AD_FORBID", self._reasons(open_pack))

    def test_verified_other_run_identity_stays_out_of_prompt(self) -> None:
        """已确认记忆仍不得把别的物件、别的交付物或研发记忆写进提示词。"""
        root = Path(__file__).resolve().parents[1]
        data = {
            "modules": {"ui.MainMenu": {}},
            "entries": [
                {
                    "id": "RL_SKU",
                    "kind": "style_redline",
                    "module": "ui.MainMenu",
                    "status": "active",
                    "trust": "verified",
                    "summary": "[收敛踩坑红线] 主菜单按钮：避免「露莓果酱焊上蛋糕」",
                },
                {
                    "id": "AD_SKU",
                    "kind": "art_decision",
                    "module": "ui.MainMenu",
                    "status": "active",
                    "trust": "verified",
                    "summary": "主菜单热可可杯必须留托盘高光",
                },
                {
                    "id": "AD_FAMILY",
                    "kind": "art_decision",
                    "module": "ui.MainMenu",
                    "status": "active",
                    "trust": "verified",
                    "summary": "主菜单图标用 currentColor 描边",
                },
                {
                    "id": "RL_OK2",
                    "kind": "style_redline",
                    "module": "ui.MainMenu",
                    "status": "active",
                    "trust": "verified",
                    "summary": "[收敛踩坑红线] 避免「按钮没有按下态」",
                },
            ],
        }
        with patch(
            "improve.warm_start.load_taste",
            return_value={
                "keep_phrases": ["露莓果酱糖釉高光"],
                "banned_habits": ["不要霓虹", "不要画热可可杯"],
                "preferred_lighting": ["柔光", "HarborHotCocoa暖光"],
            },
        ), patch(
            "improve.knowledge.recall_layered_knowledge_cards",
            return_value=[
                {
                    "id": "CARD_SKU",
                    "title": "主菜单按下态",
                    "body": "不要画成草莓软糖SSS",
                    "layer_scope": "private",
                }
            ],
        ):
            pack = build_warm_start_pack(
                root,
                data,
                module="ui.MainMenu",
                goal="休闲主菜单概念稿",
            )
        block = pack["prompt_block"]
        reasons = self._reasons(pack)
        self.assertIn("他趟具体物件", reasons["RL_SKU"])
        self.assertIn("他趟具体物件", reasons["AD_SKU"])
        self.assertIn("其他交付物", reasons["AD_FAMILY"])
        for token in (
            "露莓果酱",
            "热可可",
            "currentColor",
            "草莓软糖SSS",
            "HarborHotCocoa",
        ):
            self.assertNotIn(token, block, token)
        self.assertIn("避免「按钮没有按下态」", block)
        self.assertIn("不要霓虹", block)
        self.assertIn("柔光", block)

    def test_layer_isolate_prompt_drops_memory_dump(self) -> None:
        from scripts.pmem_layer_split.isolate import _prompt_for

        leaked = _prompt_for(
            {
                "id": "boat",
                "keep": "木船 Warm-Start 候选红线 style_redline",
                "remove": "码头 .memory 收敛踩坑",
            }
        )
        self.assertNotIn("Warm-Start", leaked)
        self.assertNotIn("候选红线", leaked)
        self.assertNotIn("style_redline", leaked)
        self.assertNotIn(".memory", leaked)
        self.assertNotIn("收敛踩坑", leaked)
        self.assertIn("boat", leaked)
        clean = _prompt_for({"id": "boat", "keep": "木船", "remove": "码头"})
        self.assertIn("木船", clean)
        self.assertIn("码头", clean)


if __name__ == "__main__":
    unittest.main()
