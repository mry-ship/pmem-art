"""User pack must contain pmem-art runtime and must not ship mry-ship/pmem."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from pack_pmem_art import assert_pack_clean, pack  # noqa: E402
from pmem_art import VERSION  # noqa: E402


class TestPackPmemArt(unittest.TestCase):
    def test_zip_has_runtime_without_pmem(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = pack(ROOT, Path(tmp))
            self.assertTrue(zip_path.is_file())
            self.assertIn(str(VERSION).replace(" ", ""), zip_path.name)
            assert_pack_clean(zip_path)
            with zipfile.ZipFile(zip_path) as zf:
                names = zf.namelist()
            self.assertTrue(any(n.endswith("pmem_art.py") for n in names))
            self.assertTrue(any(n.endswith("skills_kit/skill_specs.py") for n in names))
            self.assertTrue(any(n.endswith("skills_kit/route_bank.py") for n in names))
            self.assertTrue(any(n.endswith("skills_kit/data/route_bank.jsonl") for n in names))
            self.assertFalse(any("/.memory/" in n.replace("\\", "/") for n in names))
            self.assertFalse(any(n.endswith("pmem.mdc") for n in names))
            mcp_name = next(n for n in names if n.endswith(".cursor/mcp.json"))
            with zipfile.ZipFile(zip_path) as zf:
                mcp = json.loads(zf.read(mcp_name).decode("utf-8"))
            self.assertIn("pmem-art", mcp.get("mcpServers") or {})
            self.assertNotIn("pmem", mcp.get("mcpServers") or {})


if __name__ == "__main__":
    unittest.main()
