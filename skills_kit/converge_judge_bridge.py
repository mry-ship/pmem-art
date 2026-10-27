"""Converge scoring priority: independent VLM → quant VLM (gpt.py) → Agent pending.

Offline Absolute-5D is **advisory only** — never drives STOP, pad chain, or record totals.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
_SCRIPTS = REPO / "scripts"


def _dim_weights(scale_prof: dict[str, Any] | None) -> dict[str, float]:
    w = (scale_prof or {}).get("dim_weights")
    if isinstance(w, dict) and w:
        return {k: float(w[k]) for k in w}
    keys = (
        "composition",
        "lighting_color",
        "perspective_anatomy",
        "texture_detail",
        "spec_style",
    )
    return {k: 0.2 for k in keys}


def weighted_total(dims: dict[str, Any], scale_prof: dict[str, Any] | None) -> float:
    w = _dim_weights(scale_prof)
    total = 0.0
    for k, wt in w.items():
        total += float(dims.get(k) or 0) * wt
    return round(total, 2)


def offline_advisory_only(
    path: Path,
    *,
    api_scale: str = "medium",
    prompt_mode: str = "",
    ref_path: str | None = None,
) -> dict[str, Any]:
    if str(_SCRIPTS) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS))
    try:
        from absolute_5d_scorer import absolute_5d  # noqa: WPS433

        r = absolute_5d(
            str(path),
            api_scale=api_scale,
            prompt_mode=prompt_mode,
            ref_path=ref_path,
        )
        dims = {k: round(float(v), 3) for k, v in (r.get("dims") or {}).items()}
        return {
            "role": "advisory_only",
            "ok_for_stop": False,
            "score": round(float(r.get("score") or 0), 3),
            "dims": dims,
            "coverage": r.get("coverage"),
            "version": (r.get("meta") or {}).get("version"),
            "track": r.get("track"),
        }
    except Exception as exc:  # noqa: BLE001
        return {"role": "advisory_only", "ok_for_stop": False, "error": str(exc)}


def _normalize_vlm_result(
    parsed: dict[str, Any],
    item: dict[str, Any],
    judge_source: str,
    offline: dict[str, Any],
) -> dict[str, Any]:
    out = dict(parsed)
    out["judge_source"] = judge_source
    out["offline_advisory"] = offline
    out["ok_for_stop"] = bool(parsed.get("ok"))
    if parsed.get("ok") and "total" not in parsed and parsed.get("dims"):
        out["total"] = weighted_total(parsed["dims"], item.get("scale_prof"))
    return out


def score_for_converge(
    item: dict[str, Any],
    env: dict[str, str],
    model: str,
    *,
    root: Path | None = None,
    scale_prof: dict[str, Any] | None = None,
    goal: str = "",
    use_independent_vlm: bool = True,
) -> dict[str, Any]:
    """Score one image for automated converge runners (not manual Agent record)."""
    path = Path(item["path"])
    root = root or REPO
    bot = item
    api_scale = str(item.get("api_scale") or "medium")
    prompt_mode = str(item.get("prompt_mode") or "")
    ref = item.get("ref_image") or ""
    ref_path = str((root / ref).resolve()) if ref and not Path(ref).is_file() else str(ref)
    if ref and Path(ref).is_file():
        ref_path = str(Path(ref).resolve())

    offline = offline_advisory_only(
        path,
        api_scale=api_scale,
        prompt_mode=prompt_mode,
        ref_path=ref_path if ref_path and Path(ref_path).is_file() else None,
    )
    item = {**item, "scale_prof": scale_prof or {}, "goal": goal or item.get("goal") or ""}

    # 1) Project independent VLM (vlm_judge.local.yaml / PMEM_VLM_API_KEY)
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    if use_independent_vlm:
        try:
            from vlm_judge import maybe_run_independent_vlm_judge  # noqa: WPS433

            prof = scale_prof or {"scale": api_scale, "prompt_mode": prompt_mode, "goal": goal}
            remote = maybe_run_independent_vlm_judge(
                str(path),
                root=root,
                data=None,
                scale_prof=prof,
                goal=goal or str(item.get("goal") or ""),
                module=str(item.get("module") or ""),
                round_num=int(item.get("round") or 1),
            )
            if remote.get("active") and str(remote.get("source")) == "independent_vlm":
                dims_raw = str(remote.get("dims") or "")
                if dims_raw:
                    from skills_kit.scoring import parse_5d_dims  # noqa: WPS433

                    w_info = parse_5d_dims(dims_raw, _dim_weights(scale_prof))
                    dims = w_info.get("parsed") or {}
                    defects = remote.get("defects") or []
                    if isinstance(defects, str):
                        defects = [defects] if defects.strip() else []
                    parsed = {
                        "ok": True,
                        "dims": dims,
                        "total": w_info.get("weighted_score") or weighted_total(dims, scale_prof),
                        "defects": [str(x) for x in defects][:4],
                        "grade": remote.get("grade"),
                        "model": remote.get("model"),
                        "provider": remote.get("provider"),
                    }
                    return _normalize_vlm_result(parsed, item, "independent_vlm", offline)
        except Exception as exc:  # noqa: BLE001
            vlm_err = str(exc)
        else:
            vlm_err = ""
    else:
        vlm_err = ""

    # 2) Quant VLM via apikey-openai gpt.py shim
    if str(_SCRIPTS) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS))
    import vlm_quant_5d_scorer as vlm  # noqa: WPS433

    quant = vlm.score_one(item, env, model)
    if quant.get("ok"):
        return _normalize_vlm_result(quant, item, "vlm_quant_5d", offline)

    # 3) Agent must judge — do not treat offline as authoritative
    err = quant.get("error") or vlm_err or "vlm_unavailable"
    return {
        "ok": False,
        "ok_for_stop": False,
        "judge_pending": "agent",
        "judge_source": "agent_required",
        "error": err,
        "offline_advisory": offline,
        "total": 0,
        "dims": {},
        "defects": [],
        "id": item.get("id") or path.name,
        "filename": item.get("filename") or path.name,
        "path": str(path),
        "vlm_quant_error": quant.get("error"),
    }
