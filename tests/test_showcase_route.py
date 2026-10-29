from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
if "fcntl" not in sys.modules:
    sys.modules["fcntl"] = types.ModuleType("fcntl")

from skills_kit.agent_router import (  # noqa: E402
    _SHOWCASE_DEFAULT_FULL,
    _showcase_ids,
    plan_route,
)


class ShowcaseRouteTests(unittest.TestCase):
    def test_full_rerun_defaults_same_scope_pack(self) -> None:
        ids = _showcase_ids("全部重跑 homepage_rerun_1028")
        self.assertEqual(ids, list(_SHOWCASE_DEFAULT_FULL))
        plan = plan_route("全部重跑 homepage_rerun_1028 同范围")
        self.assertEqual(plan.reason, "showcase")
        self.assertTrue(plan.would_execute)
        self.assertEqual(plan.route_ids, list(_SHOWCASE_DEFAULT_FULL))

    def test_empty_compare_page_still_stops(self) -> None:
        plan = plan_route("做一页对比页，没写重跑哪几支")
        self.assertEqual(plan.reason, "showcase_unspecified")
        self.assertEqual(plan.mode, "stop")

    def test_clone_variant_probes(self) -> None:
        plan = plan_route("同范围重跑：克隆和变体都重跑")
        self.assertEqual(plan.reason, "showcase")
        self.assertEqual(plan.route_ids, ["draw.clone", "draw.variant"])

    def test_style_prompt_probes(self) -> None:
        plan = plan_route("整页展陈把锁风格和提示词也重跑")
        self.assertEqual(plan.reason, "showcase")
        self.assertIn("style.lock", plan.route_ids)
        self.assertIn("prompt.write", plan.route_ids)


if __name__ == "__main__":
    unittest.main()
