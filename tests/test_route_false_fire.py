"""路由误判：关键词子串、近邻否决、开画闸对不上就停。"""
from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from skills_kit.agent_router import Plan, plan_route  # noqa: E402
from skills_kit.agent_router import _SHOWCASE_DEFAULT_FULL  # noqa: E402
from skills_kit.converge import _session_file, cmd_converge  # noqa: E402
from skills_kit.reasonableness_gate import (  # noqa: E402
    apply_review_to_session,
    default_checklist_template,
    review_reasonableness,
    review_skill_matches_routes,
)
from skills_kit.route_bank import advise_route, confidence_for  # noqa: E402
from skills_kit.route_gate import check_route_gate, save_route_advise  # noqa: E402


class RouteFalseFireTests(unittest.TestCase):
    def test_style_constraint_is_not_critique(self) -> None:
        for text in ("画一张猫，别画成赛博", "不画背景，只要角色", "别画背景，只要角色"):
            plan = plan_route(text)
            self.assertEqual(plan.route_ids, ["draw.ordinary"], text)
            self.assertNotIn("critique.review", plan.route_ids, text)

    def test_merge_bare_sheet_or_grow_not_ladder(self) -> None:
        for text in ("把这套道具整表导出一下", "表格整表打印", "越来越大的宝箱", "八档剑"):
            plan = plan_route(text)
            self.assertNotEqual(plan.route_ids, ["merge.ladder"], text)
        for text in (
            "糖果一档比一档大做合成梯",
            "从木剑长到圣剑，八个等级越来越大",
            "合成梯整表一组出齐",
            "逐格出八档鸟",
            "越升越大那条剑",
        ):
            plan = plan_route(text)
            self.assertEqual(plan.route_ids, ["merge.ladder"], text)

    def test_bare_concept_sketch_not_keyart(self) -> None:
        plan = plan_route("给我一张概念图")
        self.assertEqual(plan.route_ids, ["draw.ordinary"])
        plan_key = plan_route("一张概念海报，当主视觉")
        self.assertEqual(plan_key.route_ids, ["draw.key"])

    def test_icon_set_asks_abc(self) -> None:
        plan = plan_route("一套图标")
        self.assertEqual(plan.mode, "stop")
        self.assertEqual(plan.reason, "icon_unspecified")

    def test_style_verify_phrases_chain_clone(self) -> None:
        for text in ("锁完出图", "锁完再画", "锁风验证"):
            plan = plan_route(text, images=["ref/style.png"])
            self.assertEqual(plan.route_ids, ["style.lock", "draw.clone"], text)
            self.assertEqual(plan.reason, "style_then_clone", text)
        # 「以后都用…生图」只锁风，不串克隆
        only = plan_route("以后都用这张生图", images=["ref/style.png"])
        self.assertEqual(only.route_ids, ["style.lock"])
        self.assertEqual(only.reason, "style")
        # 裸「验证图」当题材名 ≠ 锁风验证串
        sketch = plan_route("画一张验证图普通猫")
        self.assertEqual(sketch.route_ids, ["draw.ordinary"])

    def test_named_seed_refuses_stop_jobs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ok, msg = check_route_gate(
                root,
                goal="序列帧动画",
                expect_route="draw.ordinary",
            )
            self.assertFalse(ok, msg)
            self.assertIn("stop", msg)
            # 规则已判 style→clone 时，禁止种成普通图
            ok2, msg2 = check_route_gate(
                root,
                goal="锁完出图",
                expect_route="draw.ordinary",
            )
            self.assertFalse(ok2, msg2)
            self.assertIn("不一致", msg2)

    def test_merge_negation_and_grow_without_ladder(self) -> None:
        for text in (
            "宝箱越来越大没有合成",
            "越升越大的太阳",
            "这颗星越升越大",
            "太阳越来越大一档光",
            "export整表overview",
            "八档鸟但没有合成梯",
            "不要合成梯八档剑",
        ):
            plan = plan_route(text)
            self.assertNotEqual(plan.route_ids, ["merge.ladder"], text)
            advised = advise_route(text)
            self.assertNotEqual(advised.get("vague_reason"), "artist_ask_merge", text)
            self.assertNotIn("merge.ladder", advised.get("route_ids") or [])
        # advise 也不要因裸「越升越大」逼问合成梯
        advised = advise_route("越升越大的太阳")
        self.assertNotEqual(advised.get("vague_reason"), "artist_ask_merge")
        self.assertNotIn("merge.ladder", advised.get("route_ids") or [])

    def test_guiwei_in_frame_is_not_atlas(self) -> None:
        plan = plan_route("角色归位到画面中心，出一张立绘")
        self.assertEqual(plan.route_ids, ["draw.ordinary"])

    def test_bare_l1_is_not_merge(self) -> None:
        plan = plan_route("L1缓存示意图")
        self.assertNotEqual(plan.route_ids, ["merge.ladder"])

    def test_key_art_smile_stays_key(self) -> None:
        plan = plan_route("画个主视觉，人物微笑，气氛图")
        self.assertEqual(plan.route_ids, ["draw.key"])

    def test_style_lock_plus_draw_chains_clone(self) -> None:
        plan = plan_route("以后都用暖色，画一张猫", images=["ref/style.png"])
        self.assertEqual(plan.route_ids, ["style.lock", "draw.clone"])

    def test_future_palette_only_stays_lock(self) -> None:
        plan = plan_route("往后出图都用这张的色板", images=["ref/style.png"])
        self.assertEqual(plan.route_ids, ["style.lock"])

    def test_style_lock_an_zhe_not_folded_to_ordinary(self) -> None:
        from skills_kit.route_normalize import normalize_for_route

        for text in ("以后按这张画", "以后都按这张画风", "都按这张色板"):
            self.assertIn("按这张", normalize_for_route(text), text)
            plan = plan_route(text, images=["ref/style.png"])
            self.assertEqual(plan.route_ids, ["style.lock"], text)
            self.assertEqual(plan.reason, "style", text)
        # 无样张：plan 仍是锁风格，advise 层再问贴图（不是普通图）
        plan_bare = plan_route("以后按这张画")
        self.assertEqual(plan_bare.route_ids, ["style.lock"])
        advised = advise_route("以后按这张画")
        self.assertFalse(advised["execute_ok"])
        self.assertEqual(advised.get("confidence"), "ask")

    def test_ref_fold_still_works_for_ordinary_pad(self) -> None:
        from skills_kit.route_normalize import normalize_for_route

        folded = normalize_for_route("按这张画一张窗边女孩")
        self.assertIn("参考这张", folded)
        self.assertNotIn("按这张", folded)

    def test_non_art_ops_stop_not_ordinary(self) -> None:
        for text in (
            "检查分析下技能是否有问题",
            "审计一下技能文档",
            "跑一下单元测试",
            "修一下 converge bug",
            "你再深度检查下整个项目是否还有什么漏洞bug，问题",
            "详细检查是否哪里有漏洞bug",
            "帮我看看有没有 bug",
            "帮我看看有没有 bugs",
            "fix the bugs",
            "审计一下 hooks",
            "审计一下 hook",
            "看看 agent_router 有没有坑",
            "检查角色代码有没有 bug",
            "看看报错比例",
            "a little bug in the renderer",
            "withdraw a bug from the backlog",
            "深度检查整个项目",
            "再查一遍仓库",
            "审计一下整个项目",
            "review the code",
            "code review this module",
        ):
            plan = plan_route(text)
            self.assertEqual(plan.mode, "stop", text)
            self.assertEqual(plan.reason, "unrecognized", text)
            self.assertEqual(plan.route_ids, [], text)
            advised = advise_route(text)
            self.assertFalse(advised["execute_ok"], text)

    def test_dev_ops_gate_keeps_draw_and_review(self) -> None:
        keep = {
            "draw a cute bug": "draw.ordinary",
            "a pile of fish hooks": "draw.ordinary",
            "画一只 bug 怪物": "draw.ordinary",
            "用这个技能画一张猫": "draw.ordinary",
            "clip the character": "draw.ordinary",
            "review the lighting": "draw.ordinary",
            "简单测试一下这个姿势": "draw.ordinary",
            "使用例子说明构图": "draw.ordinary",
            "写个角色脚本": "draw.ordinary",
            "函数曲线不好看": "draw.ordinary",
            "脸哪里不对": "draw.ordinary",
            "都按这张画一张窗边女孩": "draw.ordinary",
        }
        for text, rid in keep.items():
            plan = plan_route(text, images=["a.png"] if "这张" in text or "窗边" in text else None)
            self.assertNotEqual(plan.reason, "unrecognized", text)
            self.assertEqual(plan.route_ids, [rid], text)

    def test_accept_knowledge_card_is_coach(self) -> None:
        plan = plan_route("把这条知识卡收下")
        self.assertEqual(plan.route_ids, ["coach.report"])

    def test_bare_rerun_asks_instead_of_full_pack(self) -> None:
        for text in ("再跑一遍这张猫", "同范围"):
            plan = plan_route(text)
            self.assertEqual(plan.mode, "stop", text)
            self.assertEqual(plan.reason, "showcase_unspecified", text)
            self.assertLess(len(plan.route_ids), 2, text)

    def test_named_ordinary_rerun_is_one_skill(self) -> None:
        plan = plan_route("这张普通图再跑一遍")
        self.assertEqual(plan.route_ids, ["draw.ordinary"])

    def test_keep_and_swap_stops(self) -> None:
        plan = plan_route("有参考图；题材不变但换成一只猫；走普通图")
        self.assertEqual(plan.mode, "stop")
        self.assertEqual(plan.reason, "hard_ambiguity")

    def test_draw_umbrella_still_sees_merge(self) -> None:
        plan = plan_route("/pmem-draw 做一条合成梯，一档比一档大")
        self.assertEqual(plan.route_ids, ["merge.ladder"])

    def test_negation_on_the_right_releases_job(self) -> None:
        plan = plan_route("序列帧不要，就一张")
        self.assertNotEqual(plan.reason, "unrecognized")
        self.assertEqual(plan.route_ids, ["draw.ordinary"])

    def test_storyboard_feel_is_not_the_job(self) -> None:
        plan = plan_route("分镜感强一点的主视觉")
        self.assertNotEqual(plan.reason, "unrecognized")
        self.assertEqual(plan.route_ids, ["draw.key"])

    def test_real_storyboard_still_stops(self) -> None:
        plan = plan_route("帮我做分镜，第0件")
        self.assertEqual(plan.reason, "job_ask")

    def test_neighbor_disagreement_is_low(self) -> None:
        plan = Plan(
            mode="skill",
            would_execute=True,
            execute=False,
            reason="atlas",
            announce="",
            route_ids=["atlas.file"],
        )
        conf = confidence_for(
            plan,
            [{"route_ids": ["draw.ordinary"], "mode": "default", "score": 1.28, "text": "画一张"}],
        )
        self.assertEqual(conf, "low")

    def test_goal_mismatch_and_route_id_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = advise_route("画一张水彩半身的窗边女孩")
            self.assertTrue(payload["execute_ok"])
            save_route_advise(root, payload, text="画一张水彩半身的窗边女孩", conversation_id="conv-a")
            ok, _ = check_route_gate(root, goal="画一张水彩半身的窗边女孩", conversation_id="conv-a")
            self.assertTrue(ok)
            bad, msg = check_route_gate(root, goal="合成梯八档软糖", conversation_id="conv-a")
            self.assertFalse(bad)
            self.assertIn("对不上", msg)
            wrong, msg2 = check_route_gate(
                root,
                goal="画一张水彩半身的窗边女孩",
                expect_route="merge.ladder",
                conversation_id="conv-a",
            )
            self.assertFalse(wrong)
            self.assertIn("merge.ladder", msg2)
            foreign, _ = check_route_gate(
                root, goal="画一张水彩半身的窗边女孩", conversation_id="conv-b"
            )
            self.assertFalse(foreign)
            anon, _ = check_route_gate(root, goal="画一张水彩半身的窗边女孩")
            self.assertFalse(anon)

    def test_conversation_route_does_not_poison_global_last_advise(self) -> None:
        """带 conversation 的 route 只写分槽，并发时不覆盖全局 last_advise。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            save_route_advise(
                root,
                {
                    "banner": "【按 普通图 走了】",
                    "route_ids": ["draw.ordinary"],
                    "mode": "default",
                    "execute_ok": True,
                },
                text="画一张猫",
            )
            global_before = (root / ".memory-art" / "route_bank" / "last_advise.json").read_text(
                encoding="utf-8"
            )
            save_route_advise(
                root,
                {
                    "banner": "【按 合成梯 走了】",
                    "route_ids": ["merge.ladder"],
                    "mode": "skill",
                    "execute_ok": True,
                },
                text="软糖合成梯八档",
                conversation_id="conv-merge",
            )
            global_after = (root / ".memory-art" / "route_bank" / "last_advise.json").read_text(
                encoding="utf-8"
            )
            self.assertEqual(global_before, global_after)
            ok_m, _ = check_route_gate(
                root, goal="软糖合成梯八档", conversation_id="conv-merge", expect_route="merge.ladder"
            )
            self.assertTrue(ok_m)
            ok_g, _ = check_route_gate(root, goal="画一张猫", expect_route="draw.ordinary")
            self.assertTrue(ok_g)
            # 有 cid 但无分槽：禁止回落全局（即使全局无 owner）
            leak, msg_leak = check_route_gate(
                root, goal="画一张猫", conversation_id="conv-other"
            )
            self.assertFalse(leak, msg_leak)
            self.assertIn("缺少本地路由", msg_leak)

    def test_expired_route_id_conflict_refuses_silent_reseed(self) -> None:
        """过期缓存与本次 --route-id 不一致时禁止静默换路由。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            save_route_advise(
                root,
                {
                    "banner": "【按 合成梯 走了】",
                    "route_ids": ["merge.ladder"],
                    "mode": "skill",
                    "execute_ok": True,
                },
                text="软糖合成梯八档",
                conversation_id="conv-exp",
            )
            slot = root / ".memory-art" / "route_bank" / "by_conversation" / "conv-exp.json"
            blob = json.loads(slot.read_text(encoding="utf-8"))
            blob["saved_at"] = time.time() - (3 * 60 * 60)
            slot.write_text(json.dumps(blob, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            ok, msg = check_route_gate(
                root,
                goal="画一张水彩窗边女孩",
                expect_route="draw.ordinary",
                conversation_id="conv-exp",
            )
            self.assertFalse(ok, msg)
            self.assertIn("静默换路由", msg)
            self.assertIn("merge.ladder", msg)

    def test_expanded_goal_matches_shorter_route_text(self) -> None:
        """开画 goal 比 route 原文更长时，只要 route 锚点都在 goal 里就放行。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            save_route_advise(
                root,
                {
                    "banner": "【按 普通图 走了】",
                    "route_ids": ["draw.ordinary"],
                    "mode": "default",
                    "execute_ok": True,
                },
                text="画一张水彩窗边女孩",
                conversation_id="conv-draw",
            )
            long_goal = (
                "画一张水彩窗边女孩半身立绘；柔光；无字；休闲商业气质；"
                "不要赛博；交给 converge start"
            )
            ok, msg = check_route_gate(
                root,
                goal=long_goal,
                conversation_id="conv-draw",
                expect_route="draw.ordinary",
            )
            self.assertTrue(ok, msg)

    def test_negated_showcase_does_not_pull_full_pack(self) -> None:
        full = list(_SHOWCASE_DEFAULT_FULL)
        stopped = plan_route("整页展陈，不要全部重跑")
        self.assertNotEqual(stopped.route_ids, full)
        self.assertEqual(stopped.mode, "stop")
        cat = plan_route("不同范围再画一张猫")
        self.assertNotEqual(cat.route_ids, full)
        self.assertEqual(cat.route_ids, ["draw.ordinary"])
        named = plan_route("不要全部重跑。对比页把界面和合成梯再跑")
        self.assertEqual(named.route_ids, ["ui.kit", "merge.ladder"])
        kept = plan_route("全部重跑 homepage_rerun_1028 同范围")
        self.assertEqual(kept.route_ids, full)

    def test_goal_chunk_past_eight_and_long_text(self) -> None:
        parts = ["甲甲甲甲", "乙乙乙乙", "丙丙丙丙", "丁丁丁丁", "戊戊戊戊", "己己己己", "庚庚庚庚", "辛辛辛辛"]
        base = "，".join(parts)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            save_route_advise(
                root,
                {"route_ids": ["draw.ordinary"], "mode": "default", "execute_ok": True, "banner": "ok"},
                text=base,
            )
            # 同题扩写（route 原文仍在 goal 里）→ 放行
            expand, msg_e = check_route_gate(root, goal=base + "，柔光无字商业气质")
            self.assertTrue(expand, msg_e)
            # 换题 → 拦截
            drift, msg_d = check_route_gate(root, goal="合成梯八档软糖整表一组")
            self.assertFalse(drift, msg_d)
            self.assertIn("对不上", msg_d)
            long_text = "画一张猫" + ("甲" * 600)
            save_route_advise(
                root,
                {"route_ids": ["draw.ordinary"], "mode": "default", "execute_ok": True, "banner": "ok"},
                text=long_text,
            )
            same, _ = check_route_gate(root, goal=long_text)
            self.assertTrue(same)

    def test_generate_uses_latest_route_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data: dict = {"config": {"converge": {}}}
            save_route_advise(
                root,
                {"route_ids": ["draw.ordinary"], "mode": "default", "execute_ok": True, "banner": "ok"},
                text="画一张猫",
                conversation_id="conv-gen",
            )
            rc = cmd_converge(
                root,
                data,
                "start",
                session_id="gen-route",
                goal="画一张猫",
                module="brand.WorldStyle",
                conversation_id="conv-gen",
            )
            self.assertEqual(rc, 0)
            sf = _session_file(root, "gen-route")
            sess = json.loads(sf.read_text(encoding="utf-8"))
            rev = (
                "青瓷小猫蹲坐捧茶盏，爪与盏接触清楚；背景最多一扇窗；"
                "竖构图无字；一眼失败是多爪或茶盏漂浮。"
            )
            review = review_reasonableness(
                skill="ordinary",
                draft="青瓷小猫",
                revised=rev,
                checklist_text=default_checklist_template("ordinary"),
            )
            self.assertTrue(review["passed"], review["issues"])
            sess = apply_review_to_session(sess, review)
            sf.write_text(json.dumps(sess, ensure_ascii=False, indent=2), encoding="utf-8")
            save_route_advise(
                root,
                {"route_ids": ["style.lock"], "mode": "skill", "execute_ok": True, "banner": "ok"},
                text="画一张猫",
                conversation_id="conv-gen",
            )
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc2 = cmd_converge(
                    root,
                    data,
                    "generate",
                    session_id="gen-route",
                    round_num=1,
                    prompt="青瓷小猫",
                    conversation_id="conv-gen",
                )
            self.assertEqual(rc2, 1)
            self.assertIn("不一致", buf.getvalue())

    def test_palette_phrase_without_a_drawing_stays_lock(self) -> None:
        plan = plan_route("以后都用这张色板出图", images=["ref/style.png"])
        self.assertEqual(plan.route_ids, ["style.lock"])

    def test_review_skill_must_match_route(self) -> None:
        self.assertTrue(review_skill_matches_routes("ordinary", ["draw.ordinary"]))
        self.assertFalse(review_skill_matches_routes("ui", ["draw.ordinary"]))
        self.assertFalse(review_skill_matches_routes("foo", ["draw.ordinary"]))
        self.assertFalse(review_skill_matches_routes("ordinary", ["style.lock"]))
        self.assertTrue(review_skill_matches_routes("ordinary", []))
        plan = plan_route("帮我归档这些散图")
        self.assertEqual(plan.route_ids, ["atlas.file"])

    def test_all_skills_sentence_is_full_inventory(self) -> None:
        text = "把所有技能以及技能变体全部跑一遍"
        plan = plan_route(text)
        self.assertEqual(plan.reason, "skill_suite")
        self.assertIn("draw.ordinary", plan.route_ids)
        self.assertIn("icon.b", plan.route_ids)
        self.assertIn("merge.ladder", plan.route_ids)
        self.assertGreaterEqual(len(plan.route_ids), 8)
        advised = advise_route(text)
        self.assertTrue(advised["execute_ok"], advised.get("artist_say"))

    def test_variant_huancheng_stays_variant(self) -> None:
        text = "同一身份；换表情；机位已在图上；走变体。这个妖精换成惊讶睁大眼。"
        plan = plan_route(text, images=["a.png"])
        self.assertEqual(plan.route_ids, ["draw.variant"])
        advised = advise_route(text, images=["a.png"])
        self.assertTrue(advised["execute_ok"], advised.get("confidence"))
        clone = plan_route("参考这张，变成微笑的猫", images=["a.png"])
        self.assertEqual(clone.route_ids, ["draw.clone"])


if __name__ == "__main__":
    unittest.main()
