"""Skill image generation: apikey.fan first, else Cursor default (GenerateImage job spec)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent

AR_SIZE = {
    "9:16": "1024x1536",
    "3:4": "1024x1536",
    "4:3": "1536x1024",
    "16:9": "1536x1024",
    "1:1": "1024x1024",
}

FAN_SCRIPT = Path(r"C:\Users\ZhengLangPC\.cursor\skills\apikey-image\image_gen.py")

_BALANCE_MARKERS = (
    "INSUFFICIENT_BALANCE",
    "Insufficient account balance",
    "insufficient_quota",
    "额度已用完",
)


def _is_balance_error(text: str) -> bool:
    t = text or ""
    return any(m in t for m in _BALANCE_MARKERS)


def try_apikey_fan(
    *,
    prompt: str,
    out_path: Path,
    pad_src: Path | None = None,
    aspect_ratio: str = "1:1",
    timeout: int = 300,
) -> dict[str, Any]:
    """Run apikey-image script. Returns ok=True on success."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not FAN_SCRIPT.is_file():
        return {
            "ok": False,
            "gen_engine": "apikey.fan",
            "error": f"missing {FAN_SCRIPT}",
            "fallback": "cursor.GenerateImage",
        }

    size = AR_SIZE.get(aspect_ratio, "1024x1024")
    cmd = [sys.executable, str(FAN_SCRIPT), "-o", str(out_path), "--size", size]
    if pad_src and pad_src.is_file():
        cmd.extend(["--image", str(pad_src)])
    cmd.append(prompt[:3500])

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "gen_engine": "apikey.fan",
            "error": f"{type(exc).__name__}: {exc}",
            "fallback": "cursor.GenerateImage",
        }

    blob = (proc.stdout or "") + "\n" + (proc.stderr or "")
    if proc.returncode != 0 or not out_path.is_file():
        err = (proc.stderr or proc.stdout or "gen failed")[:500]
        fb = "cursor.GenerateImage" if _is_balance_error(blob) or _is_balance_error(err) else "cursor.GenerateImage"
        return {
            "ok": False,
            "gen_engine": "apikey.fan",
            "error": err.strip(),
            "fallback": fb,
            "balance_exhausted": _is_balance_error(blob),
        }

    return {
        "ok": True,
        "gen_engine": "apikey.fan",
        "path": str(out_path.resolve()),
        "bytes": out_path.stat().st_size,
    }


def fan_or_generate_image_job(
    *,
    prompt: str,
    out_path: Path,
    pad_src: Path | None = None,
    aspect_ratio: str = "1:1",
    bot_id: str = "",
    round_num: int = 0,
) -> dict[str, Any]:
    """Try fan; on failure return a GenerateImage job the Agent can fulfill."""
    fan = try_apikey_fan(
        prompt=prompt,
        out_path=out_path,
        pad_src=pad_src,
        aspect_ratio=aspect_ratio,
    )
    if fan.get("ok"):
        return fan

    refs = [str(pad_src.resolve())] if pad_src and pad_src.is_file() else []
    ar = aspect_ratio if aspect_ratio in AR_SIZE else "1:1"
    job = {
        "gen_engine": "cursor.GenerateImage",
        "description": prompt[:4000],
        "filename": out_path.name,
        "reference_image_paths": refs,
        "aspect_ratio": ar,
        "output_path": str(out_path.resolve()),
        "bot_id": bot_id,
        "round": round_num,
    }
    return {
        "ok": False,
        "needs_agent_gen": True,
        "fan_error": fan.get("error"),
        "balance_exhausted": fan.get("balance_exhausted"),
        "agent_job": job,
    }
