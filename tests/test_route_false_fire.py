"""路由误判：关键词子串、近邻否决、开画闸对不上就停。"""
from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
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
        for text in ("画一张猫，别画成赛博", "不画背景，只要角色"):
            plan = plan_route(text)
            self.assertEqual(plan.route_ids, ["draw.ordinary"], text)
            self.assertNotIn("critique.review", plan.route_ids, text)

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
        self.assertEqual(plan.reason, "unrecognized")

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
            extra, _ = check_route_gate(root, goal=base + "，壬壬壬壬")
            self.assertFalse(extra)
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


if __name__ == "__main__":
    unittest.main()
