"""Export Mode C game prop PNGs from a flat-background master with clean RGBA."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


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
    rgb = im.convert("RGB")
    arr = np.array(rgb, dtype=np.float32)
    bg = _bg_color(arr)
    dist = np.linalg.norm(arr - bg, axis=2)
    alpha = np.clip((dist - 8.0) / feather, 0.0, 1.0)
    alpha = np.power(alpha, 0.85)

    # Edge decontamination toward premultiplied RGBA
    a3 = alpha[..., None]
    fg = np.where(a3 > 1e-3, (arr - bg * (1.0 - a3)) / np.maximum(a3, 1e-3), 0.0)
    fg = np.clip(fg, 0, 255)

    rgba = np.dstack([fg, alpha * 255.0]).astype(np.uint8)
    out = Image.fromarray(rgba, "RGBA")
    return out.filter(ImageFilter.GaussianBlur(radius=0.4))


def fit_square(rgba: Image.Image, size: int, fill_ratio: float = 0.78) -> Image.Image:
    bbox = rgba.getbbox()
    if not bbox:
        return Image.new("RGBA", (size, size), (0, 0, 0, 0))
    cropped = rgba.crop(bbox)
    cw, ch = cropped.size
    target = int(size * fill_ratio)
    scale = target / max(cw, ch)
    nw, nh = max(1, int(cw * scale)), max(1, int(ch * scale))
    resized = cropped.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.paste(resized, ((size - nw) // 2, (size - nh) // 2), resized)
    return canvas


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("master", type=Path)
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--stem", default="potion")
    args = p.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    im = Image.open(args.master)
    rgba = rgba_from_flat_bg(im)
    rgba.save(args.out_dir / f"{args.stem}_master.png")
    for sz in (256, 128, 64):
        fit_square(rgba, sz).save(args.out_dir / f"{args.stem}_{sz}.png")


if __name__ == "__main__":
    main()
