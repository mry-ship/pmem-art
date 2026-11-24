"""Hard pits: aspect register gate, parallel slots, image sha1, taste lock."""
from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from PIL import Image

from skills_kit.converge import (
    _assert_output_matches_session_aspect,
    _file_sha1,
    cmd_converge,
)
from skills_kit.image_gates import _inspect_image_physical_traits
from skills_kit.validate_params import _physical_image_gate
from skills_kit.parallel_slots import assert_can_start, list_active_sessions, max_parallel
from improve.taste_profile import save_taste, load_taste


class TestAspectRegisterGate(unittest.TestCase):
    def test_portrait_rejects_landscape_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "vert.png"
            Image.new("RGB", (720, 1280), (1, 2, 3)).save(p)
            traits = _inspect_image_physical_traits(p)
            ok, why = _assert_output_matches_session_aspect(
                image_path=p, traits=traits, session_ar="16:9"
            )
            self.assertFalse(ok)
            self.assertIn("16:9", why)

    def test_matching_aspect_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "land.png"
            Image.new("RGB", (1280, 720), (1, 2, 3)).save(p)
            traits = _inspect_image_physical_traits(p)
            ok, why = _assert_output_matches_session_aspect(
                image_path=p, traits=traits, session_ar="16:9"
            )
            self.assertTrue(ok, why)
            self.assertEqual(why, "")


class TestStartRequiresExplicitAspectWithPad(unittest.TestCase):
    def test_start_with_pad_without_aspect_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".memory-art" / "converge").mkdir(parents=True)
            pad = root / "pad.png"
            Image.new("RGB", (40, 90), (9, 9, 9)).save(pad)
            buf = io.StringIO()
            old = os.environ.get("PMEM_ART_UNDER_TEST")
            os.environ["PMEM_ART_UNDER_TEST"] = "1"
            try:
                with redirect_stdout(buf), redirect_stderr(buf):
                    rc = cmd_converge(
                        root,
                        {"config": {"converge": {}, "agent": {"max_parallel": 4}}},
                        "start",
                        session_id="hard-pit-aspect",
                        goal="test",
                        module="brand.WorldStyle",
                        reference_image_paths=[str(pad)],
                        aspect_ratio="",
                        skip_route_gate=True,
                        skip_reason="unittest hard-pit aspect",
                    )
            finally:
                if old is None:
                    os.environ.pop("PMEM_ART_UNDER_TEST", None)
                else:
                    os.environ["PMEM_ART_UNDER_TEST"] = old
            self.assertEqual(rc, 1)
            self.assertIn("必须显式传入", buf.getvalue())


class TestParallelSlots(unittest.TestCase):
    def test_blocks_when_full(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / ".memory-art" / "converge"
            d.mkdir(parents=True)
            data = {"config": {"agent": {"max_parallel": 2}}}
            for i in range(2):
                (d / f"s{i}.json").write_text(
                    json.dumps({"session_id": f"s{i}", "status": "running"}),
                    encoding="utf-8",
                )
            ok, msg = assert_can_start(root, data, session_id="s-new")
            self.assertFalse(ok)
            self.assertIn("并行槽已满", msg)
            # same id reuse ok
            ok2, _ = assert_can_start(root, data, session_id="s0")
            self.assertTrue(ok2)
            self.assertEqual(max_parallel(data), 2)
            self.assertEqual(len(list_active_sessions(root)), 2)


class TestGeneralDimBounds(unittest.TestCase):
    def test_general_axis_does_not_steal_the_next_label(self) -> None:
        from skills_kit.scoring import parse_5d_dims

        stolen = parse_5d_dims("构图/光影9.5/透视9.0/质感9.1/风格9.2/无瑕疵9.3")
        self.assertNotIn("composition", stolen["parsed"])
        self.assertIsNone(stolen["weighted_score"])
        kept = parse_5d_dims("构图:9.6/光影 9.5/透视9.4/质感9.3/风格9.2/无瑕疵9.1")
        self.assertEqual(kept["parsed"]["composition"], 9.6)
        self.assertEqual(kept["parsed"]["lighting_color"], 9.5)
        self.assertIsNotNone(kept["weighted_score"])
        self.assertLessEqual(kept["weighted_score"], 10)

    def test_general_axis_above_ten_is_dropped(self) -> None:
        from skills_kit.scoring import parse_5d_dims

        over = parse_5d_dims("构图11/光影9.5/透视9.0/质感9.1/风格9.2/无瑕疵9.3")
        self.assertNotIn("composition", over["parsed"])
        self.assertIsNone(over["weighted_score"])
        kv = parse_5d_dims("composition=12 lighting=9 perspective=9 texture=9 style=9")
        self.assertIsNone(kv["weighted_score"])


class TestImageSha1(unittest.TestCase):
    def test_cap_pulls_dims_down_with_the_score(self) -> None:
        from skills_kit.judge_auto import auto_vlm_judge_image
        from skills_kit.prompt_scale import get_converge_scale_profile

        prof = get_converge_scale_profile("medium", goal="写实窗边少女", module="character.Hero")
        res = auto_vlm_judge_image(
            "",
            prof,
            round_num=1,
            dims="构图9.60/光影9.50/透视9.50/质感9.60/风格9.60/无瑕疵9.70",
            defects="构图呆板",
            use_remote_vlm=False,
        )
        self.assertLessEqual(res["calibrated_score"], 8.90)
        self.assertTrue(res.get("dims_parsed"))
        for val in res["dims_parsed"].values():
            self.assertLessEqual(float(val), res["calibrated_score"] + 1e-6)
        self.assertNotIn("9.60", res["dims"])
        from skills_kit.scoring import cap_reported_dims, parse_5d_dims

        again = parse_5d_dims(res["dims"]).get("parsed") or {}
        self.assertEqual(set(again), set(res["dims_parsed"]))
        for key, val in res["dims_parsed"].items():
            self.assertLessEqual(abs(float(again[key]) - float(val)), 0.05)

        kept, line = cap_reported_dims(
            {"composition": 9.6, "lighting_color": 9.5, "flawlessness": 9.4},
            weighted=9.5,
            calibrated=9.5,
        )
        self.assertEqual(line, "")
        self.assertEqual(kept["composition"], 9.6)

    def test_foreign_bytes_are_refused(self) -> None:
        from skills_kit.converge import _foreign_plate_owner

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plate = root / "plate.png"
            Image.new("RGB", (80, 80), (3, 4, 5)).save(plate)
            digest = _file_sha1(plate)
            folder = root / ".memory-art" / "converge"
            folder.mkdir(parents=True)
            (folder / "other.json").write_text(
                json.dumps({
                    "session_id": "other",
                    "rounds": [{"round": 1, "image_sha1": digest, "image": "plate.png"}],
                }),
                encoding="utf-8",
            )
            self.assertIn("other", _foreign_plate_owner(root, digest, "mine", 1))
            self.assertEqual(_foreign_plate_owner(root, digest, "other", 1), "")
            self.assertIn("other", _foreign_plate_owner(root, digest, "other", 2))
            plate2 = root / "plate2.png"
            Image.new("RGB", (80, 80), (8, 8, 2)).save(plate2)
            digest2 = _file_sha1(plate2)
            (folder / "alias.json").write_text(
                json.dumps({
                    "session_id": "alias-inner",
                    "rounds": [{"round": 1, "image_sha1": digest2}],
                }),
                encoding="utf-8",
            )
            self.assertEqual(_foreign_plate_owner(root, digest2, "alias", 1), "")
            self.assertTrue(_foreign_plate_owner(root, digest2, "alias", 2))
            (folder / "decoy.tmp.json").write_text(
                json.dumps({
                    "session_id": "decoy",
                    "rounds": [{"round": 1, "image_sha1": digest}],
                }),
                encoding="utf-8",
            )
            self.assertNotIn("decoy", _foreign_plate_owner(root, digest, "mine", 1))

    def test_finish_refuses_swapped_plate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plate = root / "r1.png"
            Image.new("RGB", (80, 80), (1, 2, 3)).save(plate)
            digest = _file_sha1(plate)
            Image.new("RGB", (80, 80), (9, 8, 7)).save(plate)
            folder = root / ".memory-art" / "converge"
            folder.mkdir(parents=True)
            (folder / "swap.json").write_text(
                json.dumps({
                    "session_id": "swap",
                    "goal": "对账",
                    "module": "brand.WorldStyle",
                    "scale": "medium",
                    "max_rounds": 1,
                    "accept_threshold": 9.5,
                    "rounds": [{
                        "round": 1,
                        "score": 8.0,
                        "judged": True,
                        "image": "r1.png",
                        "image_sha1": digest,
                        "dims": "构图8.00/光影8.00/透视8.00/质感8.00/风格8.00/无瑕疵8.00",
                    }],
                }),
                encoding="utf-8",
            )
            buf = io.StringIO()
            with redirect_stdout(buf), redirect_stderr(buf):
                rc = cmd_converge(
                    root, {"config": {}}, "finish",
                    session_id="swap", apply_memory=False, silent=True,
                )
            self.assertEqual(rc, 1)
            self.assertIn("计分后成图被换掉", buf.getvalue())
            saved = json.loads((folder / "swap.json").read_text(encoding="utf-8"))
            self.assertNotEqual(saved.get("status"), "finished")
            self.assertFalse(saved.get("showcase_ready"))

    def test_finish_keeps_matching_plate_and_legacy_without_sha(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plate = root / "r1.png"
            Image.new("RGB", (80, 80), (4, 5, 6)).save(plate)
            digest = _file_sha1(plate)
            folder = root / ".memory-art" / "converge"
            folder.mkdir(parents=True)

            def write_sess(name: str, sha: str | None) -> None:
                row = {
                    "round": 1,
                    "score": 9.6,
                    "judged": True,
                    "passed": True,
                    "image": "r1.png",
                    "dims": "构图9.60/光影9.60/透视9.60/质感9.60/风格9.60/无瑕疵9.60",
                    "dims_parsed": {
                        "composition": 9.6,
                        "lighting_color": 9.6,
                        "perspective_anatomy": 9.6,
                        "texture_detail": 9.6,
                        "spec_style": 9.6,
                        "flawlessness": 9.6,
                    },
                    "defects": "缆绳暗部略匀，水波高光略少",
                    "step_trace": ["step1_start", "step2_generate", "step3_judge"],
                    "stage": "judged",
                    "subject_kind": "scene",
                }
                if sha is not None:
                    row["image_sha1"] = sha
                (folder / f"{name}.json").write_text(
                    json.dumps({
                        "session_id": name,
                        "goal": "对账",
                        "module": "brand.WorldStyle",
                        "scale": "medium",
                        "max_rounds": 3,
                        "accept_threshold": 9.5,
                        "rounds": [row],
                    }),
                    encoding="utf-8",
                )

            write_sess("keep", digest)
            buf = io.StringIO()
            with redirect_stdout(buf), redirect_stderr(buf):
                rc = cmd_converge(
                    root, {"config": {}}, "finish",
                    session_id="keep", apply_memory=False, silent=True,
                )
            self.assertEqual(rc, 0, buf.getvalue())
            self.assertNotIn("计分后成图被换掉", buf.getvalue())
            kept = json.loads((folder / "keep.json").read_text(encoding="utf-8"))
            self.assertEqual(kept.get("status"), "finished")

            write_sess("legacy", None)
            buf = io.StringIO()
            with redirect_stdout(buf), redirect_stderr(buf):
                rc = cmd_converge(
                    root, {"config": {}}, "finish",
                    session_id="legacy", apply_memory=False, silent=True,
                )
            self.assertEqual(rc, 0, buf.getvalue())
            self.assertNotIn("计分后成图被换掉", buf.getvalue())

            write_sess("gone", digest)
            plate.unlink()
            buf = io.StringIO()
            with redirect_stdout(buf), redirect_stderr(buf):
                rc = cmd_converge(
                    root, {"config": {}}, "finish",
                    session_id="gone", apply_memory=False, silent=True,
                )
            self.assertEqual(rc, 1, buf.getvalue())
            self.assertIn("计分后成图丢失", buf.getvalue())
            gone = json.loads((folder / "gone.json").read_text(encoding="utf-8"))
            self.assertNotEqual(gone.get("status"), "finished")

    def test_sha_changes_when_file_replaced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "a.png"
            Image.new("RGB", (32, 32), (1, 1, 1)).save(p)
            a = _file_sha1(p)
            Image.new("RGB", (32, 32), (9, 9, 9)).save(p)
            b = _file_sha1(p)
            self.assertNotEqual(a, b)


class TestTasteLock(unittest.TestCase):
    def test_save_taste_atomic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".memory-art" / "_profile").mkdir(parents=True)
            # minimal bind: write taste via save after seeding path
            taste = load_taste(root)
            taste["likes"] = ["soft gloss"]
            path = save_taste(root, taste)
            self.assertTrue(path.is_file())
            again = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn("soft gloss", str(again.get("likes") or again))


class TestDecodedPhysicalGate(unittest.TestCase):
    def test_broken_png_is_not_valid_because_the_header_parses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "broken.png"
            Image.new("RGB", (128, 128), (20, 40, 60)).save(path)
            raw = path.read_bytes()
            idat = raw.find(b"IDAT")
            self.assertGreater(idat, 0)
            path.write_bytes(raw[: idat + 8] + b"\xff" * 24)
            traits = _inspect_image_physical_traits(path)
            self.assertGreater(traits["header_width"], 0)
            self.assertFalse(traits["decode_ok"])
            self.assertEqual(traits["width"], 0)
            gate = _physical_image_gate(traits, image_path=str(path))
            self.assertTrue(gate["blocked"])
            self.assertTrue(any("解码" in r for r in gate["reasons"]))
            self.assertFalse(any("熵" in r for r in gate["reasons"]))

    def test_flat_color_fails_on_pixels_not_byte_entropy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "flat.png"
            Image.new("RGB", (128, 128), (180, 180, 180)).save(path)
            traits = _inspect_image_physical_traits(path)
            self.assertTrue(traits["decode_ok"])
            self.assertGreaterEqual(traits["blank_ratio"], 0.985)
            traits["color_entropy"] = 7.5
            gate = _physical_image_gate(traits, image_path=str(path))
            self.assertTrue(gate["blocked"])
            self.assertTrue(any("空白" in r for r in gate["reasons"]))
            self.assertFalse(any("熵" in r for r in gate["reasons"]))

    def test_two_tone_image_passes_even_if_bytes_compress(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mark.png"
            img = Image.new("RGB", (128, 128), (12, 18, 32))
            img.paste((220, 48, 36), (24, 24, 104, 104))
            img.save(path)
            traits = _inspect_image_physical_traits(path)
            self.assertTrue(traits["decode_ok"])
            gate = _physical_image_gate(traits, image_path=str(path))
            self.assertFalse(gate["blocked"], gate["reasons"])

    def test_layer_with_almost_no_opaque_pixels_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "speck.png"
            img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
            img.putpixel((3, 3), (255, 0, 0, 255))
            img.save(path)
            traits = _inspect_image_physical_traits(path, asset_kind="layer")
            self.assertTrue(traits["decode_ok"])
            self.assertTrue(traits["has_alpha"])
            self.assertLess(traits["alpha_coverage"], 0.01)
            gate = _physical_image_gate(traits, image_path=str(path), asset_kind="layer")
            self.assertTrue(gate["blocked"])
            self.assertTrue(any("有效像素" in r for r in gate["reasons"]))

    def test_layer_subject_on_transparency_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "blob.png"
            img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
            img.paste((40, 160, 90, 255), (30, 20, 100, 110))
            img.save(path)
            traits = _inspect_image_physical_traits(path, asset_kind="layer")
            gate = _physical_image_gate(traits, image_path=str(path), asset_kind="layer")
            self.assertFalse(gate["blocked"], gate["reasons"])

    def test_low_byte_entropy_does_not_block_a_decoded_picture(self) -> None:
        traits = {
            "exists": True,
            "decode_ok": True,
            "width": 256,
            "height": 256,
            "color_entropy": 1.1,
            "has_alpha": False,
            "alpha_coverage": 1.0,
            "blank_ratio": 0.4,
            "asset_kind": "opaque",
        }
        gate = _physical_image_gate(traits)
        self.assertFalse(gate["blocked"], gate["reasons"])


if __name__ == "__main__":
    unittest.main()
