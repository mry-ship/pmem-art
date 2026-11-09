"""Export Mode C game prop PNGs.

Default: keep engine output as-is (opaque OK). Do NOT chroma-key flat
backgrounds to fake alpha — Cursor GenerateImage cannot emit transparency;
use opaque isolation bg at generation time. True alpha only when the
upstream engine already produced RGBA.

Legacy `--key-flat-bg` remains for rare migrations and prints a warning.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

try:
    from .alpha_policy import ISOLATION_BG_HEX, post_key_allowed
except ImportError:  # python skills_kit/export_mode_c_icon.py
    from alpha_policy import ISOLATION_BG_HEX, post_key_allowed  # type: ignore


def _bg_color(arr: np.ndarray, margin: int = 8) -> np.ndarray:
    h, w = arr.shape[:2]
    samples = np.concatenate(
        [
            arr[:margin, :margin].reshape(-1, 3),
            arr[:margin, -margin:].reshape(-1, 3),
            arr[-margin:, :margin].reshape(-1, 3),
            arr[-margin:, -margin:].reshape(-1, 3),
        ],
        axis=0,
    )
    return np.median(samples, axis=0)


def rgba_from_flat_bg(im: Image.Image, *, feather: float = 12.0) -> Image.Image:
    """LEGACY chroma-key. Prefer native alpha or opaque isolation instead."""
    rgb = im.convert("RGB")
    arr = np.array(rgb, dtype=np.float32)
    bg = _bg_color(arr)
    dist = np.linalg.norm(arr - bg, axis=2)
    alpha = np.clip((dist - 8.0) / feather, 0.0, 1.0)
    alpha = np.power(alpha, 0.85)

    a3 = alpha[..., None]
    fg = np.where(a3 > 1e-3, (arr - bg * (1.0 - a3)) / np.maximum(a3, 1e-3), 0.0)
    fg = np.clip(fg, 0, 255)

    rgba = np.dstack([fg, alpha * 255.0]).astype(np.uint8)
    out = Image.fromarray(rgba, "RGBA")
    return out.filter(ImageFilter.GaussianBlur(radius=0.4))


def as_delivery_rgba(im: Image.Image, *, key_flat_bg: bool = False) -> Image.Image:
    """Return RGBA for resize/export without inventing alpha unless explicitly keyed."""
    if key_flat_bg:
        if not post_key_allowed():
            print(
                "WARN: --key-flat-bg is legacy. Cursor 路径应直接生成不透明隔离底，"
                "透明引擎应直接出真 alpha；不要靠后抠交差。",
                file=sys.stderr,
            )
        return rgba_from_flat_bg(im)
    if im.mode in ("RGBA", "LA"):
        return im.convert("RGBA")
    if im.mode == "P" and "transparency" in im.info:
        return im.convert("RGBA")
    return im.convert("RGBA")


def _has_useful_alpha(rgba: Image.Image) -> bool:
    if rgba.mode != "RGBA":
        return False
    # Sample corners + center strip — full scan is fine for ≤1024 icons.
    extrema = rgba.getchannel("A").getextrema()
    return bool(extrema and extrema[0] < 250)


def fit_square(
    rgba: Image.Image,
    size: int,
    fill_ratio: float = 0.78,
    *,
    opaque_bg: tuple[int, int, int] | None = None,
) -> Image.Image:
    bbox = rgba.getbbox()
    if opaque_bg is not None:
        canvas = Image.new("RGBA", (size, size), opaque_bg + (255,))
    else:
        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    if not bbox:
        return canvas
    cropped = rgba.crop(bbox)
    cw, ch = cropped.size
    target = int(size * fill_ratio)
    scale = target / max(cw, ch)
    nw, nh = max(1, int(cw * scale)), max(1, int(ch * scale))
    resized = cropped.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas.paste(resized, ((size - nw) // 2, (size - nh) // 2), resized)
    return canvas


def _parse_hex(s: str) -> tuple[int, int, int]:
    raw = (s or ISOLATION_BG_HEX).strip().lstrip("#")
    if len(raw) != 6:
        raw = "000000"
    return int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("master", type=Path)
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--stem", default="potion")
    p.add_argument(
        "--key-flat-bg",
        action="store_true",
        help="LEGACY: chroma-key flat bg to RGBA (discouraged)",
    )
    p.add_argument(
        "--opaque-bg",
        default="",
        help="Solid canvas for size variants when delivering opaque isolation (default #000000)",
    )
    args = p.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    im = Image.open(args.master)
    keyed = bool(args.key_flat_bg)
    rgba = as_delivery_rgba(im, key_flat_bg=keyed)
    source_had_alpha = im.mode in ("RGBA", "LA") or (
        im.mode == "P" and "transparency" in im.info
    )
    # True-alpha delivery: legacy key, or source already has meaningful alpha
    # (four corners near 0 — not a one-pixel speck).
    corner_alpha = False
    if source_had_alpha and rgba.mode == "RGBA":
        w, h = rgba.size
        corners = [rgba.getpixel((0, 0))[3], rgba.getpixel((w - 1, 0))[3],
                   rgba.getpixel((0, h - 1))[3], rgba.getpixel((w - 1, h - 1))[3]]
        corner_alpha = sum(1 for a in corners if a < 16) >= 3
    if keyed or corner_alpha:
        rgba.save(args.out_dir / f"{args.stem}_master.png")
        for sz in (256, 128, 64):
            fit_square(rgba, sz).save(args.out_dir / f"{args.stem}_{sz}.png")
        return

    # Opaque isolation (Cursor default): keep the generated solid bg as-is — never key white→black.
    # Prompt-time isolation (pure black etc.) is the contract; post-hoc dig is forbidden.
    bg = _parse_hex(args.opaque_bg or ISOLATION_BG_HEX)
    rgb = rgba.convert("RGB")
    rgb.save(args.out_dir / f"{args.stem}_master.png")
    # Size variants: scale the full frame (including its solid bg); letterbox only if AR ≠ 1:1.
    for sz in (256, 128, 64):
        canvas = Image.new("RGB", (sz, sz), bg)
        scale = min(sz / rgb.size[0], sz / rgb.size[1])
        nw, nh = max(1, int(rgb.size[0] * scale)), max(1, int(rgb.size[1] * scale))
        resized = rgb.resize((nw, nh), Image.Resampling.LANCZOS)
        canvas.paste(resized, ((sz - nw) // 2, (sz - nh) // 2))
        canvas.save(args.out_dir / f"{args.stem}_{sz}.png")


if __name__ == "__main__":
    main()
