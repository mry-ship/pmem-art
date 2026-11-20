# -*- coding: utf-8 -*-
"""Parallel gpt-image-2.5 isolation via apikey-image image_gen.py."""
from __future__ import annotations

import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .defaults import (
    DEFAULT_WORKERS,
    ISOLATE_PROMPT,
    BG_ISOLATE_PROMPT,
    ALLOWED_SIZES,
    ISOLATE_USE_CONTEXT_PAD,
    SHADOW_GROUNDED,
    SHADOW_FLYING,
    SHADOW_DISTANT,
    aspect_pad_rule,
)
from .job import Job, assert_allowed_size


def shadow_rule_for(layer: dict) -> str:
    """Map plan/truth grounded flag → isolate shadow sentence."""
    if "grounded" in layer and layer.get("grounded") is not None:
        # Accept bool or stringy true/false (same rules as calibrate._parse_grounded)
        from .calibrate import _parse_grounded

        return SHADOW_GROUNDED if _parse_grounded(layer["grounded"]) else SHADOW_FLYING
    lid = str(layer.get("id") or "").lower()
    name = str(layer.get("name") or "").lower()
    blob = f"{lid} {name} {layer.get('keep') or ''}".lower()
    if any(k in blob for k in ("fly", "flying", "悬空", "飞天", "飘")):
        return SHADOW_FLYING
    # Prefer explicit id/name tokens; bare "house" alone is too broad.
    if any(
        k in blob
        for k in ("barn", "flower_house", "treehouse", "建筑", "谷仓", "花屋", "树屋", "cottage")
    ) and ("fairy" not in blob and "飞" not in blob):
        return SHADOW_DISTANT
    if layer.get("id") in ("bg",) or layer.get("mode") == "full":
        return SHADOW_DISTANT
    return SHADOW_GROUNDED


def _find_image_gen() -> Path | None:
    """Prefer gpt-image-2.5 via apikey-image. None → Agent falls back to Cursor GenerateImage."""
    env = os.environ.get("APIKEY_IMAGE_GEN")
    if env and Path(env).exists():
        return Path(env)
    home = Path.home()
    for c in (
        home / ".cursor" / "skills" / "apikey-image" / "image_gen.py",
        home / ".agents" / "skills" / "apikey-image" / "image_gen.py",
    ):
        if c.exists():
            return c
    return None


def _prompt_for(
    layer: dict,
    extra_remove: str = "",
    *,
    canvas_wh: tuple[int, int] | None = None,
    size: str | None = None,
) -> str:
    remove = layer.get("remove") or ""
    if extra_remove:
        remove = (remove + ", " + extra_remove).strip(", ")
    keep = layer.get("keep") or layer.get("note") or layer["id"]
    if layer.get("id") == "bg" or layer.get("mode") == "full":
        cw, ch = canvas_wh or (0, 0)
        eng = size or layer.get("size") or "1024x1536"
        if cw > 0 and ch > 0:
            aspect_rule = aspect_pad_rule(cw, ch, eng)
        else:
            aspect_rule = (
                "Keep scenic proportions identical to the crop. "
                "If engine size aspect differs from the crop, pad with matching "
                "sky/ground margins — NEVER squash or stretch."
            )
        return BG_ISOLATE_PROMPT.format(
            keep=keep,
            remove=remove or "all characters, props, foreground subjects",
            aspect_rule=aspect_rule,
        )
    return ISOLATE_PROMPT.format(
        keep=keep,
        remove=remove or "neighbors, ground, sky",
        shadow_rule=shadow_rule_for(layer),
    )


def _run_one(
    image_gen: Path,
    crop: Path,
    out: Path,
    prompt: str,
    size: str,
    quality: str,
    *,
    context: Path | None = None,
) -> tuple[bool, str]:
    assert_allowed_size(size)
    cmd = [
        sys.executable,
        str(image_gen),
        "-o",
        str(out),
        "--image",
        str(crop),
    ]
    # Dual-pad: generous crop first, then full-scene boxed context (if present)
    if context is not None and context.is_file():
        cmd.extend(["--image", str(context)])
    cmd.extend(
        [
            "--size",
            size,
            "--quality",
            quality,
            "--background",
            "transparent",
            prompt,
        ]
    )
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        if r.returncode != 0:
            return False, (r.stderr or r.stdout or "fail")[-500:]
        return True, (r.stdout or "").strip()
    except Exception as e:
        return False, str(e)


def _should_isolate(lid: str, st: dict, *, force: bool, ids: list[str] | None) -> bool:
    if ids is not None:
        return lid in ids
    if force:
        return True
    status = st.get("status")
    if status == "ok":
        return False
    if status == "pending_gate":
        # already have a fresh sprite waiting for compose/gate
        return False
    # dirty / error / needs_human / missing / unset
    return True


def isolate_layers(
    job: Job,
    *,
    ids: list[str] | None = None,
    workers: int = DEFAULT_WORKERS,
    force: bool = False,
    skip_bg: bool = False,
    dry_run: bool = False,
) -> dict:
    truth = job.load_truth()
    status = job.load_status()
    layers_st = status.setdefault("layers", {})
    job.new_dir.mkdir(exist_ok=True)
    canvas = truth.get("canvas") or {}
    canvas_wh = (int(canvas.get("w") or 0), int(canvas.get("h") or 0))
    if canvas_wh[0] <= 0 or canvas_wh[1] <= 0:
        try:
            ref = job.open_ref({"ref": truth.get("ref")})
            canvas_wh = ref.size
        except Exception:
            canvas_wh = (0, 0)

    targets = []
    for layer in truth["layers"]:
        lid = layer["id"]
        if skip_bg and lid == "bg":
            continue
        st = layers_st.get(lid, {})
        # Keep local_dig only in --bg-local mode; API mode must re-draw muddy bg
        if (
            st.get("source") == "local_dig"
            and lid == "bg"
            and not skip_bg
        ):
            need = True
        elif st.get("source") == "local_dig" and not force and (ids is None or lid not in ids):
            continue
        else:
            need = _should_isolate(lid, st, force=force, ids=ids)
        if not need:
            continue
        crop = job.crops_dir / f"{lid}.png"
        if not crop.exists():
            print("SKIP no crop", lid)
            continue
        ctx = job.crops_dir / f"{lid}_ctx.png"
        if not (ISOLATE_USE_CONTEXT_PAD and ctx.is_file()):
            ctx = None
        size = layer.get("size") or "1024x1024"
        if size not in ALLOWED_SIZES:
            size = "1024x1024"
        quality = layer.get("quality") or "high"
        extra = ""
        if st.get("status") == "dirty":
            extra = "; ".join(st.get("reasons") or [])
        out = job.new_dir / Path(layer["file"]).name
        targets.append((layer, crop, ctx, out, size, quality, extra))

    print(f"isolate targets: {[t[0]['id'] for t in targets]} workers={workers}")
    if dry_run:
        for layer, crop, ctx, out, size, quality, extra in targets:
            ctx_s = f" +ctx={ctx.name}" if ctx else ""
            print(f"DRY {layer['id']} size={size} q={quality}{ctx_s} -> {out.name}")
        return {"targets": [t[0]["id"] for t in targets], "dry_run": True}

    if not targets:
        print("nothing to isolate")
        return status

    image_gen = _find_image_gen()
    if image_gen is None:
        # Soft stop: skill allows Cursor GenerateImage fallback (Agent-side).
        print(
            "NO_GPT_IMAGE_25: no gpt-image-2.5 path; "
            "Agent must isolate with Cursor GenerateImage "
            "(opaque black isolation bg; no post cutout). "
            "Do not mention keys to the user."
        )
        for layer, crop, ctx, out, size, quality, extra in targets:
            lid = layer["id"]
            prev = layers_st.get(lid, {})
            entry = {
                "status": "needs_cursor_gen",
                "file": prev.get("file"),
                "retries": int(prev.get("retries") or 0),
                "source": "await_cursor",
                "crop": f"_crops/{crop.name}",
                "out": f"new/{out.name}",
                "size": size,
                "quality": quality,
                "prompt": _prompt_for(
                    layer, extra_remove=extra, canvas_wh=canvas_wh, size=size
                ),
            }
            if ctx is not None:
                entry["context"] = f"_crops/{ctx.name}"
            layers_st[lid] = entry
            print("NEED_CURSOR", lid, "->", out.name, "+ctx" if ctx else "")
        status["layers"] = layers_st
        status["dirty_ids"] = [t[0]["id"] for t in targets]
        status["engine"] = "cursor_fallback"
        job.save_status(status)
        return status

    def work(item):
        layer, crop, ctx, out, size, quality, extra = item
        prompt = _prompt_for(
            layer, extra_remove=extra, canvas_wh=canvas_wh, size=size
        )
        ok, msg = _run_one(
            image_gen, crop, out, prompt, size, quality, context=ctx
        )
        return layer["id"], layer, ctx, out, ok, msg, extra

    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        futs = [ex.submit(work, t) for t in targets]
        for fut in as_completed(futs):
            lid, layer, ctx, out, ok, msg, extra = fut.result()
            prev = layers_st.get(lid, {})
            retries = int(prev.get("retries") or 0)
            if prev.get("status") == "dirty":
                retries += 1
            if ok:
                layers_st[lid] = {
                    "status": "pending_gate",
                    "file": f"new/{out.name}",
                    "retries": retries,
                    "source": "isolate",
                    "engine": "gpt-image-2.5",
                    "last_size": layer.get("size"),
                    "last_quality": layer.get("quality"),
                    "pads": ["crop"] + (["context"] if ctx else []),
                }
                print("OK", lid, msg)
            else:
                # API present but call failed → also hand off to Cursor path
                sz = layer.get("size") or "1024x1024"
                entry = {
                    "status": "needs_cursor_gen",
                    "file": prev.get("file"),
                    "retries": retries,
                    "source": "await_cursor",
                    "crop": f"_crops/{lid}.png",
                    "out": f"new/{out.name}",
                    "size": sz,
                    "quality": layer.get("quality") or "high",
                    "prompt": _prompt_for(
                        layer,
                        extra_remove=extra if prev.get("status") == "dirty" else "",
                        canvas_wh=canvas_wh,
                        size=sz,
                    ),
                    "error": msg,
                }
                if ctx is not None:
                    entry["context"] = f"_crops/{ctx.name}"
                layers_st[lid] = entry
                print("FAIL_FALLBACK_CURSOR", lid, msg)

    status["layers"] = layers_st
    status["engine"] = "gpt-image-2.5"
    job.save_status(status)
    return status
