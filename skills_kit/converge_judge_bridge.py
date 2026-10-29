"""Converge scoring priority: independent VLM → quant VLM (gpt.py) → Agent pending.

Pixel offline scores are not computed.
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
    from .medium_family import GENERAL_6D_KEYS, ensure_general_weights, weighted_harmonic

    w = ensure_general_weights(_dim_weights(scale_prof))
    present = tuple(k for k in GENERAL_6D_KEYS if k in dims and k in w)
    if len(present) < 5:
        return 0.0
    scores = {k: float(dims.get(k) or 0) for k in present}
    total = weighted_harmonic(scores, w, present)
    return 0.0 if total is None else total


def offline_advisory_only(
    path: Path,
    *,
    api_scale: str = "medium",
    prompt_mode: str = "",
    ref_path: str | None = None,
) -> dict[str, Any]:
    """Retired. Blur used to raise this score, so the live judge no longer calls it."""
    del path, api_scale, prompt_mode, ref_path
    return {"role": "removed", "ok_for_stop": False, "score": None}


_GENERAL_DIM_KEYS = (
    "composition",
    "lighting_color",
    "perspective_anatomy",
    "texture_detail",
    "spec_style",
)


def _official_total(dims: dict[str, Any], item: dict[str, Any], defects: str = "") -> float | None:
    """Geometric mean of the general five. Other rubrics keep the total they already computed.

    Missing general keys are not filled with 0. That used to turn a UI or icon score into 0.
    """
    if not isinstance(dims, dict) or not dims:
        return None
    if any(k not in dims for k in _GENERAL_DIM_KEYS):
        return None
    from .converge_policy import (
        DEFAULT_ANATOMY_FLOOR,
        SCENE_COLLAPSE_FLOOR,
        anatomy_score,
        infer_style_family,
        scene_structure_ok_for_stop,
        style_body_floor,
        style_scene_floor,
    )
    from .prompt_scale import classify_subject

    scale_prof = item.get("scale_prof") if isinstance(item.get("scale_prof"), dict) else {}
    goal = str(item.get("goal") or scale_prof.get("goal") or "")
    module = str(item.get("module") or "")
    ref_image = str(item.get("ref_image") or "")
    family = infer_style_family(goal, module, ref_image)
    total = weighted_total(dims, scale_prof)
    kind = classify_subject(
        goal=goal,
        module=module,
        ref_image=ref_image,
        ref_analysis=str(item.get("ref_analysis") or ""),
    )
    anat = anatomy_score(dims)
    if kind == "scene":
        requested = float(scale_prof.get("scene_structure_floor") or SCENE_COLLAPSE_FLOOR)
        floor = style_scene_floor(family, requested, defects)
        if not scene_structure_ok_for_stop(dims, defects, floor=floor) and anat is not None:
            total = min(float(total), float(anat))
    elif kind in {"humanoid", "creature", "both", "mechanical", "generic"}:
        requested = float(scale_prof.get("anatomy_floor") or DEFAULT_ANATOMY_FLOOR)
        floor = style_body_floor(family, defects, requested)
        if anat is None:
            total = min(float(total), round(floor - 0.05, 2))
        elif anat < floor:
            total = min(float(total), float(anat))
    return round(float(total), 2)


def _normalize_vlm_result(
    parsed: dict[str, Any],
    item: dict[str, Any],
    judge_source: str,
) -> dict[str, Any]:
    out = dict(parsed)
    out["judge_source"] = judge_source
    out["ok_for_stop"] = bool(parsed.get("ok"))
    dims = parsed.get("dims") if isinstance(parsed.get("dims"), dict) else None
    if parsed.get("ok") and dims:
        defects = parsed.get("defects") or []
        if isinstance(defects, list):
            defect_text = "；".join(str(x) for x in defects)
        else:
            defect_text = str(defects or "")
        official = _official_total(dims, item, defect_text)
        if official is not None:
            out["total"] = official
            craft = {
                "composition",
                "lighting_color",
                "perspective_anatomy",
                "texture_detail",
                "spec_style",
            }
            if craft <= set(dims) and "flawlessness" not in dims:
                out["ok_for_stop"] = False
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

                    w_info = parse_5d_dims(
                        dims_raw,
                        _dim_weights(scale_prof),
                        module=str(item.get("module") or ""),
                    )
                    dims = w_info.get("parsed") or {}
                    defects = remote.get("defects") or []
                    if isinstance(defects, str):
                        defects = [defects] if defects.strip() else []
                    parsed = {
                        "ok": True,
                        "dims": dims,
                        "total": (
                            w_info.get("weighted_score")
                            if w_info.get("weighted_score") is not None
                            else (
                                weighted_total(dims, scale_prof)
                                if dims and all(k in dims for k in _GENERAL_DIM_KEYS)
                                else 0
                            )
                        ),
                        "defects": [str(x) for x in defects][:4],
                        "grade": remote.get("grade"),
                        "model": remote.get("model"),
                        "provider": remote.get("provider"),
                    }
                    return _normalize_vlm_result(parsed, item, "independent_vlm")
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
        return _normalize_vlm_result(quant, item, "vlm_quant_5d")

    # 3) Agent must judge — do not treat offline as authoritative
    err = quant.get("error") or vlm_err or "vlm_unavailable"
    return {
        "ok": False,
        "ok_for_stop": False,
        "judge_pending": "agent",
        "judge_source": "agent_required",
        "error": err,
        "total": 0,
        "dims": {},
        "defects": [],
        "id": item.get("id") or path.name,
        "filename": item.get("filename") or path.name,
        "path": str(path),
        "vlm_quant_error": quant.get("error"),
    }
