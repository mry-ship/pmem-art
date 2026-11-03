# -*- coding: utf-8 -*-
"""Repair round 2: NCC-align AI cutouts onto original, build full-canvas layers, compose."""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent
ORIG = ROOT / "Original" / "Original.png"
MANIFEST = ROOT / "Manifest" / "layer_manifest.json"
AI = ROOT / "_work" / "ai"
LAYERS = ROOT / "Layers"
RECON = ROOT / "Reconstructed"
VAL = ROOT / "Validation"
W, H = 409, 1024


def ensure_alpha(im: Image.Image) -> Image.Image:
    im = im.convert("RGBA")
    arr = np.array(im)
    if arr[:, :, 3].mean() > 248:
        dark = arr[:, :, :3].mean(axis=2) < 14
        bright = arr[:, :, :3].min(axis=2) > 248
        alpha = np.where(dark | bright, 0, 255).astype(np.uint8)
        im.putalpha(Image.fromarray(alpha))
    return im


def trim(im: Image.Image) -> Image.Image:
    im = ensure_alpha(im)
    bb = im.getchannel("A").getbbox()
    return im.crop(bb) if bb else im


def ncc_search(orig_rgb: np.ndarray, templ_rgba: Image.Image, search_box, scales):
    """Find best scale+pos of template inside search_box on original."""
    L, T, R, B = search_box
    region = orig_rgb[T:B, L:R].astype(np.float32)
    best = None
    t_full = np.array(templ_rgba)
    for sc in scales:
        tw = max(8, int(templ_rgba.size[0] * sc))
        th = max(8, int(templ_rgba.size[1] * sc))
        if tw >= region.shape[1] or th >= region.shape[0]:
            continue
        t = np.array(templ_rgba.resize((tw, th), Image.Resampling.LANCZOS))
        alpha = t[:, :, 3].astype(np.float32) / 255.0
        if alpha.mean() < 0.05:
            continue
        mask = alpha > 0.35
        if mask.sum() < 30:
            continue
        t_rgb = t[:, :, :3].astype(np.float32)
        # grayscale NCC over sliding window (stride 2 for speed)
        t_gray = t_rgb.mean(axis=2)
        t_vals = t_gray[mask]
        t_vals = t_vals - t_vals.mean()
        t_norm = np.sqrt((t_vals ** 2).sum()) + 1e-6
        step = 2 if max(region.shape) > 180 else 1
        for y in range(0, region.shape[0] - th + 1, step):
            for x in range(0, region.shape[1] - tw + 1, step):
                patch = region[y:y + th, x:x + tw].mean(axis=2)
                p_vals = patch[mask]
                p_vals = p_vals - p_vals.mean()
                score = float((p_vals * t_vals).sum() / ((np.sqrt((p_vals ** 2).sum()) + 1e-6) * t_norm))
                # also reward color agreement under mask
                p_rgb = region[y:y + th, x:x + tw]
                color_err = np.abs(p_rgb - t_rgb)[mask].mean() / 255.0
                score = score - 0.35 * color_err
                if best is None or score > best[0]:
                    best = (score, L + x, T + y, tw, th, sc)
    return best


def build_layer_from_match(orig: Image.Image, ai: Image.Image, bbox, expand=0.12):
    x, y, w, h = bbox
    L = max(0, int(x - w * expand))
    T = max(0, int(y - h * expand))
    R = min(W, int(x + w * (1 + expand)))
    B = min(H, int(y + h * (1 + expand)))
    cut = trim(ai)
    # expected size roughly bbox
    base_scale = min(w / cut.size[0], h / cut.size[1])
    scales = [base_scale * s for s in (0.75, 0.85, 0.95, 1.0, 1.08, 1.18, 1.3)]
    orig_rgb = np.array(orig.convert("RGB"))
    best = ncc_search(orig_rgb, cut, (L, T, R, B), scales)
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if best is None:
        # fallback contain in bbox
        sc = min(h / cut.size[1], w / cut.size[0])
        nw, nh = max(1, int(cut.size[0] * sc)), max(1, int(cut.size[1] * sc))
        r = cut.resize((nw, nh), Image.Resampling.LANCZOS)
        px = x + (w - nw) // 2
        py = y + h - nh
        canvas.paste(r, (px, py), r)
        return canvas, {"mode": "fallback", "x": px, "y": py, "nw": nw, "nh": nh, "score": None}

    score, px, py, tw, th, sc = best
    r = cut.resize((tw, th), Image.Resampling.LANCZOS)
    # Original-pixel recovery under AI alpha
    a = np.array(r.getchannel("A")).astype(np.float32) / 255.0
    ai_rgb = np.array(r.convert("RGB")).astype(np.float32)
    # sample original
    patch = np.zeros((th, tw, 3), dtype=np.float32)
    # clip paste region
    x0, y0 = px, py
    x1, y1 = min(W, px + tw), min(H, py + th)
    tw2, th2 = x1 - x0, y1 - y0
    if tw2 <= 0 or th2 <= 0:
        canvas.paste(r, (px, py), r)
        return canvas, {"mode": "ai_only", "x": px, "y": py, "nw": tw, "nh": th, "score": score}
    orig_patch = orig_rgb[y0:y1, x0:x1].astype(np.float32)
    ai_p = ai_rgb[:th2, :tw2]
    a_p = a[:th2, :tw2]
    diff = np.abs(orig_patch - ai_p).mean(axis=2)
    # use original where similar; AI where occlusion/inpaint (large diff) but still opaque
    use_ai = (a_p > 0.4) & (diff > 32)
    rgb = np.where(use_ai[:, :, None], ai_p, orig_patch)
    # where alpha low, ignore
    out = np.dstack([rgb, (a_p * 255).astype(np.uint8)])
    piece = Image.fromarray(out.astype(np.uint8), "RGBA")
    # clean fringe
    aa = piece.getchannel("A").point(lambda v: 0 if v < 20 else v)
    aa = aa.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.45))
    piece.putalpha(aa)
    canvas.paste(piece, (x0, y0), piece)
    return canvas, {"mode": "ncc", "x": x0, "y": y0, "nw": tw2, "nh": th2, "score": round(float(score), 4), "scale": sc}


def build_background(object_layers):
    ai = Image.open(AI / "background.png").convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
    orig = Image.open(ORIG).convert("RGB")
    # union alpha of objects
    union = np.zeros((H, W), dtype=np.float32)
    for im in object_layers:
        a = np.array(im.getchannel("A")).astype(np.float32) / 255.0
        union = np.maximum(union, a)
    union = np.clip(Image.fromarray((union * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(1.5)), 0, 255)
    # reopen as array
    u = np.array(union).astype(np.float32) / 255.0
    o = np.array(orig).astype(np.float32)
    a = np.array(ai).astype(np.float32)
    # outside objects: original; inside holes: AI bg
    rgb = o * (1 - u[:, :, None]) + a * u[:, :, None]
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


def main():
    mdoc = json.loads(MANIFEST.read_text(encoding="utf-8"))
    orig = Image.open(ORIG).convert("RGBA")
    LAYERS.mkdir(exist_ok=True)
    object_ims = []
    infos = []

    for layer in sorted(mdoc["layers"], key=lambda x: x["z_index"]):
        if layer["id"] == "background":
            continue
        print("align", layer["id"], "...")
        ai = Image.open(AI / f"{layer['id']}.png")
        canvas, info = build_layer_from_match(orig, ai, layer["bbox"])
        canvas.save(ROOT / layer["file"])
        object_ims.append(canvas)
        layer["status"] = "repaired_v3"
        layer["placement"] = info
        infos.append({"id": layer["id"], **info})
        print(" ", info)

    bg = build_background(object_ims)
    bg.save(LAYERS / "001_Background.png")
    for layer in mdoc["layers"]:
        if layer["id"] == "background":
            layer["status"] = "repaired_v3"

    # compose in z order
    final = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    final = Image.alpha_composite(final, bg)
    for layer in sorted(mdoc["layers"], key=lambda x: x["z_index"]):
        if layer["id"] == "background":
            continue
        final = Image.alpha_composite(final, Image.open(ROOT / layer["file"]).convert("RGBA"))

    RECON.mkdir(exist_ok=True)
    final.save(RECON / "Final.png")
    Image.blend(orig, final, 0.45).save(RECON / "Final_Overlay.png")

    o = np.array(orig.convert("RGB")).astype(np.float32)
    r = np.array(final.convert("RGB")).astype(np.float32)
    diff = np.abs(o - r)
    mae = float(diff.mean())
    mse = float(((o - r) ** 2).mean())
    psnr = 99.0 if mse < 1e-9 else float(20 * math.log10(255.0 / math.sqrt(mse)))
    ol, rl = o.mean(2), r.mean(2)
    mu_o, mu_r = ol.mean(), rl.mean()
    sig_o, sig_r = ol.var(), rl.var()
    sig_or = ((ol - mu_o) * (rl - mu_r)).mean()
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    ssim = float(((2 * mu_o * mu_r + c1) * (2 * sig_or + c2)) / ((mu_o**2 + mu_r**2 + c1) * (sig_o + sig_r + c2)))
    VAL.mkdir(exist_ok=True)
    heat = (diff.mean(2) / max(diff.mean(2).max(), 1e-6) * 255).astype(np.uint8)
    Image.fromarray(np.stack([heat, (255 - heat) // 2, np.full_like(heat, 40)], 2)).save(VAL / "Difference.png")
    board = Image.new("RGB", (W * 3 + 20, H), (24, 28, 34))
    board.paste(orig.convert("RGB"), (0, 0))
    board.paste(final.convert("RGB"), (W + 10, 0))
    board.paste(Image.open(RECON / "Final_Overlay.png").convert("RGB"), (W * 2 + 20, 0))
    board.save(VAL / "Overlay.png")
    report = {"mae": round(mae, 3), "psnr": round(psnr, 3), "ssim_luma": round(ssim, 4), "repair_round": 2}
    (VAL / "Report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    MANIFEST.write_text(json.dumps(mdoc, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "Manifest" / "placements.json").write_text(json.dumps(infos, ensure_ascii=False, indent=2), encoding="utf-8")
    print("VALIDATION", report)
    from _run_pipeline import emit_html
    emit_html(mdoc, report)


if __name__ == "__main__":
    main()
