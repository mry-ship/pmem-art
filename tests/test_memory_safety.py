"""Inbox triage, provisional ranking, and the memory write lock."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _project(td: Path) -> None:
    mem = td / ".memory-art"
    (mem / "entries").mkdir(parents=True)
    (mem / "config.yaml").write_text("project:\n  name: t\n", encoding="utf-8")
    (mem / "modules.yaml").write_text(
        "modules:\n"
        "  character.Hero:\n"
        "    status: active\n"
        "    paths:\n"
        "      - assets/character/hero/**\n"
        "  ui.HUD:\n"
        "    status: active\n"
        "    paths:\n"
        "      - assets/ui/hud/**\n",
        encoding="utf-8",
    )


class TestInboxTriage(unittest.TestCase):
    def test_unspecified_module_waits_then_doctor_files_or_discards(self) -> None:
        import sys

        sys.path.insert(0, str(ROOT))
        from feedback import cmd_feedback
        from lifecycle import cmd_doctor_lifecycle
        from pmem_art import load_project

        td = Path(tempfile.mkdtemp())
        _project(td)
        data = load_project(td)
        rc = cmd_feedback(td, data, "头太大，别这样画", module="", apply=True, silent=True)
        self.assertEqual(rc, 0)
        self.assertTrue(list((td / ".memory-art" / "inbox").glob("*.md")))
        self.assertFalse(list((td / ".memory-art" / "entries").rglob("*.md")))

        cmd_doctor_lifecycle(td, load_project(td))
        self.assertFalse(list((td / ".memory-art" / "inbox").glob("*.md")))
        self.assertTrue(list((td / ".memory-art" / "inbox" / "_discarded").glob("*.md")))
        self.assertFalse(list((td / ".memory-art" / "entries").rglob("*.md")))

        cmd_feedback(
            td,
            load_project(td),
            "character.Hero 这版留着",
            module="",
            apply=True,
            silent=True,
        )
        cmd_doctor_lifecycle(td, load_project(td))
        filed = list((td / ".memory-art" / "entries").rglob("*.md"))
        self.assertEqual(len(filed), 1)
        body = filed[0].read_text(encoding="utf-8")
        self.assertIn("module: character.Hero", body)
        self.assertIn("status: active", body)


class TestConfirmModule(unittest.TestCase):
    def test_child_module_id_is_not_ambiguous_with_parent(self) -> None:
        import sys

        sys.path.insert(0, str(ROOT))
        from lifecycle import confirm_inbox_module

        modules = {
            "character.Hero": {"paths": ["assets/character/**"]},
            "character.Hero.Chibi": {"paths": ["assets/character/hero/chibi/**"]},
        }
        self.assertEqual(
            confirm_inbox_module("character.Hero.Chibi 头太大", "", modules, []),
            "character.Hero.Chibi",
        )
        self.assertEqual(
            confirm_inbox_module("character.Hero.Chibi头太大", "", modules, []),
            "character.Hero.Chibi",
        )
        self.assertEqual(
            confirm_inbox_module("character.Hero头太大", "", {"character.Hero": {}}, []),
            "character.Hero",
        )
        self.assertIsNone(
            confirm_inbox_module("头太大", "assets/character/hero/chibi/a.png", modules, []),
        )
        both = dict(modules)
        both["character.Heroine"] = {"paths": ["assets/character/heroine/**"]}
        self.assertEqual(
            confirm_inbox_module("character.Heroine 这版留着", "", both, []),
            "character.Heroine",
        )
        self.assertIsNone(
            confirm_inbox_module("character.Hero.Sidekick 头太大", "", modules, []),
        )
        self.assertIsNone(
            confirm_inbox_module("对照 character.Hero 与 character.Hero.Sidekick", "", modules, []),
        )
        self.assertIsNone(
            confirm_inbox_module("character.Hero.跟班 头太大", "", modules, []),
        )
        self.assertIsNone(
            confirm_inbox_module("character.Hero_v2 头太大", "", modules, []),
        )
        self.assertIsNone(
            confirm_inbox_module(
                "对照 character.Hero 与 character.Hero.Chibi",
                "",
                modules,
                [],
            ),
        )
        self.assertIsNone(
            confirm_inbox_module(
                "奖励弹窗太花",
                "",
                {"ui.HUD": {}},
                [{"module": "ui.HUD", "aliases": ["弹窗"]}],
            ),
        )


class TestProvisionalRank(unittest.TestCase):
    def test_confirmed_recipe_outranks_higher_provisional(self) -> None:
        import sys

        sys.path.insert(0, str(ROOT))
        from improve import rank_memory_entry

        provisional = {
            "kind": "recipe",
            "status": "provisional",
            "module": "character.Hero",
            "summary": "未达标最高分",
            "score": 9.55,
            "layer_scope": "private",
        }
        confirmed = {
            "kind": "recipe",
            "status": "active",
            "module": "character.Hero",
            "summary": "达标定稿",
            "score": 9.2,
            "layer_scope": "private",
        }
        self.assertGreater(
            rank_memory_entry(confirmed, target_module="character.Hero"),
            rank_memory_entry(provisional, target_module="character.Hero"),
        )


class TestMemoryWriteLock(unittest.TestCase):
    def test_reentrant_lock_does_not_deadlock(self) -> None:
        import sys

        sys.path.insert(0, str(ROOT))
        from lifecycle import memory_write_lock

        td = Path(tempfile.mkdtemp())
        with memory_write_lock(td, timeout_sec=2):
            with memory_write_lock(td, timeout_sec=2):
                self.assertTrue((td / ".memory-art" / "_profile" / "memory_write.lock").is_file())
        with memory_write_lock(td, timeout_sec=2):
            self.assertTrue((td / ".memory-art" / "_profile" / "memory_write.lock").is_file())


if __name__ == "__main__":
    unittest.main()
