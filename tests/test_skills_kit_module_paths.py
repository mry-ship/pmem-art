"""Regression: SkillsKit 子模块 paths 必须把自动存/取闸门指到对的位置。"""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULES = ROOT / ".memory" / "modules.yaml"


def _load_registry():
    from pmem.core.registry import ModuleRegistry

    return ModuleRegistry.load(MODULES)


class SkillsKitModulePathsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.reg = _load_registry()
        except ImportError as exc:  # pragma: no cover
            raise unittest.SkipTest(f"pmem 未安装: {exc}") from exc

    def _mid(self, rel: str) -> str | None:
        hit = self.reg.module_for_path(rel)
        return hit.module_id if hit else None

    def test_key_files_land_on_leaf_modules(self):
        expect = {
            "skills_kit/agent_router.py": "feature.SkillsKit.Router",
            "skills_kit/colloquial_lexicon.py": "feature.SkillsKit.Router",
            "skills_kit/converge.py": "feature.SkillsKit.Converge",
            "skills_kit/must_fix.py": "feature.SkillsKit.Converge",
            "skills_kit/delivery_gates.py": "feature.SkillsKit.Converge",
            "skills_kit/local_locks.py": "feature.SkillsKit.Converge",
            "skills_kit/showcase_gate.py": "feature.SkillsKit.Showcase",
            "skills_kit/skill_specs.py": "feature.SkillsKit.Registry",
            "skills_kit/install.py": "feature.SkillsKit.Registry",
            "skills_kit/merge_relation.py": "feature.SkillsKit.MergeLadder",
            "docs/MERGE_MULTI_LENS.md": "feature.SkillsKit.MergeLadder.Relation",
            "skills_kit/export_mode_c_icon.py": "feature.SkillsKit.Icon",
            "skills_kit/alpha_policy.py": "feature.SkillsKit",
            ".agents/skills/pmem-draw/SKILL.md": "feature.SkillsKit.Draw",
            ".agents/skills/pmem-ui/SKILL.md": "feature.SkillsKit.UI",
            ".agents/skills/pmem-icon/SKILL.md": "feature.SkillsKit.Icon",
            ".agents/skills/pmem-merge-ladder/SKILL.md": "feature.SkillsKit.MergeLadder",
            ".agents/skills/pmem-style-lock/SKILL.md": "feature.SkillsKit.StyleLock",
            ".agents/skills/pmem-atlas/SKILL.md": "feature.SkillsKit.Atlas",
            ".agents/skills/pmem-agent/SKILL.md": "feature.SkillsKit.Agent",
            ".agents/skills/pmem-prompt/SKILL.md": "feature.SkillsKit.Prompt",
            ".agents/skills/pmem-critique/SKILL.md": "feature.SkillsKit.Critique",
            ".agents/skills/pmem-coach/SKILL.md": "feature.SkillsKit.Coach",
            ".cursor/skills/pmem-draw/SKILL.md": "feature.SkillsKit.Draw",
        }
        for rel, mid in expect.items():
            with self.subTest(rel=rel):
                self.assertEqual(self._mid(rel), mid)

    def test_all_skills_kit_py_files_are_registered(self):
        missing = []
        for path in sorted((ROOT / "skills_kit").rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if self._mid(rel) is None:
                missing.append(rel)
        self.assertEqual(missing, [], msg=f"未归属模块: {missing}")

    def test_no_path_overlap_errors_on_skills_kit(self):
        from pmem.core.registry import RegistryError

        for path in sorted((ROOT / "skills_kit").rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            rel = path.relative_to(ROOT).as_posix()
            try:
                self.reg.module_for_path(rel)
            except RegistryError as exc:
                self.fail(f"{rel}: {exc}")

    def test_leaf_modules_are_registered_for_writes(self):
        for mid in (
            "feature.SkillsKit.Router",
            "feature.SkillsKit.Converge",
            "feature.SkillsKit.MergeLadder.Relation",
            "feature.SkillsKit.MergeLadder.Delivery",
            "feature.SkillsKit.Prompt",
            "feature.SkillsKit.Critique",
            "feature.SkillsKit.Coach",
        ):
            resolved = self.reg.resolve_module(mid)
            self.assertTrue(resolved.known, msg=mid)
            self.assertEqual(resolved.id, mid)


if __name__ == "__main__":
    unittest.main()
