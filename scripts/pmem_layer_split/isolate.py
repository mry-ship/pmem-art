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
    SHADOW_GROUNDED,
    SHADOW_FLYING,
    SHADOW_DISTANT,
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


def _find_image_gen() -> Path:
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
    raise FileNotFoundError(
        "apikey-image/image_gen.py not found; set APIKEY_IMAGE_GEN or install skill"
    )


def _prompt_for(layer: dict, extra_remove: str = "") -> str:
    remove = layer.get("remove") or ""
    if extra_remove:
        remove = (remove + ", " + extra_remove).strip(", ")
    keep = layer.get("keep") or layer.get("note") or layer["id"]
    if layer.get("id") == "bg" or layer.get("mode") == "full":
        return BG_ISOLATE_PROMPT.format(
            keep=keep,
            remove=remove or "all characters, props, foreground subjects",
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
) -> tuple[bool, str]:
    assert_allowed_size(size)
    cmd = [
        sys.executable,
        str(image_gen),
        "-o",
        str(out),
        "--image",
        str(crop),
        "--size",
        size,
        "--quality",
        quality,
        "--background",
        "transparent",
        prompt,
    ]
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
        size = layer.get("size") or "1024x1024"
        if size not in ALLOWED_SIZES:
            size = "1024x1024"
        quality = layer.get("quality") or "high"
        extra = ""
        if st.get("status") == "dirty":
            extra = "; ".join(st.get("reasons") or [])
        out = job.new_dir / Path(layer["file"]).name
        targets.append((layer, crop, out, size, quality, extra))

    print(f"isolate targets: {[t[0]['id'] for t in targets]} workers={workers}")
    if dry_run:
        for layer, crop, out, size, quality, extra in targets:
            print(f"DRY {layer['id']} size={size} q={quality} -> {out.name}")
        return {"targets": [t[0]["id"] for t in targets], "dry_run": True}

    if not targets:
        print("nothing to isolate")
        return status

    image_gen = _find_image_gen()

    def work(item):
        layer, crop, out, size, quality, extra = item
        prompt = _prompt_for(layer, extra_remove=extra)
        ok, msg = _run_one(image_gen, crop, out, prompt, size, quality)
        return layer["id"], layer, out, ok, msg

    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        futs = [ex.submit(work, t) for t in targets]
        for fut in as_completed(futs):
            lid, layer, out, ok, msg = fut.result()
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
                    "last_size": layer.get("size"),
                    "last_quality": layer.get("quality"),
                }
                print("OK", lid, msg)
            else:
                layers_st[lid] = {
                    "status": "error",
                    "file": prev.get("file"),
                    "retries": retries,
                    "source": "isolate",
                    "error": msg,
                }
                print("FAIL", lid, msg)

    status["layers"] = layers_st
    job.save_status(status)
    return status
