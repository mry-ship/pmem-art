"""Nine skills, one /pmem- command each."""
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
    "pmem-agent",
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
    def test_primary_contracts(self):
        self.assertEqual([s["name"] for s in SKILL_SPECS], PRIMARY)
        self.assertTrue(set(RETIRED_FOLDERS).isdisjoint(s["name"] for s in SKILL_SPECS))

    def test_each_skill_has_one_pmem_command(self):
        for spec in SKILL_SPECS:
            self.assertEqual(command_names(spec), [spec["name"]])
            self.assertNotIn("alias", spec)
            self.assertNotIn("/art-", spec["body"])
        self.assertIn("禁止自动 `accept --all`", _spec("pmem-coach")["body"])

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
        self.assertIn("过程板", draw)
        self.assertIn("converge discuss", _spec("pmem-merge-ladder")["body"])
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
        self.assertIn("--reference-image-paths", draw)
        self.assertIn("不能只看垫进去的那一张就给分", draw)

        console = _spec("pmem-agent")["body"]
        self.assertIn("总控自己不生图", console)
        self.assertIn("两句相同", console)
        self.assertIn("打回给玩家一起矫正", console)
        self.assertIn("不进入第二段", console)
        self.assertIn("格式不改", console)
        self.assertIn("不能在交出去之前收成一张", console)
        self.assertIn("--reference-image-paths", console)
        self.assertIn("停和打回的条件与上面相同", console)
        self.assertNotIn("和上一句相同才停", console)
        for name in PRIMARY:
            if name == "pmem-agent":
                continue
            self.assertIn(f".cursor/skills/{name}/SKILL.md", console)

    def test_install_keeps_one_command_per_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            retired = root / ".cursor" / "commands"
            retired.mkdir(parents=True)
            (retired / "art-draw.md").write_text("old", encoding="utf-8")
            (retired / "pmem-concept.md").write_text("old", encoding="utf-8")
            install_skills_and_agent_configs(root, quiet=True)
            skills = {p.name for p in (root / ".cursor" / "skills").iterdir()}
            commands = {p.stem for p in (root / ".cursor" / "commands").glob("*.md")}
            self.assertEqual(skills, set(PRIMARY))
            self.assertEqual(commands, set(PRIMARY))
            draw = (root / ".cursor" / "commands" / "pmem-draw.md").read_text(encoding="utf-8")
            self.assertIn("合同 · 原画", draw)
            self.assertNotIn("/art-draw", draw)
            rule = (root / ".cursor" / "rules" / "pmem-art.mdc").read_text(encoding="utf-8")
            self.assertIn("按 XX 走了", rule)
            self.assertIn("/pmem-agent", rule)
            self.assertIn("不进克隆", rule)
            self.assertNotIn("/art-", rule)


if __name__ == "__main__":
    unittest.main()
