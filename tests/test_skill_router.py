"""Merged skill list: one router, old slash names stay locked to a branch."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from skills_kit.install import command_names, install_skills_and_agent_configs
from skills_kit.prompt_scale import DEFAULT_MAX_ROUNDS
from skills_kit.skill_specs import SKILL_SPECS


PRIMARY = [
    "pmem-draw",
    "pmem-style-lock",
    "pmem-critique",
    "pmem-atlas",
    "pmem-ui",
    "pmem-icon",
    "pmem-coach",
    "pmem-merge-ladder",
]

RETIRED_FOLDERS = [
    "pmem-concept",
    "pmem-clone-image",
    "pmem-variant",
    "pmem-lens-propose",
    "pmem-improve",
    "pmem-learn",
    "art-merge",
    "art-draw",
]


def _spec(name: str) -> dict:
    return next(s for s in SKILL_SPECS if s["name"] == name)


class SkillRouterTests(unittest.TestCase):
    def test_eight_primary_contracts(self):
        self.assertEqual([s["name"] for s in SKILL_SPECS], PRIMARY)
        self.assertTrue(set(RETIRED_FOLDERS).isdisjoint(s["name"] for s in SKILL_SPECS))

    def test_old_slash_names_lock_a_single_branch(self):
        draw = _spec("pmem-draw")
        self.assertEqual(
            command_names(draw),
            [
                "pmem-draw",
                "art-draw",
                "pmem-concept",
                "art-concept",
                "pmem-clone-image",
                "art-clone",
                "pmem-variant",
                "art-variant",
                "pmem-lens-propose",
                "art-lens",
            ],
        )
        self.assertEqual(draw["alias_routes"]["pmem-concept"], "原画")
        self.assertEqual(draw["alias_routes"]["pmem-clone-image"], "克隆")
        self.assertEqual(draw["alias_routes"]["art-variant"], "变体")
        self.assertEqual(draw["alias_routes"]["art-lens"], "镜头包")
        self.assertNotIn("art-draw", draw["alias_routes"])

        coach = _spec("pmem-coach")
        self.assertEqual(coach["alias_routes"]["pmem-learn"], "知识")
        self.assertIn("禁止自动 `accept --all`", coach["body"])

        merge = _spec("pmem-merge-ladder")
        self.assertEqual(command_names(merge), ["pmem-merge-ladder", "art-ladder", "art-merge"])
        self.assertEqual(merge["alias_routes"]["art-ladder"], "合成梯")
        self.assertEqual(merge["alias_routes"]["art-merge"], "合成梯")

    def test_router_safety_gates_stay_in_the_contract(self):
        draw = _spec("pmem-draw")["body"]
        self.assertIn("不再让人选技能", draw)
        self.assertIn("有参考，但没说新题材", draw)
        self.assertIn("不进镜头包", draw)
        self.assertIn("不要在本文件生图", draw)
        self.assertIn("合同 · 克隆", draw)
        self.assertIn("每一轮都垫最初那张风格参考", draw)
        self.assertIn("内容区回声了参考主体", draw)
        self.assertIn("禁止在这一步生图", draw)
        self.assertIn("克隆和变体仍用第二节", draw)
        self.assertNotIn("可主动提议跑", draw)
        self.assertEqual(DEFAULT_MAX_ROUNDS, 4)
        self.assertIn("最多 4 轮", draw)
        self.assertNotIn("最多 8 轮", draw)
        merge_body = _spec("pmem-merge-ladder")["body"]
        self.assertIn("最多改 **8 稿**", merge_body)
        self.assertIn("合成说不通，仍然不算定稿", merge_body)
        self.assertIn("不能拿来缩短这里", merge_body)

        merge = _spec("pmem-merge-ladder")["body"]
        self.assertIn("relation-judge", merge)
        self.assertIn("exit 0 才能出图", merge)
        self.assertIn("体量预览", merge)
        self.assertIn("不要把参考图文件垫进生图", merge)
        self.assertIn("scale_pct", merge)
        self.assertIn("L1 ≥ 0.58", merge)
        self.assertIn("parts_add", merge)
        self.assertIn("不要改掉这份 canonical 里已有的 track", merge)
        self.assertIn("再跑一次 audit", merge)
        self.assertNotIn("一次生成整梯 contact sheet", merge)
        self.assertIn("有参考又要换题材的这一张，走克隆", draw)

    def test_install_keeps_one_skill_folder_and_locks_old_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install_skills_and_agent_configs(root, quiet=True)
            skills = {p.name for p in (root / ".cursor" / "skills").iterdir()}
            self.assertEqual(skills, set(PRIMARY))
            concept = (root / ".cursor" / "commands" / "pmem-concept.md").read_text(encoding="utf-8")
            self.assertIn("点名锁定", concept)
            self.assertIn("原画", concept)
            self.assertIn("合同 · 原画", concept)
            ladder = (root / ".cursor" / "commands" / "art-ladder.md").read_text(encoding="utf-8")
            self.assertIn("合成梯", ladder)
            self.assertIn("exit 0 才能出图", ladder)
            rule = (root / ".cursor" / "rules" / "pmem-art.mdc").read_text(encoding="utf-8")
            self.assertIn("按 XX 走了", rule)
            self.assertIn("不进克隆", rule)


if __name__ == "__main__":
    unittest.main()
