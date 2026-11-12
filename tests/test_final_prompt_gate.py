"""最终 Prompt 对账：禁止另写 brief / 手贴。"""
from __future__ import annotations

import unittest

from skills_kit.final_prompt_gate import (
    assert_used_final_prompt,
    final_prompt_sha1,
    format_final_prompt_lines,
    looks_like_hand_pasted_warm_start,
)
from skills_kit.reasonableness_gate import _l0_subject_drift, review_reasonableness
from skills_kit.delivery_gates import generate_prefix


class TestFinalPromptGate(unittest.TestCase):
    def test_sha_and_assert(self) -> None:
        prompt = "soft gloss candy cabinet merge sheet, no text"
        lines = format_final_prompt_lines(prompt)
        self.assertTrue(any(x.startswith("FINAL_PROMPT_SHA1=") for x in lines))
        self.assertEqual(final_prompt_sha1(prompt), lines[0].split("=", 1)[1])
        ok, why = assert_used_final_prompt(prompt, prompt)
        self.assertTrue(ok)
        self.assertEqual(why, "")
        bad, msg = assert_used_final_prompt("another brief I invented", prompt)
        self.assertFalse(bad)
        self.assertIn("不一致", msg)

    def test_hand_paste_detector(self) -> None:
        self.assertTrue(looks_like_hand_pasted_warm_start("请把下面记忆包贴进提示词"))
        self.assertTrue(looks_like_hand_pasted_warm_start("优先复用定稿方向：旧整表"))
        self.assertFalse(looks_like_hand_pasted_warm_start("普通出图句 soft gloss"))


class TestReasonablenessL0(unittest.TestCase):
    def test_subject_anchor_drop(self) -> None:
        draft = "热可可合成梯八档整表，浅色圆角卡，无字无脸"
        revised = "画一张赛博霓虹城市夜景海报，巨大广告牌"
        msg = _l0_subject_drift(draft, revised)
        self.assertIn("主体锚点", msg)

    def test_direction_swap_in_revised(self) -> None:
        draft = "窗边女孩水彩半身写信"
        revised = draft + "；整张改成赛博画风另起炉灶"
        # force checklist ok-ish path via review with force? use helper only
        msg = _l0_subject_drift(draft, revised)
        self.assertIn("换题材", msg)

    def test_review_flags_l0(self) -> None:
        draft = "热可可合成梯八档整表，浅色圆角卡"
        revised = "赛博城市夜景海报霓虹广告牌巨型构图"
        checklist = "\n".join(
            f"{k}: ok" for k in (
                "subject_action",
                "contact_scale",
                "element_budget",
                "hard_locks",
                "fail_at_glance",
                "chain_mode_named",
                "single_item_centered",
                "family_or_base_lock",
                "ladder_read",
            )
        )
        # merge skill may add other issues; just assert L0 appears somewhere when checklist filled
        rev = review_reasonableness(
            skill="ordinary",
            draft=draft,
            revised=revised,
            checklist_text="\n".join(
                f"{k}: ok"
                for k in (
                    "subject_action",
                    "contact_scale",
                    "element_budget",
                    "hard_locks",
                    "fail_at_glance",
                )
            ),
        )
        self.assertFalse(rev["passed"])
        self.assertTrue(any("主体锚点" in x or "换题材" in x for x in rev["issues"]))


class TestGeneratePrefixContractStyle(unittest.TestCase):
    def test_contract_watercolor_opts_out_of_merge_default(self) -> None:
        sess = {
            "goal": "水果合成梯整表一组",
            "route_ids": ["merge.ladder"],
            "merge_delivery": "overview_sheet",
            "understanding_contract": {
                "version": 1,
                "raw_utterance": "水彩风格水果合成梯",
                "l1": {"locks": ["水彩"], "commercial_vibe": ""},
            },
        }
        out = generate_prefix(sess, "eight cell fruit ladder")
        self.assertNotIn("Gossip Harbor 玩具货柜", out)


if __name__ == "__main__":
    unittest.main()
