"""Automatic VLM / rubric judge for a single image."""
from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from ._time import _now_cst

from .prompt_scale import DEFAULT_MAX_ROUNDS, DEFAULT_THRESHOLD, get_converge_scale_profile
from .scoring import audit_score_inflation, defects_are_substantive, parse_5d_dims
from .image_gates import _aspect_relation, _inspect_image_physical_traits, resolve_case_config
from .validate_params import _physical_image_gate
from .absolute_5d_agent_rubric import AGENT_JUDGE_SOURCE, annotate_advisory_offline

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
    Independent 5D VLM Judge & anti-inflation verifier (Step 2B — strictly decoupled from image generation):
    - Takes ONLY the finished `image_path` and independent VLM 5D observations (`dims`, `defects`, `next_fix`).
    - Has NO access to the generation prompt or any generator self-assessment (`raw_score` is never trusted over 5D weighted calculation).
    - Enforces `scale_prof["dim_weights"]`, `audit_score_inflation()`, and the low-scale pose redline (`allow_action_pose_change=False`).
    - By default (`require_image=True`) a missing / blank / tiny file cannot reach STOP_TARGET_REACHED.
    - If `vlm_judge` API key is configured, calls the remote vision model first.
    - If no key: current multimodal Agent scores Absolute-5D via CLI `dims`/`defects`
      (`agent_absolute_5d`); pixel offline scorer is **advisory only**. Threshold stays
      scale profile (default 9.6) — no no-key hard STOP / 8.50 early exit.
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
    offline_meta: dict[str, Any] = {}
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

    # No independent VLM → Agent Absolute-5D (same 9.6 gate). Pixel offline = advisory only.
    if judge_source != "independent_vlm":
        if dims.strip():
            judge_source = AGENT_JUDGE_SOURCE
        else:
            judge_source = "agent_self_judge"
        if p.is_file():
            try:
                import sys as _sys

                _scripts = Path(__file__).resolve().parent.parent / "scripts"
                if str(_scripts) not in _sys.path:
                    _sys.path.insert(0, str(_scripts))
                from absolute_5d_scorer import absolute_5d as _offline_a5d  # noqa: WPS433

                offline = _offline_a5d(
                    str(p),
                    api_scale=str(scale_prof.get("scale") or "medium"),
                    prompt_mode=str(scale_prof.get("prompt_mode") or ""),
                    ref_path=str(ref_image or scale_prof.get("ref_image") or "") or None,
                )
                offline_meta = {
                    "version": (offline.get("meta") or {}).get("version"),
                    "score": offline.get("score"),
                    "coverage": offline.get("coverage"),
                    "rankable": (offline.get("meta") or {}).get("rankable"),
                    "contract": (offline.get("meta") or {}).get("contract"),
                    "role": "advisory_only",
                }
                note = annotate_advisory_offline(
                    offline.get("score"), offline.get("coverage")
                )
                remote_meta = {
                    **remote_meta,
                    "offline_advisory": offline_meta,
                    "source": judge_source,
                    "offline_advisory_note": note,
                }
                # Hint only — never splice into defects (would defeat soft-defect STOP gate).
                # Warning path below already surfaces annotate_advisory_offline(...).
            except Exception as exc:  # noqa: BLE001
                offline_meta = {"error": str(exc), "role": "advisory_only"}
                remote_meta = {
                    **remote_meta,
                    "offline_advisory": offline_meta,
                    "source": judge_source,
                }

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
    audit_res = audit_score_inflation(
        float(raw_score) if (raw_score is not None and float(raw_score) > 0) else 0.0,
        eff_dims,
        defects,
        prev_score,
        scale_prof,
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
            f"Agent Absolute-5D 已采纳（门槛 {target_th}；像素离线仅为旁证）"
        )
    if offline_meta.get("score") is not None and judge_source != "independent_vlm":
        audit_res["warnings"].append(
            annotate_advisory_offline(offline_meta.get("score"), offline_meta.get("coverage"))
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
        warn = "无独立 VLM 时须由本模型按 Absolute-5D 给出 dims；缺五维分拒绝达标"
        if warn not in audit_res["warnings"]:
            audit_res["warnings"].append(warn)

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
            next_fix = str(scale_prof.get("best_direction_hint") or "按本档最优方向继续叠加光影或构图跃升")

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
        "weighted_score": audit_res["weighted_score"],
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



