"""Automatic VLM / rubric judge for a single image."""
from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from ._time import _now_cst

from .prompt_scale import (
    DEFAULT_MAX_ROUNDS,
    DEFAULT_THRESHOLD,
    classify_subject,
    get_converge_scale_profile,
)
from .scoring import (
    audit_score_inflation,
    defects_are_substantive,
    parse_5d_dims,
)
from .image_gates import _aspect_relation, _inspect_image_physical_traits, resolve_case_config
from .validate_params import _physical_image_gate
from .absolute_5d_agent_rubric import AGENT_JUDGE_SOURCE
from .subject_lexicon import clause
from .converge_policy import (
    DEFAULT_ANATOMY_FLOOR,
    NON_ANATOMY_RUBRICS,
    SCENE_COLLAPSE_FLOOR,
    anatomy_ok_for_stop,
    collapse_marked,
    anatomy_score,
    coerce_dims_dict,
    next_fix_is_weak,
    reconcile_fix_with_subject,
    reflow_fix_text,
    scene_structure_ok_for_stop,
    infer_style_family,
    style_body_floor,
    style_scene_floor,
    clone_subject_structure_ok_for_stop,
    ui_shell_structure_ok_for_stop,
)

def auto_vlm_judge_image(
    image_path: str,
    scale_prof: dict[str, Any],
    round_num: int,
    prev_score: float | None = None,
    dims: str = "",
    defects: str = "",
    next_fix: str = "",
    raw_score: float | None = None,
    *,
    root: Path | None = None,
    module: str = "",
    require_image: bool = True,
    data: dict[str, Any] | None = None,
    goal: str = "",
    strengths: str = "",
    use_remote_vlm: bool = True,
    session_id: str = "",
    ref_image: str = "",
) -> dict[str, Any]:
    """
    Independent 6D VLM Judge & anti-inflation verifier (Step 2B — strictly decoupled from image generation):
    - Takes ONLY the finished `image_path` and independent VLM 6D observations (`dims`, `defects`, `next_fix`).
    - Has NO access to the generation prompt or any generator self-assessment (`raw_score` is never trusted over 6D harmonic mean).
    - Enforces `scale_prof["dim_weights"]`, `audit_score_inflation()`, and the low-scale pose redline (`allow_action_pose_change=False`).
    - By default (`require_image=True`) a missing / blank / tiny file cannot reach STOP_TARGET_REACHED.
    - If `vlm_judge` API key is configured, calls the remote vision model first.
    - If no key: current multimodal Agent scores the 6D checklist via CLI `dims`/`defects`
      (`agent_absolute_5d`). Pixel offline scores are not computed. Threshold stays
      scale profile (default 9.5) — no no-key hard STOP / 8.50 early exit.
    - Case aspect checks use `session_id` + `ref_image` only — never the output filename.
    """
    p = Path(image_path) if image_path else Path()
    if image_path and not p.is_file() and root is not None:
        cand = root / image_path
        if cand.is_file():
            p = cand
    if image_path and not p.is_file():
        cand_cwd = Path.cwd() / image_path
        if cand_cwd.is_file():
            p = cand_cwd

    traits = _inspect_image_physical_traits(p) if image_path else {
        "exists": False,
        "size_bytes": 0,
        "size_kb": 0.0,
        "width": 0,
        "height": 0,
        "aspect_ratio": "unknown",
        "color_entropy": 0.0,
    }

    target_th = float(scale_prof.get("target_score_threshold", DEFAULT_THRESHOLD))
    max_rounds = int(scale_prof.get("max_rounds", DEFAULT_MAX_ROUNDS))

    judge_source = "agent_self_judge"
    remote_meta: dict[str, Any] = {}
    eff_strengths = strengths or ""
    if use_remote_vlm:
        try:
            from vlm_judge import maybe_run_independent_vlm_judge
            remote = maybe_run_independent_vlm_judge(
                image_path,
                root=root,
                data=data,
                scale_prof=scale_prof,
                goal=goal or str(scale_prof.get("goal") or ""),
                module=module,
                round_num=round_num,
                cli_dims=dims,
                cli_defects=defects,
                cli_strengths=strengths,
                cli_next_fix=next_fix,
            )
            remote_meta = {
                "source": remote.get("source"),
                "provider": remote.get("provider"),
                "model": remote.get("model"),
                "error": remote.get("error") or "",
                "active": bool(remote.get("active")),
            }
            judge_source = str(remote.get("source") or "agent_self_judge")
            if judge_source == "independent_vlm":
                dims = str(remote.get("dims") or dims)
                defects = str(remote.get("defects") or defects)
                next_fix = str(remote.get("next_fix") or next_fix)
                eff_strengths = str(remote.get("strengths") or strengths)
            elif judge_source == "vlm_error" and not dims:
                defects = str(remote.get("defects") or defects)
        except Exception as exc:  # noqa: BLE001 — never break local judge path
            remote_meta = {"source": "vlm_import_error", "error": str(exc), "active": False}
            judge_source = "agent_self_judge"

    # No independent VLM → Agent Absolute-5D (same 9.5 gate).
    if judge_source != "independent_vlm":
        if dims.strip():
            judge_source = AGENT_JUDGE_SOURCE
        else:
            judge_source = "agent_self_judge"

    w_info = parse_5d_dims(dims, scale_prof.get("dim_weights"), module=module)
    weighted = w_info.get("weighted_score")

    # Always execute independent VLM/physical inspection so CLI-passed --dims/--defects never short-circuit real checks
    indep_defects: list[str] = []
    if p.is_file():
        sidecar = p.with_suffix(p.suffix + ".vlm.json")
        # Never re-ingest an independent_vlm sidecar into Agent / error-fallback paths —
        # that would revive stale API scores when no key is configured.
        if sidecar.is_file() and judge_source != "independent_vlm":
            try:
                sc_data = json.loads(sidecar.read_text(encoding="utf-8"))
                sc_src = str(sc_data.get("source") or "").strip()
                if sc_src != "independent_vlm":
                    if sc_data.get("defects"):
                        indep_defects.append(str(sc_data["defects"]))
                    if sc_data.get("dims") and not dims:
                        dims = str(sc_data["dims"])
                        w_info = parse_5d_dims(dims, scale_prof.get("dim_weights"), module=module)
                        weighted = w_info.get("weighted_score")
            except Exception:
                pass
        # Never resolve case from the output image path (filenames like scale_02_*.jpg hijack AR).
        eff_ref = (ref_image or str(scale_prof.get("ref_image") or "")).strip()
        matched_case = resolve_case_config(session_id or "", eff_ref)
        if matched_case:
            aspect_rel = _aspect_relation(
                int(traits.get("width") or 0),
                int(traits.get("height") or 0),
                str(matched_case["aspect_ratio"]),
            )
            if aspect_rel["hard_fail"]:
                indep_defects.append(
                    f"画幅比例错误: {matched_case['case_id']} 要求 aspect_ratio={matched_case['aspect_ratio']}，"
                    f"实测为 {aspect_rel['simplified']} ({traits.get('width')}x{traits.get('height')})"
                )

    phys = _physical_image_gate(traits, image_path=str(image_path or ""), target_th=target_th)
    if require_image and phys["blocked"]:
        for reason in phys["reasons"]:
            if reason not in indep_defects:
                indep_defects.append(reason)

    merged_defects = defects or ""
    for idf in indep_defects:
        if idf not in merged_defects:
            merged_defects = f"{merged_defects}；{idf}".strip("； ")
    defects = merged_defects

    eff_dims = dims
    audit_prof = dict(scale_prof)
    if goal and not str(audit_prof.get("goal") or "").strip():
        audit_prof["goal"] = goal
    if ref_image and not str(audit_prof.get("ref_image") or "").strip():
        audit_prof["ref_image"] = ref_image
    ra_merge = scale_prof.get("ref_analysis") or ""
    if ra_merge and not str(audit_prof.get("ref_analysis") or "").strip():
        audit_prof["ref_analysis"] = ra_merge
    audit_res = audit_score_inflation(
        float(raw_score) if (raw_score is not None and float(raw_score) > 0) else 0.0,
        eff_dims,
        defects,
        prev_score,
        audit_prof,
        round_num=round_num,
        module=module,
    )
    calibrated = audit_res["calibrated_score"]
    image_gate_blocked = bool(require_image and phys["blocked"])
    if image_gate_blocked:
        for reason in phys["reasons"]:
            warn = f"图像物理闸门拦截：{reason}"
            if warn not in audit_res["warnings"]:
                audit_res["warnings"].append(warn)
        if phys["score_cap"] is not None:
            calibrated = min(float(calibrated), float(phys["score_cap"]))
    if remote_meta.get("error") and judge_source in (
        "vlm_error_fallback",
        "vlm_import_error",
        "agent_absolute_5d",
        "agent_self_judge",
    ):
        audit_res["warnings"].append(
            f"独立视觉 API 不可用，改由本模型按 Absolute-5D 检查表评分（门槛仍 {target_th}）："
            f"{remote_meta.get('error') or 'no key'}"
        )
    if judge_source == "independent_vlm":
        audit_res["warnings"].append(
            f"独立视觉裁判已采纳：{remote_meta.get('provider')}/{remote_meta.get('model')}"
        )
    if judge_source == "agent_absolute_5d":
        audit_res["warnings"].append(
            f"Agent Absolute-5D 已采纳（门槛 {target_th}）"
        )

    # Rubber-stamp defects cannot justify STOP (Agent / independent VLM alike).
    soft_defects_blocked = False
    if (
        calibrated >= target_th
        and not image_gate_blocked
        and not defects_are_substantive(defects)
    ):
        soft_defects_blocked = True
        calibrated = min(float(calibrated), round(target_th - 0.05, 2))
        warn = "缺陷栏为空或仅套话，拒绝达标停机；请写出可核验的画面问题或继续迭代"
        if warn not in audit_res["warnings"]:
            audit_res["warnings"].append(warn)
    if judge_source == "agent_self_judge" and not str(dims or "").strip():
        soft_defects_blocked = True
        calibrated = min(float(calibrated), round(target_th - 0.05, 2))
        warn = "无独立 VLM 时须由本模型按六维检查表给出 dims；缺六维分拒绝达标"
        if warn not in audit_res["warnings"]:
            audit_res["warnings"].append(warn)

    subject_kind = classify_subject(
        goal=goal or str(scale_prof.get("goal") or ""),
        module=module,
        ref_image=ref_image or str(scale_prof.get("ref_image") or ""),
        ref_analysis=scale_prof.get("ref_analysis") or "",
    )
    rubric_mode = str(audit_res.get("rubric_mode") or "")
    dims_for_anat = coerce_dims_dict(audit_res.get("dims_parsed"))
    if dims_for_anat is None and str(eff_dims or "").strip():
        parsed_now = parse_5d_dims(eff_dims, scale_prof.get("dim_weights"), module=module) or {}
        dims_for_anat = coerce_dims_dict(parsed_now.get("parsed"))
        if not rubric_mode:
            rubric_mode = str(parsed_now.get("rubric_mode") or "")
    # Scene perspective is not rewritten upward. A 6.x vanishing-point score stays in the
    # harmonic mean; only a collapse under 6.0 (or collapse language) pulls the official score down.
    passed = bool(calibrated >= target_th) and not image_gate_blocked and not soft_defects_blocked
    min_rounds = int(scale_prof.get("min_rounds_before_stop") or 1)
    early_stop_blocked = False
    if passed and int(round_num) < min_rounds and int(round_num) < max_rounds:
        # high / recompose: refuse 1-round photocopy stops; keep iterating.
        early_stop_blocked = True
        passed = False
        calibrated = min(float(calibrated), round(target_th - 0.05, 2))
        warn = (
            f"未满最小轮次 ({round_num}/{min_rounds})，拒绝达标停机；"
            f"本档要求至少 {min_rounds} 轮递进后再判定"
        )
        if warn not in audit_res["warnings"]:
            audit_res["warnings"].append(warn)
        if not next_fix:
            next_fix = "下一轮仍垫最初的参考图，只在提示词上补还没到位的那一处"

    style_family = infer_style_family(
        goal or str(scale_prof.get("goal") or ""),
        module,
        ref_image or str(scale_prof.get("ref_image") or ""),
    )
    # Anatomy hard veto on general_5d. UI / icon / skill-additive rubrics have no
    # perspective_anatomy key — skip so they are not fail-closed forever.
    # Scenes: under 6.0 (isometric 5.5) or collapse language blocks.
    if subject_kind == "scene":
        requested_scene = float(scale_prof.get("scene_structure_floor") or SCENE_COLLAPSE_FLOOR)
        anatomy_floor = style_scene_floor(style_family, requested_scene, defects or "")
    else:
        requested_body = float(scale_prof.get("anatomy_floor") or DEFAULT_ANATOMY_FLOOR)
        anatomy_floor = style_body_floor(style_family, defects or "", requested_body)
    anat_val = anatomy_score(dims_for_anat)
    mod_l = (module or "").strip().lower()
    # style_palette is shared with the additive rubric, so it cannot by itself mean "this is UI".
    _ui_icon_dim_keys = (
        "nine_slice_structure",
        "glyph_silhouette",
        "squircle_safe_zone",
        "rgba_pipeline_compliance",
        "state_suite_cohesion",
        "silhouette",
        "stroke_palette",
        "studio_light",
        "alpha",
        "no_text",
        "stroke_consistency",
        "visual_weight",
        "optical_center",
        "recognizability",
    )
    looks_like_ui_icon_rubric = bool(
        isinstance(dims_for_anat, dict)
        and dims_for_anat
        and "perspective_anatomy" not in dims_for_anat
        and any(k in dims_for_anat for k in _ui_icon_dim_keys)
    )
    body_subject = subject_kind in {"humanoid", "creature", "both", "mechanical", "generic"}
    # Icon and UI rubrics have no anatomy axis. skill_additive on a person still fail-closes.
    icon_ui_rubric = rubric_mode in {"ui_5d", "app_icon_5d", "icon_prop_5d", "icon_svg_5d"}
    skip_anatomy_veto = (
        subject_kind == "ui"
        or mod_l in ("ui", "icon")
        or mod_l.startswith(("ui.", "icon."))
        or looks_like_ui_icon_rubric
        or icon_ui_rubric
        or (rubric_mode in NON_ANATOMY_RUBRICS and not body_subject)
    )
    if subject_kind == "scene" and collapse_marked(defects or ""):
        skip_anatomy_veto = False
    if subject_kind == "scene":
        structure_ok = scene_structure_ok_for_stop(
            dims_for_anat, defects or "", floor=anatomy_floor
        )
    else:
        structure_ok = anatomy_ok_for_stop(dims_for_anat, anatomy_floor)
    anatomy_veto_blocked = False
    if not skip_anatomy_veto and not structure_ok:
        anatomy_veto_blocked = True
        passed = False
        if anat_val is not None:
            calibrated = min(float(calibrated), float(anat_val))
        else:
            calibrated = min(float(calibrated), round(target_th - 0.05, 2))
        if anat_val is None:
            warn = (
                f"解剖硬伤一票否决：缺少 perspective_anatomy 维（fail-closed），"
                f"总分达线仍禁止停机（门槛 ≥{anatomy_floor}）"
            )
            anat_fix = clause("missing_dim", "zh")
        elif subject_kind == "scene" and anat_val < anatomy_floor:
            warn = (
                f"场景结构 {anat_val:.1f} < {anatomy_floor}，禁止停机"
            )
            anat_fix = clause("scene_fix", "zh")
        elif subject_kind == "scene":
            warn = (
                f"场景缺陷写了结构塌缩，透视 {anat_val:.1f} 仍禁止停机"
            )
            anat_fix = clause("scene_fix", "zh")
        else:
            warn = (
                f"解剖硬伤一票否决：透视与解剖 {anat_val:.1f} < {anatomy_floor}，"
                f"总分达线仍禁止停机；下一轮优先修结构"
            )
            if subject_kind == "creature":
                anat_fix = clause("creature_fix", "zh")
            elif subject_kind == "mechanical":
                anat_fix = clause("mech_fix", "zh")
            else:
                anat_fix = clause("anatomy", "zh")
        if warn not in audit_res["warnings"]:
            audit_res["warnings"].append(warn)
        if anat_fix and anat_fix not in str(defects or ""):
            defects = f"{defects}；{anat_fix}".strip("； ") if defects else anat_fix
        if not next_fix or "已达标" in str(next_fix):
            next_fix = anat_fix

    ui_shell_veto_blocked = False
    clone_subject_veto_blocked = False
    ref_analysis_blob = scale_prof.get("ref_analysis") or ""
    eff_goal = goal or str(scale_prof.get("goal") or "")
    eff_ref_img = ref_image or str(scale_prof.get("ref_image") or "")
    if passed and not ui_shell_structure_ok_for_stop(
        goal=eff_goal,
        ref_analysis=str(ref_analysis_blob),
        module=module,
        defects=defects or "",
        dims=dims_for_anat,
    ):
        ui_shell_veto_blocked = True
        passed = False
        shell_dim = None
        if isinstance(dims_for_anat, dict):
            for key in ("nine_slice_structure", "composition"):
                try:
                    val = float(dims_for_anat[key])
                except (KeyError, TypeError, ValueError):
                    continue
                if val < 8.5 and (shell_dim is None or val < shell_dim):
                    shell_dim = val
        calibrated = min(float(calibrated), 8.85 if shell_dim is None else shell_dim)
        warn = (
            "UI弹框母版结构一票否决：内容区不得回声参考主体/礼盒，"
            "或九宫格/构图结构分不足；总分达线仍禁止停机"
        )
        if warn not in audit_res["warnings"]:
            audit_res["warnings"].append(warn)
        shell_fix = "只清空内容区：大块留白可拉伸，删礼盒/道具插画，保留 chrome 与符号钮"
        if shell_fix not in str(defects or ""):
            defects = f"{defects}；{shell_fix}".strip("； ") if defects else shell_fix
        if not next_fix or "已达标" in str(next_fix):
            next_fix = shell_fix

    if passed and not clone_subject_structure_ok_for_stop(
        goal=eff_goal,
        ref_analysis=str(ref_analysis_blob),
        module=module,
        ref_image=eff_ref_img,
        defects=defects or "",
        dims=dims_for_anat,
    ):
        clone_subject_veto_blocked = True
        passed = False
        clone_dim = None
        if isinstance(dims_for_anat, dict) and dims_for_anat.get("composition") is not None:
            try:
                comp_now = float(dims_for_anat["composition"])
            except (TypeError, ValueError):
                comp_now = None
            if comp_now is not None and comp_now < 6.0:
                clone_dim = comp_now
        calibrated = min(float(calibrated), 8.85 if clone_dim is None else clone_dim)
        warn = (
            "Clone 题材结构一票否决：不得复制参考主体；"
            "总分达线仍禁止停机"
        )
        if warn not in audit_res["warnings"]:
            audit_res["warnings"].append(warn)
        subj_fix = "只垫参考锁材质：新主体必须独占画面，删礼盒/参考 prop 外形"
        if subj_fix not in str(defects or ""):
            defects = f"{defects}；{subj_fix}".strip("； ") if defects else subj_fix
        if not next_fix or "已达标" in str(next_fix):
            next_fix = subj_fix

    needs_flawlessness = rubric_mode in {
        "general_5d",
        "ui_5d",
        "app_icon_5d",
        "icon_prop_5d",
        "icon_svg_5d",
        "skill_additive_5d",
    }
    if (
        passed
        and needs_flawlessness
        and isinstance(dims_for_anat, dict)
        and "flawlessness" not in dims_for_anat
    ):
        passed = False
        warn = "缺无瑕疵这一维，六维没齐，不能停"
        if warn not in audit_res["warnings"]:
            audit_res["warnings"].append(warn)

    if not passed and next_fix_is_weak(next_fix):
        hint = reflow_fix_text(
            defects=[str(defects or "")],
            dims=dims_for_anat,
            api_scale=str(scale_prof.get("scale") or "medium"),
            recompose_dir=str(scale_prof.get("recompose_dir") or ""),
            intent=str(next_fix or ""),
            lang="zh",
        )
        if hint:
            next_fix = hint
    if not passed:
        next_fix = reconcile_fix_with_subject(next_fix, subject_kind, dims_for_anat)

    should_continue_next_round = bool((not passed) and (round_num < max_rounds))
    if passed:
        decision = "STOP_TARGET_REACHED"
    elif should_continue_next_round:
        decision = "CONTINUE_NEXT_ROUND"
    else:
        decision = "STOP_MAX_ROUNDS"

    return {
        "image_path": image_path,
        "resolved_path": str(p) if traits.get("exists") else image_path,
        "image_verification": traits,
        "scale": scale_prof.get("scale", "medium"),
        "target_score_threshold": target_th,
        "round_num": int(round_num),
        "max_rounds": max_rounds,
        "min_rounds_before_stop": min_rounds,
        "dims": eff_dims,
        "dims_parsed": audit_res["dims_parsed"],
        "anatomy_score": anat_val,
        "anatomy_floor": anatomy_floor,
        "anatomy_veto_blocked": anatomy_veto_blocked,
        "ui_shell_veto_blocked": ui_shell_veto_blocked,
        "clone_subject_veto_blocked": clone_subject_veto_blocked,
        "subject_kind": subject_kind,
        "rubric_mode": rubric_mode,
        "weighted_score": (
            round(float(calibrated), 2)
            if audit_res.get("weighted_score") is not None
            else None
        ),
        "raw_score": audit_res["raw_score"],
        "calibrated_score": round(float(calibrated), 2),
        "defects": defects,
        "strengths": eff_strengths,
        "next_fix": "已达标，无需继续叠加" if passed else next_fix,
        "audit_warnings": audit_res["warnings"],
        "stagnated": audit_res["stagnated"],
        "image_gate_blocked": image_gate_blocked,
        "early_stop_blocked": early_stop_blocked,
        "judge_source": judge_source,
        "remote_vlm": remote_meta,
        "passed": passed,
        "should_continue_next_round": should_continue_next_round,
        "ready_to_finish": passed or (not should_continue_next_round),
        "decision": decision,
    }



