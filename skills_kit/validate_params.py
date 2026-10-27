"""Case/converge parameter validation and physical/round gates."""
from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from ._time import _now_cst

from .prompt_scale import DEFAULT_THRESHOLD, MIN_IMAGE_BYTE_ENTROPY, MIN_IMAGE_EDGE_PX
from .scoring import defects_are_substantive
from .image_gates import (
    VALID_ASPECT_RATIOS,
    _aspect_relation,
    _inspect_image_physical_traits,
    _parse_ratio_float,
    resolve_case_config,
)

def validate_case_generation_params(
    case_id_or_session: str,
    aspect_ratio: str = "",
    reference_image_paths: list[str] | tuple[str, ...] | str | None = None,
    *,
    root: Path | None = None,
    output_image_path: str = "",
    continuation_pad: bool = False,
    allow_empty_pad: bool = False,
) -> dict[str, Any]:
    """
    Hard pre-GenerateImage parameter validator:
    1) Resolves per-case config (Case 01..04).
    2) Verifies every path in `reference_image_paths` exists on disk (raises FileNotFoundError with bad path if not).
    3) Verifies `aspect_ratio` matches the case's configured aspect_ratio (raises ValueError naming case, parameter, expected vs actual).
    4) Verifies `reference_image_paths` matches the case's configured reference image and that its actual pixel dimensions on disk
       are consistent with the expected aspect_ratio (warns on minor crop tolerance <=15%, raises ValueError on orientation flip or >15% mismatch).
    """
    base_root = Path(root).resolve() if root is not None else Path.cwd().resolve()
    if isinstance(reference_image_paths, str):
        ref_list = [reference_image_paths] if reference_image_paths.strip() else []
    elif isinstance(reference_image_paths, (list, tuple)):
        ref_list = [str(x) for x in reference_image_paths if str(x).strip()]
    else:
        ref_list = []

    case_cfg = resolve_case_config(case_id_or_session)
    case_label = case_cfg["case_id"] if case_cfg else (case_id_or_session or "UnknownCase")

    if not ref_list:
        if not allow_empty_pad:
            raise FileNotFoundError(
                f"[{case_label}] Parameter 'reference_image_paths' is empty; expected reference image "
                f"'{case_cfg['ref_image'] if case_cfg else '<valid path>'}'"
            )
        expected_ar = (case_cfg["aspect_ratio"] if case_cfg else "") or str(aspect_ratio or "").strip() or "1:1"
        actual_ar = str(aspect_ratio or "").strip() or expected_ar
        warnings: list[str] = ["本轮不垫风格参考，也不垫上一轮成图。"]
        if case_cfg is not None and actual_ar != expected_ar:
            raise ValueError(
                f"[{case_label}] Parameter 'aspect_ratio' mismatch: expected '{expected_ar}', got '{actual_ar}'."
            )
        if output_image_path:
            p_out = Path(output_image_path)
            if not p_out.is_file():
                p_out = base_root / output_image_path
            if p_out.is_file():
                out_traits = _inspect_image_physical_traits(p_out)
                out_rel = _aspect_relation(
                    int(out_traits.get("width") or 0),
                    int(out_traits.get("height") or 0),
                    actual_ar,
                )
                if out_rel["hard_fail"]:
                    raise ValueError(
                        f"[{case_label}] Parameter 'output_image_aspect_ratio' mismatch on '{output_image_path}': "
                        f"expected '{actual_ar}', got '{out_rel['simplified']}' "
                        f"({out_traits.get('width')}x{out_traits.get('height')})."
                    )
        return {
            "valid": True,
            "validation_passed": True,
            "case_id": case_label,
            "aspect_ratio": actual_ar,
            "ref_aspect_ratio": expected_ar,
            "reference_image": "",
            "reference_image_paths": [],
            "reference_traits": {},
            "warnings": warnings,
        }

    resolved_refs: list[Path] = []
    for raw_ref in ref_list:
        p_cand = Path(raw_ref)
        if not p_cand.is_file():
            p_cand = base_root / raw_ref
        if not p_cand.is_file():
            raise FileNotFoundError(
                f"[{case_label}] Parameter 'reference_image_paths' file not found on disk: '{raw_ref}' "
                f"(expected: '{case_cfg['ref_image'] if case_cfg else raw_ref}', actual: missing file '{raw_ref}')"
            )
        resolved_refs.append(p_cand.resolve())

    warnings: list[str] = []
    primary_traits = _inspect_image_physical_traits(resolved_refs[0])

    if case_cfg is not None:
        expected_ar = case_cfg["aspect_ratio"]
        expected_ref = case_cfg["ref_image"]
        actual_ar = str(aspect_ratio or "").strip()
        if not actual_ar or actual_ar != expected_ar:
            raise ValueError(
                f"[{case_label}] Parameter 'aspect_ratio' mismatch: expected '{expected_ar}', got '{actual_ar or '<empty>'}'. "
                "Aborting generation round before calling GenerateImage."
            )

        expected_ref_name = Path(expected_ref).name
        actual_ref_names = [p.name for p in resolved_refs]
        if expected_ref_name not in actual_ref_names and not continuation_pad:
            raise ValueError(
                f"[{case_label}] Parameter 'reference_image_paths' mismatch: expected '{expected_ref}', "
                f"got '{ref_list[0]}'. Aborting generation round before calling GenerateImage."
            )
        if continuation_pad and expected_ref_name not in actual_ref_names:
            warnings.append(
                f"[{case_label}] 本轮垫图改为目前最高分的成图 '{resolved_refs[0].name}'，不再要求文件名等于 '{expected_ref_name}'。"
            )

        exp_ratio_num = _parse_ratio_float(expected_ar)
        w, h = int(primary_traits.get("width", 0)), int(primary_traits.get("height", 0))
        if w > 0 and h > 0 and exp_ratio_num is not None:
            act_ratio_num = w / h
            exp_is_landscape = exp_ratio_num > 1.0
            act_is_landscape = act_ratio_num > 1.0
            rel_diff = abs(act_ratio_num - exp_ratio_num) / exp_ratio_num
            if exp_is_landscape != act_is_landscape or rel_diff > 0.15:
                raise ValueError(
                    f"[{case_label}] Parameter 'reference_image_dimensions' inconsistent with expected aspect_ratio '{expected_ar}': "
                    f"expected ratio ~{exp_ratio_num:.3f} ({expected_ar}), got {w}x{h} (ratio {act_ratio_num:.3f}, {primary_traits.get('aspect_ratio')}). "
                    "Aborting generation round before calling GenerateImage."
                )
            if rel_diff > 0.02:
                warnings.append(
                    f"[{case_label}] Reference image '{ref_list[0]}' pixel dimensions {w}x{h} ({primary_traits.get('aspect_ratio')}) "
                    f"differ slightly ({rel_diff * 100:.1f}%) from target aspect_ratio '{expected_ar}'."
                )

        if output_image_path:
            p_out = Path(output_image_path)
            if not p_out.is_file():
                p_out = base_root / output_image_path
            if p_out.is_file():
                out_traits = _inspect_image_physical_traits(p_out)
                out_rel = _aspect_relation(
                    int(out_traits.get("width") or 0),
                    int(out_traits.get("height") or 0),
                    expected_ar,
                )
                if out_rel["hard_fail"]:
                    raise ValueError(
                        f"[{case_label}] Parameter 'output_image_aspect_ratio' mismatch on '{output_image_path}': "
                        f"expected '{expected_ar}', got '{out_rel['simplified']}' "
                        f"({out_traits.get('width')}x{out_traits.get('height')})."
                    )
                if out_rel["rel_diff"] > 0.02:
                    warnings.append(
                        f"[{case_label}] Output '{output_image_path}' is {out_traits.get('width')}x{out_traits.get('height')} "
                        f"({out_rel['simplified']}), {out_rel['rel_diff'] * 100:.1f}% from '{expected_ar}'."
                    )
        resolved_ar = expected_ar
    else:
        expected_ar = primary_traits.get("canonical_aspect_ratio") or primary_traits.get("aspect_ratio") or "1:1"
        actual_ar = str(aspect_ratio or "").strip()
        if not actual_ar:
            actual_ar = expected_ar
        if actual_ar not in VALID_ASPECT_RATIOS:
            raise ValueError(
                f"[{case_label}] Parameter 'aspect_ratio' invalid: '{actual_ar}'. Must be one of {VALID_ASPECT_RATIOS}."
            )
        w, h = int(primary_traits.get("width") or 0), int(primary_traits.get("height") or 0)
        ref_rel = _aspect_relation(w, h, actual_ar) if w > 0 and h > 0 else {"hard_fail": False}
        if ref_rel.get("hard_fail"):
            raise ValueError(
                f"[{case_label}] Parameter 'aspect_ratio' mismatch against reference image '{resolved_refs[0].name}': "
                f"expected '{actual_ar}', got {w}x{h} ({ref_rel.get('simplified')}, {ref_rel.get('rel_diff', 0) * 100:.1f}%). "
                "Aborting generation round before calling GenerateImage."
            )
        if output_image_path:
            p_out = Path(output_image_path)
            if not p_out.is_file():
                p_out = base_root / output_image_path
            if p_out.is_file():
                out_traits = _inspect_image_physical_traits(p_out)
                out_rel = _aspect_relation(
                    int(out_traits.get("width") or 0),
                    int(out_traits.get("height") or 0),
                    actual_ar,
                )
                if out_rel["hard_fail"]:
                    raise ValueError(
                        f"[{case_label}] Parameter 'output_image_aspect_ratio' mismatch on '{output_image_path}': "
                        f"expected '{actual_ar}', got '{out_rel['simplified']}' "
                        f"({out_traits.get('width')}x{out_traits.get('height')})."
                    )
        resolved_ar = actual_ar

    return {
        "valid": True,
        "validation_passed": True,
        "case_id": case_label,
        "aspect_ratio": resolved_ar,
        "ref_aspect_ratio": case_cfg["aspect_ratio"] if case_cfg else (primary_traits.get("canonical_aspect_ratio") or resolved_ar),
        "reference_image": str(resolved_refs[0]),
        "reference_image_paths": [str(p) for p in resolved_refs],
        "matched_ref_aspect_ratio": True,
        "matched_ref_pad_image": True,
        "reference_traits": primary_traits,
        "warnings": warnings,
    }


def validate_converge_params(
    *,
    session_id: str = "",
    scale: str = "",
    ref_image: str = "",
    aspect_ratio: str = "",
    reference_image_paths: list[str] | tuple[str, ...] | str | None = None,
    output_image_path: str = "",
    root: Path | None = None,
    three_step_stage: str = "step2_generate",
    continuation_pad: bool = False,
    allow_empty_pad: bool = False,
) -> dict[str, Any]:
    """
    Validate converge generation/session parameters with default inheritance from `ref_image`:
    - Default `aspect_ratio` follows the reference image's canonical aspect ratio when not explicitly provided.
    - Default `reference_image_paths` (pad image) follows `[ref_image]` when not explicitly provided.
    - Verifies `reference_image_paths` files exist on disk, `aspect_ratio` matches the reference image,
      and `output_image_path` (when present) matches the target `aspect_ratio`.
    """
    base_root = Path(root).resolve() if root is not None else Path.cwd().resolve()
    if isinstance(reference_image_paths, str):
        raw_refs = [x.strip() for x in reference_image_paths.split(",") if x.strip()] if "," in reference_image_paths else ([reference_image_paths.strip()] if reference_image_paths.strip() else [])
    elif isinstance(reference_image_paths, (list, tuple)):
        raw_refs = [str(x).strip() for x in reference_image_paths if str(x).strip()]
    else:
        raw_refs = []

    inherited_default_pad_image = False
    if not raw_refs and (ref_image or "").strip() and not allow_empty_pad:
        raw_refs = [str(ref_image).strip()]
        inherited_default_pad_image = True

    matched_case_cfg = resolve_case_config(session_id, ref_image or (raw_refs[0] if raw_refs else ""))
    inherited_default_aspect_ratio = False
    eff_ar = str(aspect_ratio or "").strip()
    if not eff_ar:
        inherited_default_aspect_ratio = True
        if matched_case_cfg is not None:
            eff_ar = matched_case_cfg["aspect_ratio"]
        elif raw_refs:
            p_cand = Path(raw_refs[0])
            if not p_cand.is_file():
                p_cand = base_root / raw_refs[0]
            if p_cand.is_file():
                t0 = _inspect_image_physical_traits(p_cand)
                eff_ar = t0.get("canonical_aspect_ratio") or "1:1"

    base_res = validate_case_generation_params(
        session_id or (matched_case_cfg["case_id"] if matched_case_cfg else "converge_session"),
        aspect_ratio=eff_ar,
        reference_image_paths=raw_refs,
        root=base_root,
        output_image_path=output_image_path,
        continuation_pad=continuation_pad,
        allow_empty_pad=allow_empty_pad,
    )
    out_traits: dict[str, Any] = {}
    if output_image_path:
        p_out = Path(output_image_path)
        if not p_out.is_file():
            p_out = base_root / output_image_path
        if p_out.is_file():
            out_traits = _inspect_image_physical_traits(p_out)

    ref_traits = base_res.get("reference_traits") or {}
    return {
        "valid": True,
        "validation_passed": True,
        "case_id": base_res.get("case_id", session_id),
        "scale": (scale or "medium").strip().lower(),
        "aspect_ratio": base_res["aspect_ratio"],
        "ref_aspect_ratio": base_res.get("ref_aspect_ratio", base_res["aspect_ratio"]),
        "ref_dimensions": f"{ref_traits.get('width', 0)}x{ref_traits.get('height', 0)}" if ref_traits.get("width") else "",
        "output_aspect_ratio": out_traits.get("canonical_aspect_ratio") or out_traits.get("aspect_ratio", ""),
        "output_dimensions": f"{out_traits.get('width', 0)}x{out_traits.get('height', 0)}" if out_traits.get("width") else "",
        "reference_image": base_res.get("reference_image", ""),
        "reference_image_paths": base_res.get("reference_image_paths", raw_refs),
        "inherited_default_aspect_ratio": inherited_default_aspect_ratio,
        "inherited_default_pad_image": inherited_default_pad_image,
        "matched_ref_aspect_ratio": True,
        "matched_ref_pad_image": bool(base_res.get("reference_image_paths")),
        "matched_output_aspect_ratio": (
            (out_traits.get("canonical_aspect_ratio") or out_traits.get("aspect_ratio")) == base_res["aspect_ratio"]
            if out_traits.get("exists")
            else True
        ),
        "three_step_stage": three_step_stage,
        "three_step_verified": three_step_stage == "step3_judge",
        "warnings": base_res.get("warnings", []),
    }


def _physical_image_gate(
    traits: dict[str, Any],
    *,
    image_path: str = "",
    target_th: float = DEFAULT_THRESHOLD,
) -> dict[str, Any]:
    """Hard fail when there is no real on-disk image (or it is blank / too small)."""
    reasons: list[str] = []
    if not traits.get("exists"):
        label = (image_path or "").strip() or "<empty>"
        reasons.append(f"磁盘无有效生成图: {label}")
    else:
        w = int(traits.get("width") or 0)
        h = int(traits.get("height") or 0)
        entropy = float(traits.get("color_entropy") or 0.0)
        if w < MIN_IMAGE_EDGE_PX or h < MIN_IMAGE_EDGE_PX:
            reasons.append(f"分辨率过低: {w}x{h}（至少 {MIN_IMAGE_EDGE_PX}px 边长）")
        if entropy < MIN_IMAGE_BYTE_ENTROPY:
            reasons.append(
                f"图像内容熵过低: {entropy:.2f} < {MIN_IMAGE_BYTE_ENTROPY}（疑似空白/纯色占位图）"
            )
    blocked = bool(reasons)
    return {
        "blocked": blocked,
        "reasons": reasons,
        "score_cap": round(float(target_th) - 0.05, 2) if blocked else None,
    }


def _resolve_round_image_path(round_entry: dict[str, Any], root: Path | None = None) -> Path | None:
    img = str((round_entry or {}).get("image") or "").strip()
    if not img:
        return None
    p = Path(img)
    if p.is_file():
        return p
    if root is not None:
        cand = Path(root) / img
        if cand.is_file():
            return cand
    return None


def _round_has_real_image(round_entry: dict[str, Any], root: Path | None = None) -> bool:
    """True when the round's image path still exists on disk and passes the physical gate.

    Always re-inspects the file — never trusts a stale session `image_verification` cache.
    """
    p = _resolve_round_image_path(round_entry, root=root)
    if p is None:
        return False
    traits = _inspect_image_physical_traits(p)
    gate = _physical_image_gate(traits, image_path=str(p))
    return not gate["blocked"]


def _round_counts_as_passed(round_entry: dict[str, Any], threshold: float, root: Path | None = None) -> bool:
    """Passed for stop/finish only after generate+judge + clear gates + on-disk file."""
    r = round_entry or {}
    if not bool(r.get("judged")):
        return False
    stage = str(r.get("stage") or "")
    trace = r.get("step_trace") or []
    # Require the generate step so hand-forged judge-only rows cannot settle as 达标.
    if "step2_generate" not in trace:
        return False
    if stage != "judged" and "step3_judge" not in trace:
        return False
    # A real judge writes five-dim observations; forged score-only rows usually omit them.
    if not str(r.get("dims") or "").strip():
        return False
    try:
        score = float(r.get("score") or 0)
    except (TypeError, ValueError):
        score = 0.0
    if score < float(threshold):
        return False
    if r.get("gate_blocked") or r.get("image_gate_blocked"):
        return False
    if r.get("passed") is False:
        return False
    if r.get("anatomy_veto_blocked"):
        return False
    # Absolute-5D: fail-closed when perspective_anatomy is present and below floor.
    try:
        from .converge_policy import (
            DEFAULT_ANATOMY_FLOOR,
            anatomy_ok_for_stop,
            coerce_dims_dict,
            scene_structure_ok_for_stop,
        )

        dims_p = coerce_dims_dict(r.get("dims_parsed"))
        if str(r.get("subject_kind") or "") == "scene":
            if not scene_structure_ok_for_stop(dims_p, str(r.get("defects") or "")):
                return False
        elif isinstance(dims_p, dict) and "perspective_anatomy" in dims_p:
            floor = float(r.get("anatomy_floor") or DEFAULT_ANATOMY_FLOOR)
            if not anatomy_ok_for_stop(dims_p, floor):
                return False
    except Exception:  # noqa: BLE001 — never break pass detection on import issues
        pass
    # Keep finish aligned with judge soft-defect gate (forged JSON cannot rubber-stamp 达标).
    if not defects_are_substantive(str(r.get("defects") or "")):
        return False
    return _round_has_real_image(r, root=root)



