from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
if "fcntl" not in sys.modules:
    sys.modules["fcntl"] = types.ModuleType("fcntl")

from skills_kit.route_bank import distill_entries  # noqa: E402


class TestRouteBankDeliveryTerms(unittest.TestCase):
    def test_merge_delivery_terms_survive_distill(self) -> None:
        entries = distill_entries()
        blob = "\n".join(e.text for e in entries if "merge" in (e.bucket or "") or "merge.ladder" in e.route_ids)
        for term in ("整表", "overview_sheet", "shop_ladder", "per_cell", "一档一张"):
            self.assertIn(term, blob, msg=f"missing delivery term after distill: {term}")


if __name__ == "__main__":
    unittest.main()
