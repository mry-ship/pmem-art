"""100 句美术白话 → advise_route 匹配比对（高准确率门禁）。"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from skills_kit.colloquial_lexicon import load_lexicon, packaged_path  # noqa: E402
from skills_kit.route_bank import advise_route  # noqa: E402

CASES_PATH = ROOT / "skills_kit" / "data" / "artist_talk_100.jsonl"
ACCURACY_FLOOR = 1.0  # 100 句白话全对；口语扩展后认路门禁


def _load_cases() -> list[dict]:
    rows: list[dict] = []
    for line in CASES_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


class ColloquialLexiconTests(unittest.TestCase):
    def test_lexicon_at_least_8000(self) -> None:
        table = load_lexicon()
        self.assertGreaterEqual(len(table), 8000)
        self.assertTrue(packaged_path().is_file())


class ArtistTalkAccuracyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = _load_cases()
        assert len(cls.cases) == 100, f"need 100 cases, got {len(cls.cases)}"

    def test_hundred_artist_talk_accuracy(self) -> None:
        fails: list[str] = []
        for row in self.cases:
            text = row["text"]
            images = list(row.get("images") or [])
            roles = list(row.get("image_roles") or [])
            payload = advise_route(text, images=images, image_roles=roles)
            cid = row.get("id")
            want_ask = bool(row.get("expect_ask"))
            want_mode = row.get("expect_mode")
            want_routes = list(row.get("expect_routes") or [])

            if want_ask:
                if payload.get("mode") != "stop" or not payload.get("artist_ask"):
                    fails.append(
                        f"#{cid} ASK fail text={text!r} mode={payload.get('mode')} "
                        f"ask={payload.get('artist_ask')!r} routes={payload.get('route_ids')}"
                    )
                continue

            got_mode = payload.get("mode")
            got_routes = list(payload.get("route_ids") or [])
            if want_mode and got_mode != want_mode:
                fails.append(
                    f"#{cid} mode {got_mode!r}!={want_mode!r} text={text!r} routes={got_routes} "
                    f"ask={payload.get('artist_ask')!r}"
                )
                continue
            if want_routes and got_routes != want_routes:
                fails.append(
                    f"#{cid} routes {got_routes}!={want_routes} text={text!r} mode={got_mode} "
                    f"ask={payload.get('artist_ask')!r}"
                )

        ok = 100 - len(fails)
        acc = ok / 100.0
        if fails:
            preview = "\n".join(fails[:25])
            self.fail(f"artist_talk accuracy {acc:.0%} ({ok}/100) < {ACCURACY_FLOOR:.0%}\n{preview}")
        self.assertGreaterEqual(acc, ACCURACY_FLOOR)


if __name__ == "__main__":
    unittest.main()
