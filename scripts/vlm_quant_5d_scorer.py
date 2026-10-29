#!/usr/bin/env python3
"""Local Absolute-5D VLM scorer bridge for V8 skill converge runners.

The Linux bot host keeps a private scorer; this Windows shim talks to
apikey.fan via ~/.cursor/skills/apikey-openai/gpt.py so converge scripts
can import `vlm_quant_5d_scorer.score_one`.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image

DIMS = (
    "composition",
    "lighting_color",
    "perspective_anatomy",
    "texture_detail",
    "spec_style",
)
WEIGHTS = {k: 0.2 for k in DIMS}
GPT = Path(r"C:\Users\ZhengLangPC\.cursor\skills\apikey-openai\gpt.py")

PROMPT = """你是独立主美裁判。只看这张图，按 Absolute-5D 打分，不要因为文件名猜测档位。
档位锚：3=失败 / 5=差 / 7=合格 / 8.5=近优 / 9.5=优（可到 10）。
五维各 0–10，保留一位小数：构图、光影色彩、透视与解剖、质感、规格与风格。
有结构、透视、手部、糊边、风格跑偏就必须压到 9 以下。缺陷必须是画面里能指出来的问题，禁止写「无明显硬伤」。
只输出一个 JSON 对象，不要 markdown：
{"composition":0,"lighting_color":0,"perspective_anatomy":0,"texture_detail":0,"spec_style":0,"defects":["具体问题"],"strengths":["具体优点"],"grade":"等级词"}
"""


def _thumb(src: Path, max_side: int = 1024) -> Path:
    im = Image.open(src).convert("RGB")
    im.thumbnail((max_side, max_side))
    tmp = Path(tempfile.gettempdir()) / f"vlm_q5d_{src.stem}_{max_side}.jpg"
    im.save(tmp, "JPEG", quality=85)
    return tmp


def _parse(text: str) -> dict[str, Any]:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no json")
    data = json.loads(text[start : end + 1])
    dims = {}
    for k in DIMS:
        dims[k] = round(float(data[k]), 1)
        if not 0 <= dims[k] <= 10:
            raise ValueError(f"{k} out of range")
    defects = data.get("defects") or []
    strengths = data.get("strengths") or []
    if isinstance(defects, str):
        defects = [defects]
    if isinstance(strengths, str):
        strengths = [strengths]
    total = round(sum(dims[k] * WEIGHTS[k] for k in DIMS), 2)
    grade = str(data.get("grade") or ("优" if total >= 9.5 else "近优" if total >= 8.5 else "合格" if total >= 7 else "差"))
    return {
        "ok": True,
        "dims": dims,
        "total": total,
        "defects": [str(x) for x in defects][:4],
        "strengths": [str(x) for x in strengths][:3],
        "grade": grade,
    }


def score_one(item: dict[str, Any], env: dict[str, str], model: str, max_side: int = 1024) -> dict[str, Any]:
    """Score one image item for converge runners.

    Returns dict with ok/total/dims/defects/grade (and error on failure).
    `env` is accepted for API parity with the bot-host scorer; this shim uses
    the local apikey-openai gpt.py config instead.
    """
    del env  # local gpt.py owns auth
    path = Path(item["path"])
    if not path.is_file():
        return {"ok": False, "error": f"missing image: {path}", "total": 0, "dims": {}, "defects": []}
    if not GPT.is_file():
        return {"ok": False, "error": f"missing gpt.py: {GPT}", "total": 0, "dims": {}, "defects": []}

    img = _thumb(path, max_side=max_side)
    goal = (item.get("goal") or "").strip()
    prompt = PROMPT
    if goal:
        prompt = f"任务提示（仅作参考，仍按画面绝对品质打分）：{goal[:240]}\n\n" + PROMPT

    last = ""
    use_model = model or "gpt-6-sol"
    for attempt in range(1, 3):
        cmd = [sys.executable, str(GPT), "-m", use_model, "--effort", "medium", "--image", str(img), prompt]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=300,
            )
        except Exception as e:
            last = f"{type(e).__name__}: {e}"
            continue
        blob = (proc.stdout or "") + "\n" + (proc.stderr or "")
        if proc.returncode != 0:
            last = (proc.stderr or proc.stdout or "score failed")[:300]
            # fallback once
            if attempt == 1 and use_model != "gpt-5.6-sol":
                use_model = "gpt-5.6-sol"
            continue
        try:
            parsed = _parse(proc.stdout or "")
        except Exception as e:
            last = f"{type(e).__name__}: {(proc.stdout or '')[:200]}"
            continue
        parsed["model"] = use_model
        parsed["id"] = item.get("id") or path.name
        parsed["filename"] = item.get("filename") or path.name
        parsed["path"] = str(path)
        parsed["sha256"] = item.get("sha256") or ""
        parsed["role"] = item.get("role") or ""
        parsed["round"] = item.get("round")
        m = re.search(r"\[(\S+) 推理强度", proc.stderr or "")
        if m:
            parsed["model"] = m.group(1)
        return parsed
    return {
        "ok": False,
        "error": last or "score failed",
        "total": 0,
        "dims": {},
        "defects": [],
        "id": item.get("id") or path.name,
        "filename": item.get("filename") or path.name,
        "path": str(path),
        "raw": last,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: vlm_quant_5d_scorer.py <image>")
        raise SystemExit(2)
    p = Path(sys.argv[1])
    out = score_one({"id": p.name, "filename": p.name, "path": str(p)}, {}, "gpt-6-sol")
    print(json.dumps(out, ensure_ascii=False, indent=2))
