# -*- coding: utf-8 -*-
"""Repair round: place trimmed AI cutouts into truth bboxes (contain), clean full-canvas bg, recompose."""
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


def trim_rgba(im: Image.Image) -> Image.Image:
    im = im.convert("RGBA")
    a = im.getchannel("A")
    # if almost fully opaque, try dark-key
    arr = np.array(im)
    if arr[:, :, 3].mean() > 250:
        dark = arr[:, :, :3].mean(axis=2) < 16
        alpha = np.where(dark, 0, 255).astype(np.uint8)
        im.putalpha(Image.fromarray(alpha))
        a = im.getchannel("A")
    bb = a.getbbox()
    return im.crop(bb) if bb else im


def place_contain(canvas: Image.Image, im: Image.Image, box, prefer_height=True):
    L, T, BW, BH = box
    im = trim_rgba(im)
    iw, ih = im.size
    if prefer_height:
        scale = min(BH / ih, (BW * 1.15) / iw)
    else:
        scale = min(BW / iw, BH / ih)
    nw = max(1, int(iw * scale))
    nh = max(1, int(ih * scale))
    r = im.resize((nw, nh), Image.Resampling.LANCZOS)
    # soft clean fringe
    a = r.getchannel("A").filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.5))
    r.putalpha(a)
    x = L + (BW - nw) // 2
    y = T + BH - nh  # bottom align in box
    # clamp lightly
    x = max(L - int(0.08 * W), min(x, L + BW - nw + int(0.08 * W)))
    tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    tmp.paste(r, (x, y), r)
    canvas.alpha_composite(tmp)
    return {"left": x / W, "top": y / H, "width": nw / W, "height": nh / H, "x": x, "y": y, "nw": nw, "nh": nh}


def build_bg(mdoc) -> Image.Image:
    ai = Image.open(AI / "background.png").convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
    orig = Image.open(ORIG).convert("RGB")
    # Prefer original in top sky band and bottom snow band where AI often drifts
    o = np.array(orig).astype(np.float32)
    a = np.array(ai).astype(np.float32)
    yy = np.linspace(0, 1, H)[:, None]
    # sky: y<0.12 mostly original; ground plants y>0.88 mix original
    w = np.clip((yy - 0.10) / 0.08, 0, 1)  # 0 at top ->1 lower
    w = np.minimum(w, np.clip((0.92 - yy) / 0.08, 0, 1))
    w = w[:, :, None]
    rgb = o * (1 - w) + a * w
    # but force AI more in mid band (where objects removed)
    mid = ((yy > 0.12) & (yy < 0.85)).astype(np.float32)[:, :, None]
    rgb = o * (1 - mid) + a * mid * 0.85 + o * mid * 0.15
    # simpler: mostly AI bg, keep original only very top sky strip
    sky = (yy < 0.08).astype(np.float32)[:, :, None]
    rgb = a * (1 - sky) + o * sky
    out = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    return out


def main():
    mdoc = json.loads(MANIFEST.read_text(encoding="utf-8"))
    placements = []
    LAYERS.mkdir(exist_ok=True)

    # background first
    bg = build_bg(mdoc)
    bg.save(LAYERS / "001_Background.png")
    placements.append({"id": "background", "file": "Layers/001_Background.png", "left": 0, "top": 0, "width": 1, "height": 1})

    canvas = bg.copy()
    for layer in sorted(mdoc["layers"], key=lambda x: x["z_index"]):
        if layer["id"] == "background":
            layer["status"] = "repaired"
            continue
        ai_path = AI / f"{layer['id']}.png"
        x, y, w, h = layer["bbox"]
        box = (x, y, w, h)
        im = Image.open(ai_path)
        layer_canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        prefer_h = layer["id"] != "fence"
        info = place_contain(layer_canvas, im, box, prefer_height=prefer_h)
        if layer["id"] == "fence":
            # width-lock for fence
            im2 = trim_rgba(im)
            scale = W / im2.size[0]
            nw, nh = W, max(1, int(im2.size[1] * scale))
            if nh > h:
                scale = h / im2.size[1]
                nw, nh = max(1, int(im2.size[0] * scale)), max(1, int(im2.size[1] * scale))
            r = im2.resize((nw, nh), Image.Resampling.LANCZOS)
            a = r.getchannel("A").filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.5))
            r.putalpha(a)
            layer_canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            xx = x + (w - nw) // 2
            yy = y + h - nh
            layer_canvas.paste(r, (xx, yy), r)
            info = {"left": xx / W, "top": yy / H, "width": nw / W, "height": nh / H}

        out = ROOT / layer["file"]
        layer_canvas.save(out)
        canvas = Image.alpha_composite(canvas, layer_canvas)
        layer["status"] = "repaired"
        layer["placement"] = info
        placements.append({"id": layer["id"], "file": layer["file"], **info})
        print(layer["id"], info)

    RECON.mkdir(exist_ok=True)
    canvas.save(RECON / "Final.png")
    orig = Image.open(ORIG).convert("RGBA")
    Image.blend(orig, canvas, 0.45).save(RECON / "Final_Overlay.png")

    # validate
    VAL.mkdir(exist_ok=True)
    o = np.array(orig.convert("RGB")).astype(np.float32)
    r = np.array(canvas.convert("RGB")).astype(np.float32)
    diff = np.abs(o - r)
    mae = float(diff.mean())
    mse = float(((o - r) ** 2).mean())
    psnr = 99.0 if mse < 1e-9 else float(20 * math.log10(255.0 / math.sqrt(mse)))
    ol = o.mean(axis=2); rl = r.mean(axis=2)
    mu_o, mu_r = ol.mean(), rl.mean()
    sig_o, sig_r = ol.var(), rl.var()
    sig_or = ((ol - mu_o) * (rl - mu_r)).mean()
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    ssim = float(((2 * mu_o * mu_r + c1) * (2 * sig_or + c2)) / ((mu_o**2 + mu_r**2 + c1) * (sig_o + sig_r + c2)))
    heat = (diff.mean(axis=2) / max(diff.mean(axis=2).max(), 1e-6) * 255).astype(np.uint8)
    Image.fromarray(np.stack([heat, (255 - heat) // 2, np.full_like(heat, 40)], 2)).save(VAL / "Difference.png")
    board = Image.new("RGB", (W * 3 + 20, H), (24, 28, 34))
    board.paste(orig.convert("RGB"), (0, 0))
    board.paste(canvas.convert("RGB"), (W + 10, 0))
    board.paste(Image.open(RECON / "Final_Overlay.png").convert("RGB"), (W * 2 + 20, 0))
    board.save(VAL / "Overlay.png")
    report = {"mae": round(mae, 3), "psnr": round(psnr, 3), "ssim_luma": round(ssim, 4), "repair_round": 1}
    (VAL / "Report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (ROOT / "Manifest" / "placements.json").write_text(json.dumps(placements, ensure_ascii=False, indent=2), encoding="utf-8")
    MANIFEST.write_text(json.dumps(mdoc, ensure_ascii=False, indent=2), encoding="utf-8")
    print("VALIDATION", report)

    # refresh HTML metrics by calling emit from pipeline
    from _run_pipeline import emit_html
    emit_html(mdoc, report)


if __name__ == "__main__":
    main()
