"""Physical image traits, aspect ratio, and case config maps."""
from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from ._time import _now_cst
from core.scale_constants import DEFAULT_THRESHOLD, MIN_IMAGE_EDGE_PX

# 透明类资产的有效像素下限。低于此值视为几乎没有内容，而不是一张可用的层或图标。
_ALPHA_COVERAGE_FLOOR = {
    "layer": 0.01,
    "transparent": 0.01,
    "cutout": 0.01,
    "icon": 0.005,
    "opaque": 0.005,
}
# 单一颜色铺满整幅才算空白。透明底上的小主体不会因为四周是空而算空白。
BLANK_FRAME_SHARE = 0.985


def empty_physical_traits() -> dict[str, Any]:
    return {
        "exists": False,
        "size_bytes": 0,
        "size_kb": 0.0,
        "width": 0,
        "height": 0,
        "header_width": 0,
        "header_height": 0,
        "aspect_ratio": "unknown",
        "canonical_aspect_ratio": "unknown",
        "color_entropy": 0.0,
        "decode_ok": False,
        "decode_error": "",
        "has_alpha": False,
        "alpha_coverage": 0.0,
        "blank_ratio": 1.0,
        "asset_kind": "opaque",
    }


def physical_asset_kind(*, route_ids: Any = None, module: str = "") -> str:
    """图层和透明件查有效像素；图标阈值更松；其余按不透明成图查空白。"""
    blob = " ".join(str(x).lower() for x in (route_ids or []))
    mod = (module or "").lower()
    if "layer.split" in blob or "layer_split" in blob:
        return "layer"
    if "icon" in blob or "icon" in mod:
        return "icon"
    return "opaque"


def physical_asset_kind_for_session(
    root: Path | None,
    session_id: str = "",
    *,
    module: str = "",
) -> str:
    """Judge 侧没有路由参数时，从会话文件读 route_ids。"""
    ids: list[str] = []
    sid = (session_id or "").strip()
    if root is not None and sid and sid != "latest":
        path = Path(root) / ".memory-art" / "converge" / f"{sid}.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, TypeError):
            data = {}
        if isinstance(data, dict):
            ids = [str(x) for x in (data.get("route_ids") or []) if str(x)]
            if not module:
                module = str(data.get("module") or "")
    return physical_asset_kind(route_ids=ids, module=module)


def _byte_entropy(sample: bytes) -> float:
    import math

    if not sample:
        return 0.0
    counts = [0] * 256
    for b in sample:
        counts[b] += 1
    total = len(sample)
    return -sum((c / total) * math.log2(c / total) for c in counts if c > 0)


def _header_size(raw: bytes) -> tuple[int, int]:
    import struct

    if len(raw) >= 24 and raw[:8] == b"\x89PNG\r\n\x1a\n" and raw[12:16] == b"IHDR":
        return struct.unpack(">II", raw[16:24])
    if len(raw) >= 16 and raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        from core.imageinfo import _webp_size

        wh = _webp_size(raw)
        if wh:
            return int(wh[0]), int(wh[1])
    if len(raw) >= 4 and raw[:2] == b"\xff\xd8":
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
                return int(w), int(h)
            if marker in (0xD8, 0xD9) or (0xD0 <= marker <= 0xD7):
                idx += 2
                continue
            seg_len = struct.unpack(">H", raw[idx + 2 : idx + 4])[0]
            if seg_len < 2:
                break
            idx += 2 + seg_len
    return 0, 0


def _frame_pixel_stats(im: Any) -> dict[str, Any]:
    """Decoded pixels: alpha coverage and how much of the frame is one flat color."""
    import numpy as np
    from PIL import Image

    has_alpha = im.mode in ("RGBA", "LA") or (
        im.mode == "P" and "transparency" in getattr(im, "info", {})
    )
    rgba = im.convert("RGBA")
    resample = Image.Resampling.BOX if hasattr(Image, "Resampling") else Image.BOX
    rgba.thumbnail((96, 96), resample)
    arr = np.asarray(rgba)
    rgb = arr[..., :3]
    alpha = arr[..., 3]
    opaque = alpha >= 16
    coverage = float(opaque.mean()) if opaque.size else 0.0
    frame = int(rgb.shape[0] * rgb.shape[1]) or 1
    if opaque.any():
        vis = rgb[opaque].astype(np.int16) // 32
        packed = (
            (vis[:, 0].astype(np.int32) << 10)
            | (vis[:, 1].astype(np.int32) << 5)
            | vis[:, 2].astype(np.int32)
        )
        _, counts = np.unique(packed, return_counts=True)
        dominant_frame = float(counts.max()) / float(frame)
    else:
        dominant_frame = 0.0
    if has_alpha and coverage < 0.005:
        blank = 1.0
    elif opaque.any():
        blank = dominant_frame
    else:
        blank = 1.0
    return {
        "has_alpha": has_alpha,
        "alpha_coverage": round(coverage if has_alpha else 1.0, 4),
        "blank_ratio": round(float(blank), 4),
    }


def _decode_image_pixels(path: Path) -> dict[str, Any]:
    """Pillow verify() then load(). Header size is not proof the pixels exist."""
    from PIL import Image, UnidentifiedImageError

    failed = {
        "decode_ok": False,
        "decode_error": "",
        "width": 0,
        "height": 0,
        "has_alpha": False,
        "alpha_coverage": 0.0,
        "blank_ratio": 1.0,
    }
    try:
        with Image.open(path) as probe:
            probe.verify()
        with Image.open(path) as im:
            im.load()
            width, height = int(im.size[0]), int(im.size[1])
            loaded = im.copy()
        stats = _frame_pixel_stats(loaded)
        if width <= 0 or height <= 0:
            failed["decode_error"] = "解码后尺寸为空"
            return failed
        return {"decode_ok": True, "decode_error": "", "width": width, "height": height, **stats}
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError) as exc:
        failed["decode_error"] = f"{type(exc).__name__}: {exc}"[:200]
        return failed


def _inspect_image_physical_traits(img_path: Path, *, asset_kind: str = "") -> dict[str, Any]:
    """文件头和字节熵只作旁证。尺寸与是否有效以 Pillow 解码后的像素为准。"""
    kind = asset_kind if asset_kind in _ALPHA_COVERAGE_FLOOR else "opaque"
    if not img_path.is_file():
        out = empty_physical_traits()
        out["asset_kind"] = kind
        return out
    raw = img_path.read_bytes()
    header_w, header_h = _header_size(raw)
    entropy = _byte_entropy(raw[:65536])
    decoded = _decode_image_pixels(img_path)
    w = int(decoded["width"] or 0)
    h = int(decoded["height"] or 0)
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
        "size_bytes": len(raw),
        "size_kb": round(len(raw) / 1024.0, 1),
        "width": w,
        "height": h,
        "header_width": header_w,
        "header_height": header_h,
        "aspect_ratio": ar,
        "canonical_aspect_ratio": canonical_ar,
        "color_entropy": round(entropy, 2),
        "decode_ok": bool(decoded["decode_ok"]),
        "decode_error": decoded["decode_error"],
        "has_alpha": bool(decoded["has_alpha"]),
        "alpha_coverage": decoded["alpha_coverage"],
        "blank_ratio": decoded["blank_ratio"],
        "asset_kind": kind,
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


def _physical_image_gate(
    traits: dict[str, Any],
    *,
    image_path: str = "",
    target_th: float = DEFAULT_THRESHOLD,
    asset_kind: str = "",
) -> dict[str, Any]:
    """拦无法解码、几乎全透明、或整幅单一颜色的图。字节熵只记录，不单独放行或拦截。"""
    reasons: list[str] = []
    kind = asset_kind or str(traits.get("asset_kind") or "opaque")
    if kind not in _ALPHA_COVERAGE_FLOOR:
        kind = "opaque"
    if not traits.get("exists"):
        label = (image_path or "").strip() or "<empty>"
        reasons.append(f"磁盘无有效生成图: {label}")
    elif not traits.get("decode_ok"):
        err = str(traits.get("decode_error") or "无法解码").strip()
        reasons.append(f"图片解码失败: {err}")
    else:
        w = int(traits.get("width") or 0)
        h = int(traits.get("height") or 0)
        if w < MIN_IMAGE_EDGE_PX or h < MIN_IMAGE_EDGE_PX:
            reasons.append(f"分辨率过低: {w}x{h}（至少 {MIN_IMAGE_EDGE_PX}px 边长）")
        if traits.get("has_alpha"):
            floor = _ALPHA_COVERAGE_FLOOR[kind]
            coverage = float(traits.get("alpha_coverage") or 0.0)
            if coverage < floor:
                reasons.append(
                    f"有效像素过少: alpha {coverage:.1%} < {floor:.1%}（{kind}）"
                )
        blank = float(traits.get("blank_ratio") or 0.0)
        if blank >= BLANK_FRAME_SHARE:
            reasons.append(f"画面几乎为空: 空白比例 {blank:.1%}")
    blocked = bool(reasons)
    return {
        "blocked": blocked,
        "reasons": reasons,
        "score_cap": round(float(target_th) - 0.05, 2) if blocked else None,
    }
