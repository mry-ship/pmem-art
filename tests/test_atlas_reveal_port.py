"""Multi-project reveal: never reuse another project's port as healthy."""
from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

import atlas_reveal as ar


class TestRevealPortRootMatch(unittest.TestCase):
    def test_norm_root_insensitive(self) -> None:
        a = ar._norm_root(r"C:\Users\Me\Proj")
        b = ar._norm_root(r"c:/Users/Me/Proj/")
        self.assertEqual(a, b)

    def test_preferred_port_stable_and_diverges(self) -> None:
        a = ar.preferred_port_for_root(r"C:\Users\Me\ArtA")
        b = ar.preferred_port_for_root(r"C:\Users\Me\ArtA")
        c = ar.preferred_port_for_root(r"C:\Users\Me\ArtB-Test")
        self.assertEqual(a, b)
        self.assertGreaterEqual(a, ar.DEFAULT_PORT)
        self.assertLess(a, ar.DEFAULT_PORT + ar.PREFERRED_PORT_SPAN)
        # 不同项目应尽量错开（哈希碰撞概率极低；若真撞仍可由占用顺延兜底）
        self.assertNotEqual(a, c)

    def test_ping_rejects_foreign_root(self) -> None:
        foreign = {"ok": True, "service": ar.SERVICE_NAME, "apis": ["promote", "trash"], "root": r"C:\Other\Proj"}
        payload = mock.Mock()
        payload.status = 200
        payload.read.return_value = __import__("json").dumps(foreign).encode()
        cm = mock.MagicMock()
        cm.__enter__.return_value = payload
        cm.__exit__.return_value = False
        with mock.patch("atlas_reveal.urllib.request.urlopen", return_value=cm):
            self.assertFalse(ar.ping_server(27865, root=Path(r"C:\Mine\Proj")))
            self.assertTrue(ar.ping_server(27865))  # no root filter still ok

    def test_pick_skips_foreign_occupied_port(self) -> None:
        mine = Path(r"C:\Mine\Art").resolve()

        def fake_ping(port: int, timeout: float = 0.4, *, root=None) -> bool:
            if port != 27865:
                return False
            if root is None:
                return True  # someone is there
            return ar._norm_root(root) == ar._norm_root(r"C:\Other\Art")

        with mock.patch("atlas_reveal.ping_server", side_effect=fake_ping):
            with mock.patch("atlas_reveal._port_free", side_effect=lambda p: p == 27866):
                chosen = ar._pick_listen_port(27865, root=mine)
        self.assertEqual(chosen, 27866)


if __name__ == "__main__":
    unittest.main()
