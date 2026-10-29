"""Ten skills, one /pmem- command each."""
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
    "pmem-prompt",
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
        self.assertIn("固定 **3 稿**", merge_body)
        self.assertIn("不再拉到 8 稿", merge_body)
        self.assertIn("画风已经写成一句", merge_body)
        self.assertIn("合成说不通，仍然不算定稿", merge_body)

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
        self.assertIn("只审一轮", console)
        self.assertNotIn("固定 2 轮", console)
        self.assertIn("查合理性", console)
        self.assertIn("理解错误", console)
        self.assertIn("默认 vs 硬不确定", console)
        self.assertIn("可默认", console)
        self.assertIn("硬不确定", console)
        self.assertIn("禁止**标成「还不确定」来打回", console)
        self.assertIn("依次点名", console)
        self.assertNotIn("不合理的改合理", console)
        self.assertIn("直接执行第二段", console)
        self.assertIn("重新审核一遍", console)
        self.assertIn("确认之前不生图", console)
        self.assertNotIn("定稿是第 2 轮", console)
        self.assertIn("格式不改", console)
        self.assertIn("不能在交出去之前收成一张", console)
        self.assertIn("--reference-image-paths", console)
        self.assertIn("仍按下面停和执行", console)
        self.assertNotIn("和上一句相同才停", console)
        self.assertIn(".cursor/skills/registry.md", console)
        self.assertIn("没有识别到可用技能", console)
        self.assertIn("也不改走普通图", console)
        self.assertIn("普通图排在最后", console)
        self.assertIn("先跑 `tighten`", console)
        self.assertIn("缺一样这步不能开始", console)
        self.assertIn("--contract split", console)
        self.assertIn("skills --install", console)
        self.assertIn("不改派到多图分工", console)
        from skills_kit.skill_registry import build_registry
        reg = build_registry(SKILL_SPECS)
        bodies = {spec["name"]: spec["body"] for spec in SKILL_SPECS}
        self.assertGreaterEqual(len(reg["routes"]), 16)
        for route in reg["routes"]:
            self.assertTrue(route["routable"], route["id"])
            self.assertIn(route["heading"], bodies[route["skill"]], route["id"])
            self.assertFalse(route["simultaneous_pixels"], route["id"])
        joined = "\n".join(route["heading"] + route["when"] + route["id"] for route in reg["routes"])
        for banned in ("局部修", "设定表", "分镜", "姿势锁"):
            self.assertNotIn(banned, joined)

    def test_install_keeps_one_command_per_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            retired = root / ".cursor" / "commands"
            retired.mkdir(parents=True)
            (retired / "art-draw.md").write_text("old", encoding="utf-8")
            (retired / "pmem-concept.md").write_text("old", encoding="utf-8")
            install_skills_and_agent_configs(root, quiet=True)
            skills = {p.name for p in (root / ".cursor" / "skills").iterdir() if p.is_dir()}
            commands = {p.stem for p in (root / ".cursor" / "commands").glob("*.md")}
            self.assertEqual(skills, set(PRIMARY))
            self.assertTrue((root / ".cursor" / "skills" / "registry.json").is_file())
            self.assertTrue((root / ".cursor" / "skills" / "registry.md").is_file())
            self.assertEqual(commands, set(PRIMARY))
            draw = (root / ".cursor" / "commands" / "pmem-draw.md").read_text(encoding="utf-8")
            self.assertIn("合同 · 原画", draw)
            self.assertNotIn("/art-draw", draw)
            overview = (root / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("可默认项直接写入分析", overview)
            self.assertIn("只审一轮", overview)
            self.assertIn("多种情况列出来等玩家确认", overview)
            self.assertNotIn("固定 2 轮", overview)
            self.assertNotIn("定不稳就打回。", overview)
            self.assertIn("依次点名多支", overview)
            rule = (root / ".cursor" / "rules" / "pmem-art.mdc").read_text(encoding="utf-8")
            self.assertIn("可默认项直接写入分析", rule)
            prompt = (root / ".cursor" / "skills" / "pmem-prompt" / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("本技能不生图", prompt)
            rule = (root / ".cursor" / "rules" / "pmem-art.mdc").read_text(encoding="utf-8")
            self.assertIn("按 XX 走了", rule)
            self.assertIn("/pmem-agent", rule)
            self.assertIn("不进克隆", rule)
            self.assertNotIn("/art-", rule)


if __name__ == "__main__":
    unittest.main()
