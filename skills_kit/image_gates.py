"""Physical image traits, aspect ratio, and case config maps."""
from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from ._time import _now_cst

def _inspect_image_physical_traits(img_path: Path) -> dict[str, Any]:
    """
    Inspect image file existence, size, resolution (PNG/JPEG/WebP header), aspect ratio,
    and byte-level Shannon entropy to verify real visual content.
    """
    import math
    import struct

    if not img_path.is_file():
        return {
            "exists": False,
            "size_bytes": 0,
            "size_kb": 0.0,
            "width": 0,
            "height": 0,
            "aspect_ratio": "unknown",
            "color_entropy": 0.0,
        }
    raw = img_path.read_bytes()
    size_b = len(raw)
    w, h = 0, 0
    if len(raw) >= 24 and raw[:8] == b"\x89PNG\r\n\x1a\n" and raw[12:16] == b"IHDR":
        w, h = struct.unpack(">II", raw[16:24])
    elif len(raw) >= 16 and raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        from pmem_art import _webp_size
        wh = _webp_size(raw)
        if wh:
            w, h = int(wh[0]), int(wh[1])
    elif len(raw) >= 4 and raw[:2] == b"\xff\xd8":
        idx = 2
        n = len(raw)
        while idx + 9 < n:
            if raw[idx] != 0xFF:
                idx += 1
                continue
            marker = raw[idx + 1]
            if marker == 0xFF:
                idx += 1
                continue
            if marker in (0xC0, 0xC1, 0xC2, 0xC3):
                h, w = struct.unpack(">HH", raw[idx + 5 : idx + 9])
                break
            if marker in (0xD8, 0xD9) or (0xD0 <= marker <= 0xD7):
                idx += 2
                continue
            seg_len = struct.unpack(">H", raw[idx + 2 : idx + 4])[0]
            if seg_len < 2:
                break
            idx += 2 + seg_len

    sample = raw[:65536]
    if sample:
        counts = [0] * 256
        for b in sample:
            counts[b] += 1
        total = len(sample)
        entropy = -sum((c / total) * math.log2(c / total) for c in counts if c > 0)
    else:
        entropy = 0.0

    if w > 0 and h > 0:
        import math as _m
        g = _m.gcd(w, h)
        ar = f"{w // g}:{h // g}"
        canonical_ar = _infer_canonical_aspect_ratio(w, h)
    else:
        ar = "unknown"
        canonical_ar = "unknown"

    return {
        "exists": True,
        "size_bytes": size_b,
        "size_kb": round(size_b / 1024.0, 1),
        "width": w,
        "height": h,
        "aspect_ratio": ar,
        "canonical_aspect_ratio": canonical_ar,
        "color_entropy": round(entropy, 2),
    }


VALID_ASPECT_RATIOS: tuple[str, ...] = ("1:1", "4:3", "3:4", "16:9", "9:16")


def _infer_canonical_aspect_ratio(width: int, height: int) -> str:
    """Infer the closest standard aspect ratio bucket ('1:1', '4:3', '3:4', '16:9', '9:16') from pixel dimensions."""
    if width <= 0 or height <= 0:
        return "1:1"
    ratio = float(width) / float(height)
    buckets = {
        "1:1": 1.0,
        "4:3": 4.0 / 3.0,
        "3:4": 3.0 / 4.0,
        "16:9": 16.0 / 9.0,
        "9:16": 9.0 / 16.0,
    }
    return min(buckets.items(), key=lambda kv: abs(ratio - kv[1]))[0]



CASE_CONFIG_MAP: dict[str, dict[str, Any]] = {
    "Case 01": {
        "case_id": "Case 01",
        "aspect_ratio": "9:16",
        "ref_image": "comparison/style_refs/style_ref_01_night_city.png",
        # Avoid bare tokens like "01" / everyday words — they false-match normal session names.
        # Structured ids only — multi-token theme slugs false-match user session names
        # like my_pastel_sketch_girl / pmem_03_custom via consecutive token windows.
        "aliases": (
            "case 01", "case_01", "case01",
            "scale_01", "scale_01_night_city",
            "style_ref_01_night_city",
        ),
    },
    "Case 02": {
        "case_id": "Case 02",
        "aspect_ratio": "4:3",
        "ref_image": "comparison/style_refs/style_ref_02_pastel_sketch.png",
        "aliases": (
            "case 02", "case_02", "case02",
            "scale_02", "scale_02_sketch",
            "style_ref_02_pastel_sketch",
        ),
    },
    "Case 03": {
        "case_id": "Case 03",
        "aspect_ratio": "3:4",
        "ref_image": "comparison/style_refs/style_ref_03_sunlit_portrait.png",
        "aliases": (
            "case 03", "case_03", "case03",
            "scale_03", "scale_03_portrait",
            "style_ref_03_sunlit_portrait",
        ),
    },
    "Case 04": {
        "case_id": "Case 04",
        "aspect_ratio": "4:3",
        "ref_image": "comparison/web_refs/web_ref_01_concept_ishtar.png",
        "aliases": (
            "case 04", "case_04", "case04",
            "scale_04", "scale_04_canyon", "scale_04_ui",
            "web_ref_01_concept_ishtar",
        ),
    },
}


def _aspect_relation(width: int, height: int, expected_ar: str) -> dict[str, Any]:
    """Compare pixel ratio to a nominal aspect string. Hard-fail only on flip or >15%."""
    import math as _m
    simplified = "unknown"
    if width > 0 and height > 0:
        g = _m.gcd(int(width), int(height))
        simplified = f"{int(width) // g}:{int(height) // g}"
    expected_num = _parse_ratio_float(expected_ar)
    if width <= 0 or height <= 0 or expected_num is None:
        return {
            "hard_fail": simplified not in ("unknown", expected_ar),
            "rel_diff": 1.0 if simplified not in ("unknown", expected_ar) else 0.0,
            "simplified": simplified,
            "expected": expected_ar,
        }
    actual_num = width / height
    rel = abs(actual_num - expected_num) / expected_num
    exp_landscape = expected_num > 1.02
    act_landscape = actual_num > 1.02
    exp_portrait = expected_num < 0.98
    act_portrait = actual_num < 0.98
    flipped = (exp_landscape and act_portrait) or (exp_portrait and act_landscape)
    return {
        "hard_fail": bool(flipped or rel > 0.15),
        "rel_diff": rel,
        "simplified": simplified,
        "expected": expected_ar,
    }


def resolve_case_config(case_or_session: str = "", ref_image: str = "") -> dict[str, Any] | None:
    """Resolve a case from a session id or a reference path.

    Aliases match whole tokens, and the strongest alias score wins.
    ``01`` inside ``web_ref_01`` does not select Case 01.
    A single everyday word in a prose sentence is not a case id.
    """
    probe = f"{case_or_session or ''} {ref_image or ''}".strip().lower()
    if not probe:
        return None
    if any(tok in probe for tok in ("fresh_ref_", "fresh_bot", "empty_bots")):
        return None
    tokens = [t for t in re.split(r"[^a-z0-9]+", probe) if t]
    prose = (" " in probe) and ("/" not in probe) and ("\\" not in probe)

    def _alias_tokens(alias: str) -> tuple[str, ...]:
        return tuple(t for t in re.split(r"[^a-z0-9]+", alias.lower()) if t)

    best: dict[str, Any] | None = None
    best_score = 0
    best_hits = 0
    for cfg in CASE_CONFIG_MAP.values():
        score = 0
        hits = 0
        for alias in cfg["aliases"]:
            at = _alias_tokens(str(alias))
            if not at:
                continue
            n = len(at)
            if any(tuple(tokens[i:i + n]) == at for i in range(0, len(tokens) - n + 1)):
                hits += 1
                if len(str(alias)) <= 2 and tuple(tokens) != at:
                    score += 1
                else:
                    score += max(len(str(alias)), 3)
        if score > best_score:
            best = cfg
            best_score = score
            best_hits = hits
    if best is None or best_score <= 0:
        return None
    if prose and best_hits < 2 and best_score < 8:
        return None
    exact_aliases = {_alias_tokens(str(a)) for a in best["aliases"]}
    if best_score < 3 and tuple(tokens) not in exact_aliases:
        return None
    return dict(best)


def _parse_ratio_float(ar_str: str) -> float | None:
    if not ar_str or ":" not in str(ar_str):
        return None
    parts = str(ar_str).strip().split(":", 1)
    try:
        w_p, h_p = float(parts[0]), float(parts[1])
        if w_p > 0 and h_p > 0:
            return w_p / h_p
    except (TypeError, ValueError):
        return None
    return None



