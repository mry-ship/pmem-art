# -*- coding: utf-8 -*-
"""Contain / cover / width compose into calibrated footprints."""
from __future__ import annotations

from pathlib import Path

from PIL import Image

from .job import Job


def trim_alpha(im: Image.Image) -> Image.Image:
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    bb = im.getchannel("A").getbbox()
    return im.crop(bb) if bb else im


def place_scaled(
    canvas: Image.Image,
    im: Image.Image,
    L: int,
    T: int,
    BW: int,
    BH: int,
    mode: str = "contain",
    pad: int = 500,
) -> dict:
    W, H = canvas.size
    iw, ih = im.size
    if mode == "height":
        scale = BH / ih
    elif mode == "width":
        scale = BW / iw
    elif mode == "cover":
        scale = max(BW / iw, BH / ih)
    else:
        scale = min(BW / iw, BH / ih)
    nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
    r = im.resize((nw, nh), Image.Resampling.LANCZOS)
    x = L + (BW - nw) // 2
    y = T + BH - nh  # bottom-align
    tmp = Image.new("RGBA", (W + pad * 2, H + pad * 2), (0, 0, 0, 0))
    tmp.paste(r, (x + pad, y + pad), r)
    canvas.alpha_composite(tmp.crop((pad, pad, pad + W, pad + H)))
    return {
        "left": x / W,
        "top": y / H,
        "width": nw / W,
        "height": nh / H,
        "nw": nw,
        "nh": nh,
        "box_w": BW,
        "box_h": BH,
    }


def resolve_sprite(job: Job, layer: dict) -> Path | None:
    name = layer["file"]
    candidates = [
        job.new_dir / name,
        job.new_dir / Path(name).name,
        job.root / "new" / Path(name).name,
        job.root / name,
    ]
    # also try id.png
    candidates.append(job.new_dir / f"{layer['id']}.png")
    for p in candidates:
        if p.exists():
            return p
    return None


def compose(job: Job, *, scale: int = 2) -> dict:
    truth = job.load_truth()
    cw = int(truth["canvas"]["w"])
    ch = int(truth["canvas"]["h"])
    W, H = cw * scale, ch * scale
    job.trim_dir.mkdir(exist_ok=True)
    job.new_dir.mkdir(exist_ok=True)

    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    placed = []
    metrics = {}

    for layer in sorted(truth["layers"], key=lambda x: x.get("z", 0)):
        src = resolve_sprite(job, layer)
        if src is None:
            print("MISSING", layer["id"], layer["file"])
            metrics[layer["id"]] = {"missing": True}
            continue
        im = Image.open(src)
        mode = layer.get("fill", "contain")
        if layer["id"] == "bg":
            if im.mode != "RGBA":
                im = im.convert("RGBA")
            r = im.resize((W, H), Image.Resampling.LANCZOS)
            canvas.alpha_composite(r)
            r.save(job.trim_dir / Path(layer["file"]).name)
            info = {"left": 0.0, "top": 0.0, "width": 1.0, "height": 1.0}
            box_asp = W / H
            spr_asp = im.size[0] / max(1, im.size[1])
            fill = 1.0
            print(f"bg: cover full from {src.name}")
        else:
            im = trim_alpha(im.convert("RGBA"))
            im.save(job.trim_dir / Path(layer["file"]).name)
            L = int(layer["left"] * W)
            T = int(layer["top"] * H)
            BW = int(layer["width"] * W)
            BH = int(layer["height"] * H)
            if mode == "cover" and layer["id"] != "bg":
                mode = "contain"  # skill: forbid prop cover
            info = place_scaled(canvas, im, L, T, BW, BH, mode)
            box_asp = BW / BH if BH else 1.0
            spr_asp = im.size[0] / max(1, im.size[1])
            fill = (info["nw"] * info["nh"]) / max(1, BW * BH)
            print(
                f"{layer['id']}: {mode} fill={fill:.2f} "
                f"box_px={box_asp:.2f} spr={spr_asp:.2f} src={src.name}"
            )

        metrics[layer["id"]] = {
            "box_px_asp": round(box_asp, 4),
            "spr_asp": round(spr_asp, 4),
            "fill": round(fill, 4),
            "mode": mode if layer["id"] != "bg" else "cover",
        }
        placed.append(
            {
                "id": layer["id"],
                "name": layer.get("name", layer["id"]),
                "note": layer.get("note", ""),
                "z": layer.get("z", 0),
                "file": f"new_trim/{Path(layer['file']).name}",
                "truth": {
                    "left": layer["left"],
                    "top": layer["top"],
                    "width": layer["width"],
                    "height": layer["height"],
                },
                "left": info["left"],
                "top": info["top"],
                "width": info["width"],
                "height": info["height"],
            }
        )

    from .job import save_json

    save_json(job.placements_path, placed)
    save_json(job.root / "_compose_metrics.json", metrics)

    ref = job.open_ref({"ref": truth.get("ref")}).resize((W, H), Image.Resampling.LANCZOS)
    blend = Image.blend(ref, canvas, 0.45)
    board = Image.new("RGB", (W * 3 + 40, H + 20), (30, 36, 44))
    board.paste(ref.convert("RGB"), (10, 10))
    board.paste(canvas.convert("RGB"), (W + 20, 10))
    board.paste(blend.convert("RGB"), (W * 2 + 30, 10))
    out = job.root / "_compose_preview.png"
    board.save(out)
    canvas.convert("RGB").save(job.root / "_compose_mid.png")
    print("wrote", out)
    return {"placed": placed, "metrics": metrics, "canvas": (W, H)}
