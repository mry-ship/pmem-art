"""Converge state machine and CLI cmd_converge."""
from __future__ import annotations

import json
import os
import re
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from ._time import _now_cst


def _write_session_json(sf: Path, sess: dict[str, Any]) -> None:
    """Atomic session write (tmp + os.replace) to reduce parallel RMW corruption."""
    sf.parent.mkdir(parents=True, exist_ok=True)
    tmp = sf.with_suffix(sf.suffix + ".tmp")
    tmp.write_text(json.dumps(sess, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, sf)

from .prompt_scale import (
    DEFAULT_MAX_ROUNDS,
    DEFAULT_THRESHOLD,
    FAST_SOFT_THRESHOLD,
    _constraint_tail,
    _prompt_change_ratio,
    _recompose_change_evidence,
    build_r1_structure_floor,
    classify_subject,
    compose_continuation_prompt,
    compose_style_first_prompt,
    get_converge_scale_profile,
    strip_redline_tags_from_generation_text,
)
from .image_gates import _inspect_image_physical_traits, resolve_case_config
from .validate_params import _physical_image_gate, _round_counts_as_passed, validate_converge_params
from .judge_auto import auto_vlm_judge_image
from .absolute_5d_agent_rubric import agent_absolute_5d_judge_prompt
from .converge_loop import clear_active_session, mark_active_session
from .converge_policy import (
    DEFAULT_ANATOMY_FLOOR,
    DEFAULT_EARLY_STOP_MIN_ROUND,
    DEFAULT_PAD_MODE,
    DEFAULT_PLATEAU_ROUNDS,
    DEFAULT_REGRESSION_DROP,
    coerce_dims_dict,
    decide_round_stop,
    round_passes_structure_gates,
)


def _norm_ref_paths(paths: Any) -> list[str]:
    """Stable lowercase resolved paths for comparing suggested vs actual pads."""
    if paths is None:
        return []
    if isinstance(paths, str):
        raw = [p.strip() for p in paths.split(",") if p.strip()]
    else:
        raw = [str(p).strip() for p in paths if str(p).strip()]
    out: list[str] = []
    for item in raw:
        try:
            out.append(str(Path(item).resolve()).lower())
        except OSError:
            out.append(item.replace("\\", "/").lower())
    return out


def converge_start(
    root: Path,
    data: dict[str, Any],
    *,
    session_id: str = "latest",
    goal: str = "",
    module: str = "",
    ref_image: str = "",
    ref_analysis: str = "",
    aspect_ratio: str = "",
    reference_image_paths: list[str] | tuple[str, ...] | str | None = None,
    threshold: float = DEFAULT_THRESHOLD,
    max_rounds: int = DEFAULT_MAX_ROUNDS,
    converge_mode: str = "quality",
    scale: str = "",
    recompose_dir: str = "",
    draft_ok: bool = False,
    verbose: bool = False,
    silent: bool = False,
) -> dict[str, Any]:
    """
    Step 1 (Start & Reference Inheritance Step):
    Initializes the converge session, inspects `ref_image` physical traits, automatically infers
    default `aspect_ratio` and `reference_image_paths` (pad image) from the reference image,
    and runs parameter validation.
    """
    rc = cmd_converge(
        root,
        data,
        "start",
        session_id=session_id,
        goal=goal,
        module=module,
        ref_image=ref_image,
        ref_analysis=ref_analysis,
        aspect_ratio=aspect_ratio,
        reference_image_paths=reference_image_paths,
        threshold=threshold,
        max_rounds=max_rounds,
        converge_mode=converge_mode,
        scale=scale,
        recompose_dir=recompose_dir,
        draft_ok=draft_ok,
        verbose=verbose,
        silent=silent,
    )
    sf = _session_file(root, session_id)
    sess = json.loads(sf.read_text(encoding="utf-8")) if sf.exists() else {}
    return {
        "exit_code": rc,
        "session_id": session_id,
        "status": sess.get("status"),
        "pipeline_mode": sess.get("pipeline_mode"),
        "default_aspect_ratio": sess.get("default_aspect_ratio", ""),
        "default_reference_image_paths": sess.get("default_reference_image_paths", []),
        "param_validation": sess.get("param_validation", {}),
        "session": sess,
    }


def converge_generate(
    root: Path,
    data: dict[str, Any],
    *,
    session_id: str = "latest",
    round_num: int = 0,
    prompt: str = "",
    image: str = "",
    generate_cmd: str = "",
    scale: str = "",
    recompose_dir: str = "",
    aspect_ratio: str = "",
    reference_image_paths: list[str] | tuple[str, ...] | str | None = None,
    goal: str = "",
    module: str = "",
    ref_image: str = "",
    ref_analysis: str = "",
    threshold: float = DEFAULT_THRESHOLD,
    max_rounds: int = DEFAULT_MAX_ROUNDS,
    converge_mode: str = "quality",
    draft_ok: bool = False,
    verbose: bool = False,
    silent: bool = False,
) -> dict[str, Any]:
    """
    Step 2 (Generate-Only Step):
    Strictly produces/registers the candidate image for round `round_num` with dynamic `prompt_directive`
    prepended (`compose_style_first_prompt`), automatically inheriting `aspect_ratio` and `reference_image_paths`
    from the reference image when not explicitly provided.
    Contains NO scoring, NO self-evaluation, and NO call to `auto_vlm_judge_image`.
    """
    rc = cmd_converge(
        root,
        data,
        "generate",
        session_id=session_id,
        goal=goal,
        module=module,
        ref_image=ref_image,
        ref_analysis=ref_analysis,
        threshold=threshold,
        max_rounds=max_rounds,
        round_num=round_num,
        image=image,
        generate_cmd=generate_cmd,
        prompt=prompt,
        converge_mode=converge_mode,
        scale=scale,
        recompose_dir=recompose_dir,
        aspect_ratio=aspect_ratio,
        reference_image_paths=reference_image_paths,
        draft_ok=draft_ok,
        verbose=verbose,
        silent=silent,
    )
    sf = _session_file(root, session_id)
    sess = json.loads(sf.read_text(encoding="utf-8")) if sf.exists() else {}
    last_round = (sess.get("rounds") or [-1])[-1] if sess.get("rounds") else {}
    return {
        "exit_code": rc,
        "session_id": session_id,
        "status": sess.get("status"),
        "ready_to_finish": False,
        "aspect_ratio": last_round.get("aspect_ratio", sess.get("default_aspect_ratio", "")),
        "reference_image_paths": last_round.get("reference_image_paths", sess.get("default_reference_image_paths", [])),
        "param_validation": last_round.get("param_validation", {}),
        "round": last_round,
    }


def converge_finish(
    root: Path,
    data: dict[str, Any],
    *,
    session_id: str = "latest",
    apply_memory: bool = True,
    verbose: bool = False,
    silent: bool = False,
) -> dict[str, Any]:
    """
    Finish & Settle Step:
    Settles the winning round after `STOP_TARGET_REACHED` (`score >= 9.50`), writes recipe/redline/reflection
    into `.memory-art`, and runs silent autopilot maintenance.
    By default prints the per-round score trail; pass silent=True (CLI --quiet) for one-line whisper.
    """
    rc = cmd_converge(
        root,
        data,
        "finish",
        session_id=session_id,
        apply_memory=apply_memory,
        verbose=verbose,
        silent=silent,
    )
    sf = _session_file(root, session_id)
    sess = json.loads(sf.read_text(encoding="utf-8")) if sf.exists() else {}
    return {
        "exit_code": rc,
        "session_id": session_id,
        "status": sess.get("status"),
        "winner": sess.get("winner"),
        "rounds_to_converge": sess.get("rounds_to_converge"),
        "session": sess,
    }


def converge_judge(
    root: Path,
    data: dict[str, Any],
    *,
    session_id: str = "latest",
    round_num: int = 0,
    image: str = "",
    dims: str = "",
    strengths: str = "",
    defects: str = "",
    next_fix: str = "",
    scale: str = "",
    recompose_dir: str = "",
    threshold: float = DEFAULT_THRESHOLD,
    max_rounds: int = DEFAULT_MAX_ROUNDS,
    converge_mode: str = "quality",
    draft_ok: bool = False,
    verbose: bool = False,
    silent: bool = False,
) -> dict[str, Any]:
    """
    Step 2B (Independent VLM Scoring Step):
    Takes the finished `image` from Step 2A and runs `auto_vlm_judge_image` independently.
    Has NO `generate_cmd`, NO generation `prompt` parameter, and NO generator self-assessment score.
    """
    rc = cmd_converge(
        root,
        data,
        "judge",
        session_id=session_id,
        threshold=threshold,
        max_rounds=max_rounds,
        round_num=round_num,
        image=image,
        dims=dims,
        strengths=strengths,
        defects=defects,
        next_fix=next_fix,
        converge_mode=converge_mode,
        scale=scale,
        recompose_dir=recompose_dir,
        draft_ok=draft_ok,
        verbose=verbose,
        silent=silent,
    )
    sf = _session_file(root, session_id)
    sess = json.loads(sf.read_text(encoding="utf-8")) if sf.exists() else {}
    last_round = (sess.get("rounds") or [-1])[-1] if sess.get("rounds") else {}
    return {
        "exit_code": rc,
        "session_id": session_id,
        "status": sess.get("status"),
        "ready_to_finish": bool(sess.get("ready_to_finish")),
        "round": last_round,
    }


def converge_step(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """
    Deprecated combined entry point: strictly blocks combining image generation and scoring in one call.
    Call `converge_generate(...)` first (Step 2A), then `converge_judge(...)` (Step 2B).
    """
    raise RuntimeError(
        "Strict two-step separation enforced: image generation and VLM scoring cannot be combined in `converge_step`. "
        "Call `converge_generate(...)` (or `converge generate`) first, then `converge_judge(...)` (or `converge judge`)."
    )



def _session_file(root: Path, session_id: str = "latest") -> Path:
    d = root / ".memory-art" / "converge"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{session_id}.json"


def _plate_file(raw: str, root: Path) -> str:
    path = Path(raw)
    if not path.is_file():
        path = root / raw
    return str(path.resolve()) if path.is_file() else ""


def _best_plate(rounds: list, round_num: int, root: Path) -> tuple[str, str, int]:
    """Pad the highest-scoring earlier plate. A later worse plate does not replace it."""
    prior = [
        r for r in rounds
        if int(r.get("round") or 0) < int(round_num) and str(r.get("image") or "").strip()
    ]
    scored: list[tuple[float, int, str, str, dict]] = []
    unscored: list[tuple[int, str, str]] = []
    for row in prior:
        image = _plate_file(str(row.get("image") or "").strip(), root)
        if not image:
            continue
        fix = str(row.get("next_fix") or "").strip()
        if fix.startswith("已达标"):
            fix = ""
        number = int(row.get("round") or 0)
        try:
            score = float(row.get("score"))
        except (TypeError, ValueError):
            unscored.append((number, image, fix))
            continue
        scored.append((score, number, image, fix, row))
    if scored:
        _score, number, image, fix, _row = max(scored, key=lambda item: (item[0], item[1]))
        return image, fix, number
    if unscored:
        number, image, fix = max(unscored, key=lambda item: item[0])
        return image, fix, number
    return "", "", 0


def _round_dims_dict(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(row, dict):
        return None
    parsed = coerce_dims_dict(row.get("dims_parsed"))
    if parsed is not None:
        return parsed
    return coerce_dims_dict(row.get("dims"))


def _defect_text_copied(prev: str, curr: str) -> bool:
    """True when this round's defects are a paste of the previous round."""
    a = re.sub(r"\s+", "", (prev or "").strip().lower())
    b = re.sub(r"\s+", "", (curr or "").strip().lower())
    if len(b) < 16 or not a:
        return False
    if a == b:
        return True
    return (a in b or b in a) and min(len(a), len(b)) >= 24


def _style_jump_requested(scale: str = "", goal: str = "", flagged: bool = False) -> bool:
    if flagged:
        return True
    s = (scale or "").strip().lower()
    if s in {"recompose_bold", "bold", "style_jump"}:
        return True
    blob = goal or ""
    return any(tok in blob for tok in ("style_jump", "recompose_bold", "风格跳跃"))


def _resolve_pad_auto(
    rounds: list,
    round_num: int,
    root: Path,
    *,
    style_ref: str,
    pad_mode: str = DEFAULT_PAD_MODE,
    anatomy_floor: float = DEFAULT_ANATOMY_FLOOR,
    subject_kind: str = "",
    goal: str = "",
    module: str = "",
    ref_analysis: str = "",
    scale: str = "",
    style_jump: bool = False,
) -> tuple[str, str, int, bool, str]:
    """Pad policy: auto/ref always use the original style_ref. Fixes stay in the prompt.

    pad=previous is an explicit chain of the best plate. Style jump pads nothing.
    high/recompose may pad best plate only after round text proves camera changed.
    Returns (pad_image, fix, pad_round, continuation, reason).
    """
    del anatomy_floor, subject_kind, module, ref_analysis
    mode = (pad_mode or DEFAULT_PAD_MODE).lower().strip()
    carry_image, carry_fix, carry_round = _best_plate(rounds, round_num, root)
    style = (style_ref or "").strip()
    if _style_jump_requested(scale, goal, style_jump):
        return "", carry_fix, 0, False, "style_jump：不垫风格参考，也不链成图"
    if (scale or "").strip().lower() in {"high", "recompose"}:
        best_img, best_fix, best_round, best_score = "", carry_fix, 0, -1.0
        for row in rounds:
            if not isinstance(row, dict):
                continue
            if int(row.get("round") or 0) >= int(round_num):
                continue
            blob = " ".join(str(row.get(k) or "") for k in ("defects", "next_fix", "prompt"))
            if any(n in blob for n in ("不改机位", "没改机位", "不要改机位", "别改机位")):
                continue
            if not any(k in blob for k in ("换机位", "改了机位", "重构机位", "机位已换")):
                continue
            image = str(row.get("image") or "").strip()
            if not image or not Path(image).is_file():
                continue
            try:
                score = float(row.get("score") or 0)
            except (TypeError, ValueError):
                score = 0.0
            if score >= best_score:
                best_img = image
                best_fix = str(row.get("next_fix") or "") or carry_fix
                best_round = int(row.get("round") or 0)
                best_score = score
        if best_img:
            return best_img, best_fix, best_round, True, "pad=changed_camera（机位已换，垫换过机位的最高分）"

    if mode == "previous" and carry_image:
        return carry_image, carry_fix, carry_round, True, "pad=previous"
    why = "pad=ref" if mode == "ref" else "pad=auto→style_ref（每轮垫最初参考，修正只写进提示词）"
    if not style and not carry_image:
        why = "no_prior_plate"
    return style, carry_fix, 0, False, why


def cmd_converge(
    root: Path,
    data: dict[str, Any],
    action: str,
    *,
    session_id: str = "latest",
    goal: str = "",
    module: str = "",
    ref_image: str = "",
    ref_analysis: str = "",
    threshold: float = DEFAULT_THRESHOLD,
    max_rounds: int = DEFAULT_MAX_ROUNDS,
    round_num: int = 0,
    image: str = "",
    generate_cmd: str = "",
    score: float = 0.0,
    dims: str = "",
    strengths: str = "",
    defects: str = "",
    next_fix: str = "",
    prompt: str = "",
    apply_memory: bool = True,
    converge_mode: str = "quality",
    scale: str = "",
    recompose_dir: str = "",
    aspect_ratio: str = "",
    reference_image_paths: list[str] | tuple[str, ...] | str | None = None,
    draft_ok: bool = False,
    verbose: bool = False,
    silent: bool = False,
    lock_text: str = "",
    medium_family: str = "",
    contract: str = "",
    skip_route_gate: bool = False,
) -> int:
    """
    converge_mode: quality (default, dynamic threshold per scale, max 4 rounds, stop ≥9.5 or best-of-4) | fast (warm-start fast-track hints).
    draft_ok: if True (user said 草稿/fast), final accept may use soft threshold in fast mode.
    silent: default False — 默认打印评分履历；True/--quiet 仅一行结论；记忆写入始终后台静默。verbose=True 等同强制打印全量报告。
    lock_text: artist one-liner to loosen/tighten per-dim locks (e.g. 「构图松一点」→ show 95%→75%).
    skip_route_gate: 跳过「开画前必须先 route」闸门（仅点名调试；默认 False）。
    """
    if verbose:
        silent = False
    sf = _session_file(root, session_id)
    converge_mode = (converge_mode or "quality").lower()
    if converge_mode not in ("quality", "fast"):
        converge_mode = "quality"
    cfg_conv = (data.get("config") or {}).get("converge") if isinstance(data, dict) else {}
    if not isinstance(cfg_conv, dict):
        cfg_conv = {}
    requested_scale = (scale or cfg_conv.get("default_scale") or "medium").strip().lower()
    eff_scale = requested_scale
    scale_prof = get_converge_scale_profile(
        eff_scale,
        recompose_dir=recompose_dir,
        goal=goal,
        ref_analysis=ref_analysis,
        ref_image=ref_image,
        module=module,
        medium_family=medium_family,
        contract=contract,
    )
    style_jump_requested = _style_jump_requested(requested_scale, goal or "")
    eff_scale = scale_prof["scale"]

    if action == "start":
        import os as _os

        env_skip = _os.environ.get("PMEM_ART_SKIP_ROUTE_GATE", "").strip().lower() in (
            "1",
            "true",
            "yes",
        )
        if not skip_route_gate and not env_skip:
            from .route_gate import check_route_gate

            ok_gate, gate_msg = check_route_gate(root, goal=goal or "")
            if not ok_gate:
                print(f"❌ [路由闸门] {gate_msg}")
                return 1
            if gate_msg and "提醒" in gate_msg:
                print(f"⚠️ [路由闸门] {gate_msg}")
            else:
                print(f"✅ [路由闸门] {gate_msg}")
        if eff_scale == "recompose" and not str(recompose_dir or "").strip():
            print("❌ [档位合同] recompose 必须提供 --recompose-dir，写明新机位或景别。")
            return 1
        if str(recompose_dir or "").strip() and eff_scale != "recompose":
            print(f"⚠️ [档位合同] 当前是 {eff_scale}，已忽略 --recompose-dir。要改构图请把 --scale 设为 recompose。")
        if not module and goal:
            from feedback import infer_module_from_text
            module = infer_module_from_text(goal, data)

        from improve import build_warm_start_pack, print_warm_start
        warm = build_warm_start_pack(root, data, module=module or "brand.WorldStyle", goal=goal or "")
        print_warm_start(warm)

        fast_track = bool(converge_mode == "fast" and warm.get("fast_track_eligible"))
        scale_target_th = float(scale_prof.get("target_score_threshold", DEFAULT_THRESHOLD))
        base_th = scale_target_th if abs(float(threshold) - DEFAULT_THRESHOLD) < 1e-6 else float(threshold)
        eff_threshold = base_th
        if draft_ok and converge_mode == "fast":
            eff_threshold = min(eff_threshold, FAST_SOFT_THRESHOLD)

        default_ar = str(aspect_ratio or "").strip()
        default_ref_paths: list[str] = []
        ref_traits: dict[str, Any] = {}
        start_param_val: dict[str, Any] = {}
        if ref_image or reference_image_paths:
            try:
                start_param_val = validate_converge_params(
                    session_id=session_id,
                    scale=eff_scale,
                    ref_image=ref_image,
                    aspect_ratio=default_ar,
                    reference_image_paths=reference_image_paths,
                    root=root,
                    three_step_stage="step1_start",
                )
                default_ar = start_param_val["aspect_ratio"]
                default_ref_paths = start_param_val["reference_image_paths"]
                if default_ref_paths:
                    ref_traits = _inspect_image_physical_traits(Path(default_ref_paths[0]))
            except (FileNotFoundError, ValueError) as exc:
                print(f"❌ [Step 1 · 会话启动参数校验拦截] {exc}")
                return 1

        sess = {
            "session_id": session_id,
            "started_at": _now_cst().strftime("%Y-%m-%d %H:%M:%S UTC+8"),
            "goal": goal or "未命名生图任务",
            "module": module or "brand.WorldStyle",
            "mode": "ref_image_guided" if ref_image else "text_guided",
            "converge_mode": converge_mode,
            "quality_mode": converge_mode,
            "stop_policy": "dynamic_threshold",
            "merged_generate_and_judge": False,
            "three_step_separation": True,
            "pipeline_mode": "strict_three_step_start_generate_judge",
            "scale": eff_scale,
            "style_jump": bool(style_jump_requested),
            "scale_profile": scale_prof,
            "medium_family": str(scale_prof.get("medium_family") or "generic"),
            "contract": "split" if str(contract or "").strip().lower() == "split" else "",
            "target_score_threshold": base_th,
            "recompose_dir": recompose_dir,
            "fast_track": fast_track,
            "draft_ok": bool(draft_ok),
            "ref_image": ref_image,
            "ref_analysis": ref_analysis,
            "default_aspect_ratio": default_ar,
            "default_reference_image_paths": default_ref_paths,
            "aspect_ratio": default_ar,
            "reference_image_paths": default_ref_paths,
            "ref_physical_traits": ref_traits,
            "param_validation": start_param_val,
            "step_trace": ["step1_start"],
            "threshold": eff_threshold,
            "accept_threshold": base_th,
            "max_rounds": int(max_rounds),
            "ready_to_finish": False,
            "status": "running",
            "rounds": [],
            "warm_start": warm,
            "lessons_all": [],
            "dim_lock_overrides": {},
            "dim_lock_history": [],
            "pad_mode": str(cfg_conv.get("pad_mode") or DEFAULT_PAD_MODE),
            "anatomy_floor": float(cfg_conv.get("anatomy_floor") or DEFAULT_ANATOMY_FLOOR),
            "early_stop_min_round": int(
                cfg_conv.get("early_stop_min_round") or DEFAULT_EARLY_STOP_MIN_ROUND
            ),
            "regression_drop": float(
                cfg_conv.get("regression_drop") or DEFAULT_REGRESSION_DROP
            ),
        }
        if lock_text or goal:
            from skills_kit.prompt_scale import merge_dim_lock_overrides, format_dim_lock_summary_zh
            ov = merge_dim_lock_overrides(eff_scale, {}, goal or "", lock_text or "")
            if ov:
                sess["dim_lock_overrides"] = ov
                sess["dim_lock_history"].append(
                    {"at": "start", "text": lock_text or goal, "overrides": dict(ov)}
                )
                print(f"🔓 画师锁定微调已生效：{format_dim_lock_summary_zh(eff_scale, ov)}")
        _write_session_json(sf, sess)
        mark_active_session(root, session_id)
        print(
            f"🎯 [收敛会话已启动] 模块: {sess['module']} | 模式: {converge_mode} | 强度(scale): {eff_scale} ({scale_prof['label']})"
            f"{' · FAST-TRACK' if fast_track else ''} | 动态达标线: >= {sess['accept_threshold']} 分即停"
            f"{'（草稿软线 ' + str(eff_threshold) + '）' if draft_ok else ''} | 最大兜底轮次: {sess['max_rounds']}"
            f" | 最早停机轮次: {int(scale_prof.get('min_rounds_before_stop') or 1)}"
            f" | 媒介: {sess.get('medium_family')}"
            f"{' | 合同: split' if sess.get('contract') == 'split' else ''}"
        )
        print(f"🎚️  Scale 内部权重与约束: weights={scale_prof['dim_weights']} | budget={scale_prof['next_fix_budget']}")
        print(f"🧭 Scale 指令: {scale_prof['prompt_directive']}")
        hint = str(scale_prof.get("best_direction_hint") or "").strip()
        if hint:
            print(f"✨ 最优方向（按档加法，勿当第二份DNA锁）: {hint}")
        print(f"🧷 本档保留集: {scale_prof.get('retention_set')}")
        tail = _constraint_tail(scale_prof)
        if tail:
            print(f"📌 约束写在生成词末尾: {tail}")
        if fast_track:
            print(
                f"⚡ Fast-track：warm-start 置信 {warm.get('confidence')} 高。"
                f"仍须每张打分；若 score≥{FAST_SOFT_THRESHOLD} 且与上轮 Δ 很小可少重生，"
                f"但最终采纳默认仍要 ≥{base_th}（除非用户明确草稿/fast）。"
            )
        if ref_image:
            print(f"🖼️  垫图/参考图模式: {ref_image}")
            if ref_analysis:
                print(f"🔍 参考图解构基准: {ref_analysis}")
        print("\n👉 Agent：请先执行第 1 步 `converge generate`（仅生图，不打分），生成完成后再独立执行第 2 步 `converge judge`（独立 VLM 审图打分）。")
        return 0

    if not sf.exists():
        print(
            f"❌ 未找到收敛会话 `{session_id}`。请先显式启动：\n"
            f"   python3 pmem_art.py converge start --id {session_id} "
            f"[--goal ...] [--module brand.WorldStyle] [--ref-image ...] [--scale medium]"
        )
        return 1

    sess = json.loads(sf.read_text(encoding="utf-8"))
    if action == "discuss":
        body = (prompt or goal or "").strip()
        if not body:
            print("❌ converge discuss 需要 --prompt，把这一稿正文写进去。")
            return 1
        notes = [d for d in (sess.get("discussions") or []) if int(d.get("round") or 0) != (round_num or 0)]
        n = round_num if round_num > 0 else (len(sess.get("discussions") or []) + 1)
        notes = [d for d in notes if int(d.get("round") or 0) != n]
        notes.append({
            "round": n,
            "prompt": body,
            "strengths": (strengths or "").strip(),
            "defects": (defects or "").strip(),
            "next_fix": (next_fix or "").strip(),
        })
        notes.sort(key=lambda d: int(d.get("round") or 0))
        sess["discussions"] = notes
        _write_session_json(sf, sess)
        print(f"📝 已记下论述第 {n} 稿。finish 的过程板会列出全部 {len(notes)} 稿。")
        return 0

    th = float(sess.get("accept_threshold") or sess.get("threshold", DEFAULT_THRESHOLD))
    soft_th = FAST_SOFT_THRESHOLD if sess.get("fast_track") or sess.get("converge_mode") == "fast" else th
    mr = int(sess.get("max_rounds", DEFAULT_MAX_ROUNDS))
    rounds: list[dict[str, Any]] = sess.get("rounds") or []

    def _apply_lock_texts(*texts: str, source: str = "") -> dict[str, int]:
        from skills_kit.prompt_scale import merge_dim_lock_overrides, format_dim_lock_summary_zh
        scale_now = str(sess.get("scale") or "medium")
        before = dict(sess.get("dim_lock_overrides") or {})
        merged = merge_dim_lock_overrides(scale_now, before, *[t for t in texts if t])
        if merged != before:
            sess["dim_lock_overrides"] = merged
            hist = list(sess.get("dim_lock_history") or [])
            hist.append(
                {
                    "at": source or action,
                    "text": " | ".join(t for t in texts if t)[:240],
                    "overrides": dict(merged),
                }
            )
            sess["dim_lock_history"] = hist[-12:]
            _write_session_json(sf, sess)
            print(f"🔓 画师锁定微调：{format_dim_lock_summary_zh(scale_now, merged)}")
        return dict(sess.get("dim_lock_overrides") or {})

    if action == "lock":
        blob = (lock_text or goal or next_fix or prompt or "").strip()
        if not blob:
            print("❌ 请提供画师原话，例如：`converge lock --lock-text \"构图松一点\"`")
            return 1
        ov = _apply_lock_texts(blob, source="lock")
        from skills_kit.prompt_scale import format_dim_lock_levels_zh
        print("\n".join(format_dim_lock_levels_zh(str(sess.get("scale") or "medium"), ov)))
        return 0

    if action == "step":
        print(
            "❌ [架构隔离拦截] 已禁用单次合并调用 `converge step`（禁止在同一调用/同一回合内同时执行生图与自我打分）！\n"
            "   👉 请严格分两步调用：\n"
            "      1) 生图阶段（无打分、无VLM裁判）：`python3 pmem_art.py converge generate --id <id> --round <n> --image <path> --prompt <prompt> [--generate-cmd ...]`\n"
            "      2) 独立审图阶段（无生成Prompt自评）：`python3 pmem_art.py converge judge --id <id> --round <n> --image <path> --dims <5D> --defects <...> --next-fix <...>`"
        )
        return 1

    if action == "next":
        pending = [
            r for r in rounds
            if not r.get("judged") and str(r.get("image") or "").strip()
        ]
        if pending:
            pending_no = int(pending[-1].get("round") or 0)
            print(f"第 {pending_no} 轮还没审图。先 `converge judge --id {session_id} --round {pending_no}`，再 `converge next`。")
            return 1
        judged_nums = [int(r.get("round") or 0) for r in rounds if r.get("judged")]
        nxt = (max(judged_nums) if judged_nums else 0) + 1
        image, fix, number = _best_plate(rounds, nxt, root)
        prof = get_converge_scale_profile(
            sess.get("scale", "medium"),
            recompose_dir=sess.get("recompose_dir", ""),
            goal=sess.get("goal", ""),
            ref_analysis=sess.get("ref_analysis", ""),
            ref_image=sess.get("ref_image", ""),
            module=sess.get("module", ""),
            medium_family=str(sess.get("medium_family") or ""),
            contract=str(sess.get("contract") or ""),
        )
        if not image:
            ref = str(sess.get("ref_image") or "").strip()
            if _style_jump_requested(str(sess.get("scale") or ""), str(sess.get("goal") or ""), bool(sess.get("style_jump"))):
                print("第 1 轮是风格跳跃，不垫旧风格参考。")
            else:
                print("还没有可垫的成图。第 1 轮垫最初的参考图。" + (f"\n垫图：{ref}" if ref else ""))
            return 0
        scored = next((r.get("score") for r in rounds if int(r.get("round") or 0) == number), None)
        score_bit = f"{float(scored):.2f} 分" if scored is not None else "尚未打分"
        style_ref = str(sess.get("ref_image") or "").strip()
        pad_image, pad_fix, pad_round, continuation, pad_reason = _resolve_pad_auto(
            rounds,
            nxt,
            root,
            style_ref=style_ref,
            pad_mode=str(sess.get("pad_mode") or DEFAULT_PAD_MODE),
            anatomy_floor=float(sess.get("anatomy_floor") or DEFAULT_ANATOMY_FLOOR),
            subject_kind=classify_subject(
                goal=str(sess.get("goal") or ""),
                ref_analysis=sess.get("ref_analysis") or "",
                ref_image=style_ref,
                module=str(sess.get("module") or ""),
            ),
            goal=str(sess.get("goal") or ""),
            module=str(sess.get("module") or ""),
            ref_analysis=str(sess.get("ref_analysis") or ""),
            scale=str(sess.get("scale") or ""),
            style_jump=bool(sess.get("style_jump")),
        )
        if continuation and pad_image:
            print(
                f"下一轮第 {nxt} 轮，策略建议垫第 {pad_round} 轮（{score_bit}）：{pad_image}\n"
                f"策略：{pad_reason}\n"
                f"生图参考图只用这一张。\n"
                f"提示词：{compose_continuation_prompt(pad_fix or fix, prof)}"
            )
        elif not (pad_image or "").strip():
            print(
                f"下一轮第 {nxt} 轮不垫图。\n"
                f"策略：{pad_reason}\n"
                f"上轮成图不链（{score_bit}）：{image}\n"
                f"提示词仍带改点：{pad_fix or fix}"
            )
        else:
            shown = pad_image or style_ref or "（无风格参考）"
            print(
                f"下一轮第 {nxt} 轮，垫最初的参考图：{shown}\n"
                f"策略：{pad_reason}\n"
                f"上轮成图不链（{score_bit}）：{image}\n"
                f"提示词仍带改点：{pad_fix or fix}"
            )
        return 0

    if action == "generate":
        import subprocess

        if any([dims, defects, strengths]) or (score and float(score) > 0):
            print("❌ [生成与评分隔离拦截] `converge generate` 阶段严禁传入 score / dims / defects / strengths 等自评打分参数！")
            return 1

        r_no = round_num if round_num > 0 else (len(rounds) + 1)
        pending_unjudged = [
            r for r in rounds
            if not r.get("judged") and str(r.get("image") or "").strip()
        ]
        if pending_unjudged:
            pno = int(pending_unjudged[-1].get("round") or 0)
            if r_no > pno:
                print(
                    f"❌ 第 {pno} 轮还没 `converge judge`，不能开第 {r_no} 轮。"
                    f"先审第 {pno} 轮，不到 9.5 再出下一张。"
                )
                return 1
        already_passed = [r for r in rounds if _round_counts_as_passed(r, th, root=root)]
        if already_passed and r_no > already_passed[0].get("round", 1):
            p_r = already_passed[0]
            sess["status"] = "converged"
            sess["ready_to_finish"] = True
            sess["converged_at_round"] = p_r["round"]
            _write_session_json(sf, sess)
            print(
                f"🛑 [动态达标停机拦截] 会话已在第 {p_r['round']} 轮达到 {p_r['score']:.2f} >= {th:.2f} 达标停止，"
                f"禁止继续生成第 {r_no} 轮！请直接运行 `python3 pmem_art.py converge finish --id {session_id}`。"
            )
            return 0
        if r_no > mr:
            print(f"🛑 已超过最大轮次上限 ({mr} 轮)，请直接运行 `python3 pmem_art.py converge finish --id {session_id}` 结算最高分图。")
            return 1

        eff_ref_img = (ref_image or sess.get("ref_image") or "").strip()
        eff_ar = (aspect_ratio or sess.get("default_aspect_ratio") or sess.get("aspect_ratio") or "").strip()
        pad_mode = str(sess.get("pad_mode") or DEFAULT_PAD_MODE)
        subject_kind = classify_subject(
            goal=str(sess.get("goal") or goal or ""),
            ref_analysis=sess.get("ref_analysis") or "",
            ref_image=eff_ref_img,
            module=str(sess.get("module") or module or ""),
        )
        anatomy_floor = float(sess.get("anatomy_floor") or DEFAULT_ANATOMY_FLOOR)
        carry_image, carry_fix, carry_round, policy_continuation, pad_reason = _resolve_pad_auto(
            rounds,
            r_no,
            root,
            style_ref=eff_ref_img,
            pad_mode=pad_mode,
            anatomy_floor=anatomy_floor,
            subject_kind=subject_kind,
            goal=str(sess.get("goal") or goal or ""),
            module=str(sess.get("module") or module or ""),
            ref_analysis=str(sess.get("ref_analysis") or ref_analysis or ""),
            scale=str(sess.get("scale") or scale or ""),
            style_jump=bool(sess.get("style_jump")),
        )
        style_jump = str(pad_reason).startswith("style_jump")
        if policy_continuation and carry_image:
            suggested_paths: list[str] = [carry_image]
        elif eff_ref_img and not style_jump:
            suggested_paths = [eff_ref_img]
        else:
            suggested_paths = []
        caller_supplied = reference_image_paths is not None and bool(_norm_ref_paths(reference_image_paths))
        if not caller_supplied:
            reference_image_paths = list(suggested_paths)
        pad_diverged = caller_supplied and _norm_ref_paths(reference_image_paths) != _norm_ref_paths(suggested_paths)
        # Prompt follows the policy. Only pad=previous is a generated-plate continuation.
        continuation = policy_continuation
        actual_is_plate = bool(policy_continuation and carry_image) and (
            _norm_ref_paths([carry_image])[0] in _norm_ref_paths(reference_image_paths)
        )
        empty_pad = style_jump and not caller_supplied
        if empty_pad:
            eff_ref_paths = []
        elif reference_image_paths is not None:
            eff_ref_paths = list(reference_image_paths) if not isinstance(reference_image_paths, str) else [reference_image_paths]
        else:
            eff_ref_paths = list(
                sess.get("default_reference_image_paths")
                or sess.get("reference_image_paths")
                or ([eff_ref_img] if eff_ref_img else [])
            )
        matched_case_cfg = resolve_case_config(session_id, eff_ref_img)
        val_res: dict[str, Any] = {}
        if matched_case_cfg is not None or eff_ref_img or eff_ref_paths:
            eff_ref_for_val = eff_ref_img or (matched_case_cfg["ref_image"] if matched_case_cfg else "")
            try:
                val_res = validate_converge_params(
                    session_id=session_id or (matched_case_cfg["case_id"] if matched_case_cfg else ""),
                    scale=sess.get("scale", eff_scale),
                    ref_image="" if empty_pad else eff_ref_for_val,
                    aspect_ratio=eff_ar,
                    reference_image_paths=eff_ref_paths,
                    output_image_path=image if (image and not generate_cmd) else "",
                    root=root,
                    three_step_stage="step2_generate",
                    continuation_pad=actual_is_plate,
                    allow_empty_pad=empty_pad,
                )
                val_res["inherited_default_aspect_ratio"] = not bool((aspect_ratio or "").strip())
                val_res["inherited_default_pad_image"] = (not caller_supplied) and not empty_pad
                val_res["continuation_pad"] = actual_is_plate
                val_res["pad_diverged"] = pad_diverged
                eff_ar = val_res["aspect_ratio"]
                if not empty_pad:
                    eff_ref_paths = val_res["reference_image_paths"]
                for w_msg in val_res.get("warnings", []):
                    print(f"⚠️ [参数校验提示] {w_msg}")
            except (FileNotFoundError, ValueError) as exc:
                print(f"❌ [生成前硬性参数校验拦截] {exc}")
                return 1

        s_prof = get_converge_scale_profile(
            sess.get("scale", "medium"),
            recompose_dir=sess.get("recompose_dir", ""),
            goal=sess.get("goal", ""),
            ref_analysis=sess.get("ref_analysis", ""),
            ref_image=sess.get("ref_image", ""),
            module=sess.get("module", ""),
            medium_family=str(sess.get("medium_family") or ""),
            contract=str(sess.get("contract") or ""),
        )
        # Artist may loosen a dim mid-loop (still same --scale); fold into session + prompt.
        ov_now = _apply_lock_texts(lock_text or "", next_fix or "", prompt or "", source=f"generate_r{r_no}")
        from skills_kit.prompt_scale import format_lock_override_prompt_hint
        lock_hint = format_lock_override_prompt_hint(str(sess.get("scale") or "medium"), ov_now)
        stub_notes: list[str] = []
        floor_zh = ""
        if continuation:
            composed_prompt = compose_continuation_prompt(carry_fix or prompt, s_prof, stub_notes=stub_notes)
        else:
            composed_prompt = compose_style_first_prompt(prompt, s_prof, stub_notes=stub_notes)
            # R1 (and any non-continuation round) inject the English structure floor.
            # The Chinese twin is printed for the artist and is not sent to the model.
            floor_args = dict(
                goal=str(sess.get("goal") or goal or ""),
                ref_analysis=sess.get("ref_analysis") or ref_analysis or "",
                ref_image=eff_ref_img,
                module=str(sess.get("module") or module or ""),
            )
            floor = build_r1_structure_floor(**floor_args, lang="en")
            floor_zh = build_r1_structure_floor(**floor_args, lang="zh")
            if floor and floor not in composed_prompt:
                composed_prompt = f"{composed_prompt} | {floor}".strip(" |")
        if lock_hint:
            composed_prompt = f"{composed_prompt} | {lock_hint}".strip(" |")
        if not continuation and carry_fix and carry_fix not in composed_prompt:
            composed_prompt = f"{composed_prompt} | {carry_fix}".strip(" |")

        from improve import build_warm_start_pack, merge_warm_start_prompt
        warm = sess.get("warm_start") if isinstance(sess.get("warm_start"), dict) else {}
        if apply_memory:
            if not str(warm.get("prompt_block") or "").strip():
                warm = build_warm_start_pack(
                    root,
                    data if isinstance(data, dict) else {},
                    module=str(sess.get("module") or module or "brand.WorldStyle"),
                    goal=str(sess.get("goal") or goal or ""),
                )
                sess["warm_start"] = warm
            composed_prompt = merge_warm_start_prompt(composed_prompt, warm)

        if generate_cmd:
            proc = subprocess.run(
                generate_cmd,
                shell=True,
                cwd=str(root),
                capture_output=True,
                text=True,
            )
            if proc.returncode != 0:
                print(f"❌ 生成命令执行失败 (exit {proc.returncode}): {proc.stderr or proc.stdout}")
                return 1
            if image and (matched_case_cfg is not None or eff_ref_img or eff_ref_paths):
                try:
                    val_res = validate_converge_params(
                        session_id=session_id or (matched_case_cfg["case_id"] if matched_case_cfg else ""),
                        scale=sess.get("scale", eff_scale),
                        ref_image="" if empty_pad else (eff_ref_img or (matched_case_cfg["ref_image"] if matched_case_cfg else "")),
                        aspect_ratio=eff_ar,
                        reference_image_paths=eff_ref_paths,
                        output_image_path=image,
                        root=root,
                        three_step_stage="step2_generate",
                        continuation_pad=actual_is_plate,
                        allow_empty_pad=empty_pad,
                    )
                except (FileNotFoundError, ValueError) as exc:
                    print(f"❌ [生成后输出图比例校验拦截] {exc}")
                    return 1

        p_img = Path(image) if image else Path()
        if image and not p_img.is_file():
            cand = root / image
            if cand.is_file():
                p_img = cand
        img_v = _inspect_image_physical_traits(p_img) if image else {
            "exists": False,
            "size_bytes": 0,
            "size_kb": 0.0,
            "width": 0,
            "height": 0,
            "aspect_ratio": "unknown",
            "color_entropy": 0.0,
        }
        phys_gen = _physical_image_gate(img_v, image_path=str(image or ""), target_th=th)
        if phys_gen["blocked"]:
            why = "；".join(phys_gen["reasons"])
            print(f"❌ [生图闸门] 拒绝登记无效输出图：{why}")
            return 1

        gen_entry = {
            "round": r_no,
            "round_label": f"第 {r_no} 轮候选图（待独立审图）",
            "stage": "generated_pending_judge",
            "judged": False,
            "image": image,
            "image_verification": img_v,
            "aspect_ratio": eff_ar or img_v.get("canonical_aspect_ratio", ""),
            "reference_image_paths": eff_ref_paths,
            "param_validation": val_res,
            "step_trace": ["step1_start", "step2_generate"],
            "prompt": composed_prompt,
            "continuation": continuation,
            "policy_continuation": policy_continuation,
            "suggested_pad_paths": suggested_paths,
            "pad_diverged": pad_diverged,
            "pad_mode": pad_mode,
            "pad_reason": pad_reason,
            "score": None,
            "dims": "",
            "passed": False,
            "generated_at": _now_cst().strftime("%H:%M:%S"),
        }
        rounds = [r for r in rounds if r.get("round") != r_no]
        rounds.append(gen_entry)
        rounds.sort(key=lambda x: x["round"])
        sess["rounds"] = rounds
        sess["status"] = "generated_pending_judge"
        sess["ready_to_finish"] = False
        sess["ActionRequired"] = f"JUDGE_ROUND_{r_no}"
        _write_session_json(sf, sess)
        mark_active_session(root, session_id)

        v_badge = (
            f"{img_v.get('width')}x{img_v.get('height')} ({img_v.get('aspect_ratio')}, {img_v.get('size_kb')}KB)"
            if img_v.get("exists")
            else "待检出文件"
        )
        suggest_target = suggested_paths[0] if suggested_paths else "（无）"
        actual_shown = eff_ref_paths if eff_ref_paths else "（无）"
        diverge_bit = "（与策略建议不一致）" if pad_diverged else ""
        pad_line = (
            f"   · 策略建议垫图: {suggest_target}（{pad_reason}）\n"
            f"   · 本轮实际垫图: {actual_shown}{diverge_bit}\n"
        )
        floor_line = f"   · 结构底线: {floor_zh}\n" if floor_zh else ""
        warm_n_red = len((warm or {}).get("top_redlines") or [])
        warm_n_rec = len((warm or {}).get("top_recipes") or [])
        memory_line = ""
        if apply_memory and str((warm or {}).get("prompt_block") or "").strip():
            memory_line = (
                f"   · 📚 pmem-art 已自动并入记忆：模块 {warm.get('module') or sess.get('module') or '?'} "
                f"（recipe {warm_n_rec} · 红线 {warm_n_red}）\n"
            )
        stub_line = ""
        if stub_notes:
            stub_line = "   · 已从生图提示词去掉玩具媒介词: " + "、".join(stub_notes) + "\n"
        fix_line = ""
        if continuation and carry_fix and carry_fix not in composed_prompt:
            fix_line = f"   · 改点: {carry_fix}\n"
        print(
            f"🎨 [Step 2A · 仅生图阶段完成] 第 {r_no}/{mr} 轮图像已生成: `{image}` ({v_badge})\n"
            f"{pad_line}"
            f"{memory_line}"
            f"{floor_line}"
            f"{fix_line}"
            f"{stub_line}"
            f"   · 置顶风格指令 Prompt: {composed_prompt}\n"
            f"   · 当前未执行任何自评或 VLM 裁判；请先看图再打六维，不要从 9.3 起跳：\n"
            f"{agent_absolute_5d_judge_prompt(round_num=r_no, max_rounds=mr)}\n"
            f"   · 然后：`python3 pmem_art.py converge judge --id {session_id} --round {r_no} --image {image} --dims ...`"
        )
        return 0

    if action in ("judge", "round"):
        from improve import craft_lessons_from_round, print_round_lessons

        if generate_cmd:
            print("❌ [生成与评分隔离拦截] `converge judge` 独立审图阶段严禁传入 `--generate-cmd` 生图命令！")
            return 1

        # Prefer pending (unjudged) round; default missing "judged" to False so malformed rows don't open phantom rounds.
        r_no = round_num if round_num > 0 else (
            len(rounds) if rounds and not rounds[-1].get("judged", False) else (len(rounds) + 1)
        )
        existing_r = next((r for r in rounds if r.get("round") == r_no), None)
        if existing_r is None:
            print(
                f"❌ [生成与评分隔离拦截] 第 {r_no} 轮尚无 `converge generate` 记录，禁止直接 `judge`/`round`。\n"
                f"   👉 请先：`python3 pmem_art.py converge generate --id {session_id} --round {r_no} --image <path> --prompt <prompt>`"
            )
            return 1
        trace = existing_r.get("step_trace") or []
        has_generate = (
            "step2_generate" in trace
            or existing_r.get("stage") == "generated_pending_judge"
        )
        if not has_generate:
            print(
                f"❌ [生成与评分隔离拦截] 第 {r_no} 轮缺少 generate 轨迹（step_trace={trace!r}），禁止审图。\n"
                f"   👉 请先 `converge generate` 再 `converge judge`。"
            )
            return 1
        eff_image = image or (existing_r.get("image", "") if existing_r else "")
        recorded_gen_prompt = existing_r.get("prompt", "") if existing_r else ""

        judged_rounds = [
            r for r in rounds
            if r.get("judged") and r.get("score") is not None and r.get("round") != r_no
        ]
        already_passed = [r for r in judged_rounds if _round_counts_as_passed(r, th, root=root)]
        if already_passed and r_no > already_passed[0].get("round", 1):
            p_r = already_passed[0]
            sess["status"] = "converged"
            sess["ready_to_finish"] = True
            sess["converged_at_round"] = p_r["round"]
            _write_session_json(sf, sess)
            print(
                f"🛑 [动态达标停机拦截] 会话已在第 {p_r['round']} 轮达到 {p_r['score']:.2f} >= {th:.2f} 达标停止，"
                f"禁止继续执行第 {r_no} 轮！请直接运行 `python3 pmem_art.py converge finish --id {session_id}`。"
            )
            return 0
        if r_no > mr:
            print(f"🛑 已超过最大轮次上限 ({mr} 轮)，请直接运行 `python3 pmem_art.py converge finish --id {session_id}` 结算最高分图。")
            return 1

        prev_sc = None
        if judged_rounds:
            prev = max(judged_rounds, key=lambda x: x.get("round", 0))
            try:
                prev_sc = float(prev.get("score", 0))
            except (TypeError, ValueError):
                prev_sc = None

        s_prof = get_converge_scale_profile(
            sess.get("scale", "medium"),
            recompose_dir=sess.get("recompose_dir", ""),
            goal=sess.get("goal", ""),
            ref_analysis=sess.get("ref_analysis", ""),
            ref_image=sess.get("ref_image", ""),
            module=sess.get("module", ""),
            medium_family=str(sess.get("medium_family") or ""),
            contract=str(sess.get("contract") or ""),
        )
        s_prof = dict(s_prof)
        s_prof["target_score_threshold"] = th
        s_prof["max_rounds"] = mr

        cli_score = float(score or 0)
        # Independent VLM if keyed; else Agent Absolute-5D (threshold stays session 9.5).
        # Official score is the judge's five dimensions. Pixel offline scores are not used.
        judge_res = auto_vlm_judge_image(
            image_path=eff_image,
            scale_prof=s_prof,
            round_num=r_no,
            prev_score=prev_sc,
            dims=dims,
            defects=defects,
            next_fix=next_fix,
            raw_score=None,
            root=root,
            module=str(sess.get("module") or ""),
            data=data if isinstance(data, dict) else {},
            goal=str(sess.get("goal") or goal or ""),
            strengths=strengths,
            session_id=str(session_id or sess.get("session_id") or ""),
            ref_image=str(sess.get("ref_image") or ref_image or ""),
        )
        if judge_res.get("strengths") and not strengths:
            strengths = str(judge_res.get("strengths") or "")
        if judge_res.get("dims") and not dims:
            dims = str(judge_res.get("dims") or "")
        if judge_res.get("defects"):
            defects = str(judge_res.get("defects") or defects)
        if judge_res.get("next_fix") and judge_res.get("decision") != "STOP_TARGET_REACHED":
            next_fix = str(judge_res.get("next_fix") or next_fix)
        score = judge_res["calibrated_score"]
        passed = judge_res["passed"]
        gate_notes: list[str] = []
        if judge_res.get("image_gate_blocked"):
            for w in judge_res.get("audit_warnings") or []:
                if "图像物理闸门" in str(w):
                    gate_notes.append(str(w).replace("图像物理闸门拦截：", "").strip())
            if not gate_notes:
                gate_notes.append("磁盘无有效生成图或图像内容无效")
        directive = str(s_prof.get("prompt_directive") or "")
        if not recorded_gen_prompt or (directive and directive not in recorded_gen_prompt):
            gate_notes.append("生成 prompt 未包含本档 prompt_directive")
        if str(s_prof.get("scale") or "") == "recompose":
            direction = str(sess.get("recompose_dir") or "").strip()
            if not direction or direction not in (recorded_gen_prompt or ""):
                gate_notes.append("生成 prompt 未包含指定构图方向")
            # Only the look-at-image writeup counts. Prompt / next_fix always
            # contain 「重构机位」 or --recompose-dir, which is not proof the plate moved.
            evidence_blob = " ".join(
                [
                    str(judge_res.get("strengths") or strengths or ""),
                    str(judge_res.get("defects") or defects or ""),
                ]
            )
            if not _recompose_change_evidence(evidence_blob, direction):
                gate_notes.append(
                    "recompose 未检出机位/布局变化证据（相对 --recompose-dir），拒绝贴原停机"
                )
        prior_prompts = [
            r for r in rounds
            if r.get("round") != r_no and str(r.get("prompt") or "").strip()
        ]
        if prior_prompts and recorded_gen_prompt and not bool((existing_r or {}).get("continuation")):
            first_prompt = str(min(prior_prompts, key=lambda x: x.get("round") or 0).get("prompt") or "")
            prev_prompt = str(max(prior_prompts, key=lambda x: x.get("round") or 0).get("prompt") or "")
            baseline = str(s_prof.get("prompt_delta_baseline") or "previous")
            compare_to = first_prompt if baseline == "first" else prev_prompt
            change = _prompt_change_ratio(compare_to, recorded_gen_prompt, directive)
            limit = float(s_prof.get("max_prompt_delta_ratio") or 1.0)
            if str(sess.get("contract") or "") != "split" and change > limit:
                gate_notes.append(f"prompt 改动 {change:.0%} 超过档位上限 {limit:.0%}")
        if cli_score > 0 and judge_res.get("weighted_score") is None:
            gate_notes.append(f"已忽略命令行 --score {cli_score:.2f}，六维未解析成功")
        early_safe_stop: str | None = None
        if gate_notes:
            passed = False
            score = min(float(score), round(th - 0.05, 2))
            judge_res["audit_warnings"] = list(judge_res.get("audit_warnings") or []) + gate_notes
            extra = "；".join(gate_notes)
            judge_res["defects"] = f"{judge_res.get('defects') or ''}；{extra}".strip("；")
            judge_res["passed"] = False
            judge_res["decision"] = "CONTINUE_NEXT_ROUND" if r_no < mr else "STOP_MAX_ROUNDS"
            judge_res["ready_to_finish"] = r_no >= mr
        should_continue = bool((not passed) and r_no < mr)

        # R4+ safe early-stop (drop / plateau) — hard-wired, not agent prose.
        if not passed and should_continue and not gate_notes:
            hist = [
                r for r in rounds
                if r.get("judged")
                and r.get("score") is not None
                and int(r.get("round") or 0) != r_no
            ]
            running_best: float | None = None
            no_improve = 0
            for r in sorted(hist, key=lambda x: int(x.get("round") or 0)):
                try:
                    sc_h = float(r.get("score"))
                except (TypeError, ValueError):
                    continue
                if running_best is None or sc_h > running_best + 1e-9:
                    running_best = sc_h
                    no_improve = 0
                else:
                    no_improve += 1
            best_before = running_best
            if best_before is None or float(score) > float(best_before) + 1e-9:
                no_improve_now = 0
            else:
                no_improve_now = no_improve + 1
            dims_now = coerce_dims_dict(judge_res.get("dims_parsed")) or _round_dims_dict(
                {"dims": judge_res.get("dims"), "dims_parsed": judge_res.get("dims_parsed")}
            )
            early_safe_stop = decide_round_stop(
                score_ok=True,
                total=float(score),
                dims=dims_now,
                round_num=r_no,
                min_rounds=int(s_prof.get("min_rounds_before_stop") or 1),
                threshold=th,
                anatomy_floor=float(sess.get("anatomy_floor") or DEFAULT_ANATOMY_FLOOR),
                best_total=best_before,
                no_improve_streak=no_improve_now,
                plateau_rounds=DEFAULT_PLATEAU_ROUNDS,
                regression_drop=float(sess.get("regression_drop") or DEFAULT_REGRESSION_DROP),
                early_stop_min_round=int(
                    sess.get("early_stop_min_round") or DEFAULT_EARLY_STOP_MIN_ROUND
                ),
            )
            if early_safe_stop in ("STOP_REGRESSION", "STOP_PLATEAU"):
                should_continue = False
                judge_res["decision"] = early_safe_stop
                judge_res["ready_to_finish"] = True
                warn_es = (
                    f"安全早停 {early_safe_stop}：第 {r_no} 轮起连续掉分/平台，"
                    f"保底结算历史最高分轮次（门槛 drop≥{sess.get('regression_drop') or DEFAULT_REGRESSION_DROP}，"
                    f"R≥{sess.get('early_stop_min_round') or DEFAULT_EARLY_STOP_MIN_ROUND}）"
                )
                judge_res["audit_warnings"] = list(judge_res.get("audit_warnings") or []) + [warn_es]

        merged_defects = judge_res.get("defects") or defects
        prior_defect_rows = [
            r for r in rounds
            if isinstance(r, dict) and int(r.get("round") or 0) < int(r_no)
        ]
        if prior_defect_rows and merged_defects:
            prev_def = str(max(prior_defect_rows, key=lambda x: int(x.get("round") or 0)).get("defects") or "")
            if _defect_text_copied(prev_def, str(merged_defects)):
                copied_warn = "裁判缺陷与上一轮几乎相同：必须对着本张像素重写，禁止复制上一轮 defects"
                print(f"⚠️ {copied_warn}")
                judge_res["audit_warnings"] = list(judge_res.get("audit_warnings") or []) + [copied_warn]

        skip_ahead = False
        delta = abs(float(score) - prev_sc) if prev_sc is not None else None
        if (
            not gate_notes
            and (sess.get("fast_track") or sess.get("converge_mode") == "fast")
            and float(score) >= soft_th
            and not passed
            and delta is not None
            and delta < 0.25
            and r_no >= 2
        ):
            skip_ahead = True

        lessons = craft_lessons_from_round(
            defects=merged_defects, strengths=strengths, next_fix=next_fix,
            score=float(score), dims="",
        )
        sess.setdefault("lessons_all", []).extend(lessons)

        prev_pv = dict((existing_r or {}).get("param_validation") or sess.get("param_validation") or {})
        prev_pv["three_step_verified"] = bool(existing_r is not None)
        prev_pv["three_step_stage"] = "step3_judge"
        prev_pv["validation_passed"] = bool(prev_pv.get("validation_passed", True))
        eff_round_ar = (
            (existing_r or {}).get("aspect_ratio")
            or sess.get("default_aspect_ratio")
            or sess.get("aspect_ratio")
            or judge_res["image_verification"].get("canonical_aspect_ratio", "")
        )
        eff_round_refs = (
            (existing_r or {}).get("reference_image_paths")
            or sess.get("default_reference_image_paths")
            or sess.get("reference_image_paths")
            or ([sess.get("ref_image")] if sess.get("ref_image") else [])
        )

        entry = {
            "round": r_no,
            "round_label": f"经过 {r_no} 轮达标定稿" if passed else (f"第 {r_no} 轮初稿" if r_no == 1 else f"第 {r_no} 轮精修"),
            "stage": "judged",
            "judged": True,
            "atomic_step": False,
            "three_step_verified": bool(existing_r is not None),
            "step_trace": ["step1_start", "step2_generate", "step3_judge"] if existing_r is not None else ["step3_judge"],
            "aspect_ratio": eff_round_ar,
            "reference_image_paths": eff_round_refs,
            "param_validation": prev_pv,
            "generated_at": (existing_r or {}).get("generated_at", ""),
            "image": eff_image,
            "image_verification": judge_res["image_verification"],
            "raw_score": judge_res["raw_score"],
            "score": round(float(score), 2),
            "target_score_threshold": th,
            "dims": judge_res["dims"],
            "dims_parsed": judge_res["dims_parsed"],
            "weighted_score": judge_res["weighted_score"],
            "audit_warnings": judge_res["audit_warnings"],
            "stagnated": judge_res["stagnated"],
            "strengths": strengths or "构图与基础色调符合要求",
            "defects": merged_defects or ("无明显硬伤，细节达标" if passed else "局部细节或光影仍需打磨"),
            "next_fix": (
                "已达标，无需继续叠加"
                if passed
                else (
                    strip_redline_tags_from_generation_text(next_fix)
                    or "保持原图画风笔触与留白透气感，微调局部色彩过渡与排线疏密节奏"
                )
            ),
            "prompt": recorded_gen_prompt or (compose_style_first_prompt(prompt, s_prof) if prompt else ""),
            "continuation": bool((existing_r or {}).get("continuation")),
            "passed": passed,
            "gate_blocked": bool(gate_notes),
            "image_gate_blocked": bool(judge_res.get("image_gate_blocked")),
            "anatomy_score": judge_res.get("anatomy_score"),
            "anatomy_floor": judge_res.get("anatomy_floor"),
            "anatomy_veto_blocked": bool(judge_res.get("anatomy_veto_blocked")),
            "subject_kind": judge_res.get("subject_kind") or "",
            "judge_source": judge_res.get("judge_source") or "agent_self_judge",
            "remote_vlm": judge_res.get("remote_vlm") or {},
            "should_continue_next_round": should_continue,
            "decision": judge_res["decision"],
            "early_safe_stop": early_safe_stop,
            "lessons": lessons,
            "skip_ahead_hint": skip_ahead,
            "recorded_at": _now_cst().strftime("%H:%M:%S"),
        }
        rounds = [r for r in rounds if r.get("round") != r_no]
        rounds.append(entry)
        rounds.sort(key=lambda x: x["round"])
        sess["rounds"] = rounds
        sess["ready_to_finish"] = bool(judge_res["ready_to_finish"])

        img_v = judge_res["image_verification"]
        v_badge = (
            f"{img_v.get('width')}x{img_v.get('height')} ({img_v.get('aspect_ratio')}, {img_v.get('size_kb')}KB, byteH={img_v.get('color_entropy')})"
            if img_v.get("exists")
            else "未检出物理文件"
        )

        src_badge = {
            "independent_vlm": "独立视觉 API",
            "agent_self_judge": "Agent 自评",
            "vlm_error_fallback": "API 失败→自评回退",
            "vlm_error": "API 失败",
        }.get(str(judge_res.get("judge_source") or ""), str(judge_res.get("judge_source") or ""))

        if passed:
            rounds = [r for r in rounds if r.get("round", 0) <= r_no]
            sess["rounds"] = rounds
            sess["converged_at_round"] = r_no
            sess["rounds_to_converge"] = r_no
            sess["status"] = "converged"
            sess["ActionRequired"] = "STOP_AND_FINISH"
            msg = (
                f"✅ [Step 2B · 六维审图 · {src_badge}] 第 {r_no} 轮得分 {score:.2f} >= 目标阈值 {th:.2f}（经过 {r_no} 轮迭代达标停止）！\n"
                f"   · 图像校验: {v_badge} | 六维: {judge_res['dims']}\n"
                f"   · ready_to_finish = True，请运行 `python3 pmem_art.py converge finish --id {session_id}` 完成定稿。"
            )
        elif skip_ahead and sess.get("draft_ok"):
            sess["status"] = "fast_soft_accept"
            sess["ActionRequired"] = "STOP_AND_FINISH"
            sess["ready_to_finish"] = True
            msg = (
                f"⚡ Fast-track 草稿软达标：第 {r_no} 轮 {score:.2f} ≥ {soft_th} 且 Δ 很小。"
                f"用户已允许草稿 — 可 `converge finish --id {session_id}`；正式交付仍建议冲到 ≥{th:.2f}。"
            )
        elif early_safe_stop in ("STOP_REGRESSION", "STOP_PLATEAU"):
            scored_rounds = [r for r in rounds if r.get("score") is not None]
            best = max(scored_rounds, key=lambda x: x["score"]) if scored_rounds else entry
            sess["status"] = "early_safe_stop"
            sess["ActionRequired"] = "STOP_PICK_BEST"
            sess["ready_to_finish"] = True
            msg = (
                f"🛑 [安全早停 · {early_safe_stop}] 第 {r_no}/{mr} 轮得分 {score:.2f}，"
                f"后半程掉分/平台，停止继续糊化。\n"
                f"   · 保底最高分：第 {best.get('round')} 轮 ({best.get('score'):.2f} 分: {best.get('image')})。\n"
                f"   · 请运行 `python3 pmem_art.py converge finish --id {session_id}` 结算。"
            )
        elif r_no >= mr:
            best = max([r for r in rounds if r.get("score") is not None], key=lambda x: x["score"])
            sess["status"] = "max_rounds_reached"
            sess["ActionRequired"] = "STOP_PICK_BEST"
            sess["ready_to_finish"] = True
            msg = (
                f"🏁 第 {r_no}/{mr} 轮得分 {score:.2f} < {th:.2f}，已满 {mr} 轮上限！\n"
                f"   · 全阶段最高分为第 {best['round']} 轮 ({best['score']:.2f} 分: {best['image']})。\n"
                f"   · 请立即运行 `python3 pmem_art.py converge finish --id {session_id}` 结算（默认写记忆并打印评分履历；只要一行结论加 `--quiet`）。"
            )
        else:
            sess["status"] = "continue"
            sess["ActionRequired"] = f"GENERATE_ROUND_{r_no + 1}"
            nxt_image, nxt_fix, nxt_round = _best_plate(rounds, r_no + 1, root)
            fix_line = nxt_fix or entry["next_fix"]
            msg = (
                f"🔄 [Step 2B · 六维审图 · {src_badge}] 第 {r_no}/{mr} 轮得分 {score:.2f} < 目标阈值 {th:.2f}（未达标继续下一轮第 {r_no + 1} 轮）。\n"
                f"   · 图像校验: {v_badge} | 六维: {judge_res['dims']}\n"
                f"   · 不合理处: {entry['defects']}\n"
            )
            if nxt_image:
                msg += (
                    f"   · 下一轮先垫这张再出图：第 {nxt_round} 轮 `{nxt_image}`\n"
                    f"   · 只改这一处：{fix_line}\n"
                    f"   · 生图参考图只用这一张。可先 `converge next --id {session_id}` 核对路径，画完再 generate。\n"
                )
            else:
                msg += f"   · 下一轮只改：{entry['next_fix']}\n"
            if skip_ahead:
                msg += (
                    f"   · ⚡ Fast-track 提示：已 ≥{soft_th} 且与上轮变化很小 — "
                    f"可少做大重生、做局部修正；最终采纳仍要 ≥{th:.2f}（非草稿）。\n"
                )
            msg += f"   👉 先用上面这张垫图出第 {r_no + 1} 轮，再 `converge generate`，然后 `converge judge`。"

        _write_session_json(sf, sess)
        mark_active_session(root, session_id)
        print(msg)
        print_round_lessons(lessons, silent=silent)
        return 0

    if action in ("finish", "table", "status"):
        if not rounds:
            print("ℹ️ 当前收敛会话还没有轮次记录（先 converge generate，再 converge judge，然后 finish）。")
            return 0

        s_prof_fin = sess.get("scale_profile") or get_converge_scale_profile(sess.get("scale", "medium"))
        canonical_th = float(sess.get("accept_threshold") or s_prof_fin.get("target_score_threshold", th))
        accept_th = canonical_th
        if sess.get("draft_ok") and (sess.get("fast_track") or sess.get("converge_mode") == "fast"):
            accept_th = min(accept_th, FAST_SOFT_THRESHOLD)

        def _score_of(r: dict[str, Any]) -> float:
            try:
                val = r.get("score")
                return float(val) if val is not None else -1.0
            except (TypeError, ValueError):
                return -1.0

        judged_for_finish = [r for r in rounds if _score_of(r) >= 0]
        if not judged_for_finish:
            print("ℹ️ 当前会话还没有完成审图的轮次（先 converge judge 再 finish）。")
            return 0

        def _structure_ok(row: dict[str, Any]) -> bool:
            return round_passes_structure_gates(
                goal=str(sess.get("goal") or ""),
                ref_analysis=str(sess.get("ref_analysis") or ""),
                module=str(sess.get("module") or ""),
                ref_image=str(sess.get("ref_image") or ""),
                defects=str(row.get("defects") or ""),
                dims=_round_dims_dict(row),
            )

        struct_ok = [r for r in judged_for_finish if _structure_ok(r)]
        pool = struct_ok if struct_ok else judged_for_finish
        if struct_ok and len(struct_ok) < len(judged_for_finish):
            sess["structure_gate_fallback"] = True

        passing_rounds = [
            r for r in pool
            if _round_counts_as_passed(r, accept_th, root=root)
        ]
        from .showcase_gate import can_accept_winner
        n_judged = len(judged_for_finish)
        mr = int(sess.get("max_rounds") or DEFAULT_MAX_ROUNDS)
        if passing_rounds:
            first_pass = min(passing_rounds, key=lambda x: x["round"])
            rounds = [r for r in rounds if r.get("round", 0) <= first_pass["round"]]
            sess["rounds"] = rounds
            winner = first_pass
            sess["converged_at_round"] = winner["round"]
            outcome_str = (
                f"✅ **经过 {winner['round']} 轮迭代达标定稿**（generate 与 judge 分步收敛，"
                f"第 {winner['round']} 轮达到 `{_score_of(winner):.2f} / 10.0` 分 ≥ `{accept_th:.2f}` 分档位目标线即刻停机）"
            )
            badge_text = f"经过 {len([r for r in rounds if _score_of(r) >= 0])} 轮达标定稿"
        else:
            winner = max(pool, key=lambda x: (_score_of(x), x.get("round") or 0))
            outcome_str = (
                f"⚠️ **共执行 {len(judged_for_finish)} 轮审图（目标阈值 `{accept_th:.2f}` 分），未达标，已挑选全阶段最高分**"
                f"（胜出：第 {winner['round']} 轮 `{_score_of(winner):.2f} / 10.0` 分）"
            )
            badge_text = f"共 {len(judged_for_finish)} 轮未达阈值，采用最高分"

        win_score = _score_of(winner)
        sess["showcase_ready"] = can_accept_winner(
            n_judged, win_score, threshold=float(accept_th), max_rounds=mr
        )
        if action == "finish" and not sess["showcase_ready"]:
            print(
                f"❌ 还不能 finish：最高 {win_score:.2f} < {float(accept_th):.2f}，"
                f"且只审了 {n_judged}/{mr} 轮。继续 converge generate / judge。"
                " 未满 4 轮且不到线时不能结算终稿，也不能复制成 final.jpg。"
            )
            _write_session_json(sf, sess)
            return 1

        if action == "finish":
            sess["winner"] = winner
            sess["rounds_to_converge"] = len(rounds)
            sess["convergence_badge"] = badge_text
            sess["status"] = "finished"
            _write_session_json(sf, sess)
            clear_active_session(root, session_id)
        else:
            # status / table 只预览，不能把会话标成 finished，否则 stop hook 会放行。
            _write_session_json(sf, sess)
            if not sess["showcase_ready"]:
                print(
                    "ℹ️ 这是预览，会话还没结算。未满 4 轮且不到 9.5 时不能当终稿，"
                    "继续 converge generate / judge。"
                )
            else:
                print("ℹ️ 这是预览。可以 `converge finish` 结算终稿。")

        warm = sess.get("warm_start") or {}
        md_lines = [
            f"### 🎯 自评收敛生图报告 — {sess.get('goal', '')}",
            "",
            f"- **目标模块**：`{sess.get('module')}`",
            f"- **收敛档位 (`--scale`)**：`{sess.get('scale', 'medium')}`（目标阈值 `>= {accept_th:.2f}` · 动态达标停机）",
            f"- **收敛模式**：`{sess.get('converge_mode', 'quality')}`"
            + (" · ⚡ FAST-TRACK" if sess.get("fast_track") else ""),
            f"- **生图模式**：{'🖼️ 垫图解构收敛模式 (`' + sess.get('ref_image', '') + '`)' if sess.get('ref_image') else '✍️ 纯文本指令收敛模式'}",
        ]
        if sess.get("recompose_dir"):
            md_lines.append(f"- **定向改构图指令 (`--recompose-dir`)**：`{sess.get('recompose_dir')}`")
        if warm.get("confidence") is not None:
            md_lines.append(f"- **Warm-Start 置信度**：`{warm.get('confidence')}`（私有记忆 `{len(warm.get('top_recipes') or []) + len(warm.get('top_redlines') or [])}` 条 · 跨项目共享卡 `{len(warm.get('shared_knowledge') or [])}` 张）")
        if sess.get("ref_analysis"):
            md_lines.append(f"- **参考图解构基准**：{sess.get('ref_analysis')}")
        md_lines.extend([
            f"- **收敛结论**：{outcome_str}",
            f"- **最终采用图片**：`{winner.get('image')}`（综合评分 **`{_score_of(winner):.2f}`** · {badge_text}）",
            "",
            "#### 📊 全阶段生图迭代评分与优劣分析总表",
            "",
            "| 迭代阶段 | 生成图片 | 综合评分 (满分10) | 合理 / 亮点之处 | 不合理 / 缺陷之处 | 下一轮叠加修正策略 | 结果 |",
            "| :---: | :--- | :---: | :--- | :--- | :--- | :---: |",
        ])

        for r in rounds:
            is_win = (r["round"] == winner["round"])
            badge = f"🏆 **达标定稿**" if is_win and passing_rounds else ("✅ 达标" if r.get("passed") else "🔄 继续迭代")
            sc = r.get("score")
            score_cell = "待审图" if sc is None else f"**{float(sc):.2f}**"
            score_cell += (f"<br><small>{r['dims']}</small>" if r.get("dims") else "")
            img_cell = f"`{r.get('image') or '-'}`"
            r_label = r.get("round_label") or f"第 {r['round']} 轮"
            md_lines.append(
                f"| {r_label} | {img_cell} | {score_cell} | {r.get('strengths', '-')} | {r.get('defects', '-')} | {r.get('next_fix', '-')} | {badge} |"
            )

        md_lines.append("")
        all_lessons = []
        for r in rounds:
            all_lessons.extend(r.get("lessons") or [])
        if not all_lessons:
            all_lessons = sess.get("lessons_all") or []
        if all_lessons:
            md_lines.append("#### 📚 本轮可学（能力提升）")
            md_lines.append("")
            seen = set()
            for L in all_lessons:
                key = (L.get("category"), L.get("lesson"))
                if key in seen:
                    continue
                seen.add(key)
                md_lines.append(f"- **[{L.get('category')}]** {L.get('lesson')} → _{L.get('drill')}_")
            md_lines.append("")

        if not passing_rounds:
            md_lines.append(
                f"> 💡 **阶段总结**：本次共迭代 {len(rounds)} 轮，最高分为第 {winner['round']} 轮（`{winner['score']:.2f}` 分），"
                f"仍留有轻微不足：「{winner.get('defects')}」，后续可针对该点微调或局部重绘。"
            )

        # Artist-facing scale contract footer — show base% → effective% when artist loosened a dim.
        try:
            from skills_kit.prompt_scale import format_scale_artist_footer, merge_dim_lock_overrides
            scale_now = str(sess.get("scale") or "medium")
            scrape_bits = [str(sess.get("goal") or ""), str(lock_text or "")]
            for r in rounds:
                scrape_bits.append(str(r.get("next_fix") or ""))
                scrape_bits.append(str(r.get("defects") or ""))
            ov_finish = merge_dim_lock_overrides(
                scale_now, sess.get("dim_lock_overrides") or {}, *scrape_bits
            )
            if ov_finish:
                sess["dim_lock_overrides"] = ov_finish
                _write_session_json(sf, sess)
            scale_footer = format_scale_artist_footer(
                scale_now,
                recompose_dir=str(sess.get("recompose_dir") or ""),
                goal=str(sess.get("goal") or ""),
                ref_analysis=str(sess.get("ref_analysis") or ""),
                ref_image=str(sess.get("ref_image") or ""),
                module=str(sess.get("module") or ""),
                dim_lock_overrides=ov_finish,
            )
            md_lines.append("")
            md_lines.append(scale_footer)
            md_lines.append("")
        except Exception:
            pass

        saved_paths: list[str] = []
        reflection_path = None
        tip = None
        doctor_tip = None
        if action == "finish" and apply_memory:
            from feedback import write_memory_entry
            from improve import write_session_reflection, ingest_term_to_knowledge

            for blob in (sess.get("goal", ""), sess.get("ref_analysis", "")):
                if blob:
                    ingest_term_to_knowledge(root, blob, source="converge_finish")
            for r in rounds:
                for blob in (r.get("defects", ""), r.get("next_fix", ""), r.get("strengths", "")):
                    if blob:
                        ingest_term_to_knowledge(root, blob, source="converge_finish")

            mod = sess.get("module") or "brand.WorldStyle"
            def _ensure_conv_asset(img_str: str, m_id: str, prompt_str: str) -> str:
                if not img_str:
                    return ""
                import shutil
                cand = Path(img_str)
                if not cand.is_absolute():
                    cand = root / img_str
                if not cand.is_file():
                    return img_str
                try:
                    rel_c = cand.resolve().relative_to(root.resolve()).as_posix()
                    if rel_c.startswith("assets/"):
                        return rel_c
                except Exception:
                    pass
                dom = m_id.split(".")[0] if "." in m_id else "misc"
                ent = m_id.split(".")[1].lower() if "." in m_id else "general"
                dest_rel = f"assets/{dom}/{ent}/{cand.name}"
                dest_p = root / dest_rel
                dest_p.parent.mkdir(parents=True, exist_ok=True)
                if cand.resolve() != dest_p.resolve():
                    shutil.copy2(str(cand), str(dest_p))
                try:
                    from classify import classify_asset, ensure_module_from_classification
                    cl = classify_asset(root, data, path=dest_rel, prompt=prompt_str)
                    cl["suggested_module"] = m_id
                    cl["domain"] = dom
                    cl["entity"] = m_id.split(".")[1] if "." in m_id else m_id
                    cl["canonical_rel"] = dest_rel
                    ensure_module_from_classification(root, data, cl, force_active=True)
                except Exception:
                    pass
                return dest_rel

            win_img = _ensure_conv_asset(
                winner.get("image", ""),
                mod,
                str(winner.get("prompt") or sess.get("goal") or ""),
            )
            if win_img:
                winner["image"] = win_img

            settle_word = "达标" if passing_rounds else "未达阈值，采用最高分"
            win_summary = f"[收敛胜出 {winner['score']:.2f}分] {sess.get('goal', '')[:50]} — {winner.get('strengths', '')[:30]}"
            win_caption = (
                f"🏆 收敛胜出定稿 ({winner['score']:.2f}/10分 · 经过{len(rounds)}轮{settle_word})："
                f"{sess.get('goal', '')}"
                + (f" · 亮点：{winner.get('strengths')}" if winner.get("strengths") else "")
            )
            win_body = (
                f"**【闭环收敛胜出定稿（经过 {len(rounds)} 轮{settle_word} · {winner['score']:.2f} 分）】**\n"
                f"- **生成目标**：{sess.get('goal')}\n"
                f"- **收敛档位**：{sess.get('scale', 'medium')} (目标阈值 >= {accept_th:.2f})\n"
                f"- **保留原因（亮点）**：{winner.get('strengths')}\n"
                f"- **最终使用 Prompt**：`{winner.get('prompt') or sess.get('goal')}`\n"
            )
            if sess.get("ref_image"):
                win_body += f"- **参考垫图**：`{sess.get('ref_image')}`（解构：{sess.get('ref_analysis')}）\n"
            if warm.get("prompt_block"):
                win_body += f"\n<details><summary>Warm-Start 包</summary>\n\n```\n{warm.get('prompt_block')}\n```\n</details>\n"
            met_bar = _score_of(winner) >= canonical_th
            recipe_status = "active" if met_bar else "provisional"
            p_rec = write_memory_entry(
                root,
                module=mod,
                kind="recipe",
                summary=win_summary,
                body=win_body,
                asset=win_img,
                role="approved" if met_bar else "reference",
                caption=win_caption,
                status=recipe_status,
                extra_meta={
                    "ai_params": {
                        "prompt": str(winner.get("prompt") or sess.get("goal") or ""),
                        "score": winner.get("score"),
                        "round": winner.get("round"),
                        "dims": winner.get("dims", ""),
                    }
                },
                replace_same_asset=met_bar,
            )
            saved_paths.append(str(p_rec.relative_to(root)))

            failed = [r for r in rounds if not r.get("passed") and r.get("defects")]
            if failed:
                def _soft_defects(text: object) -> bool:
                    try:
                        from improve.taste_profile import is_soft_defect_phrase
                        return is_soft_defect_phrase(str(text or ""))
                    except Exception:
                        s = str(text or "").strip()
                        return (not s) or s in ("微瑕", "几乎无") or s.startswith("几乎无")

                actionable = [r for r in failed if not _soft_defects(r.get("defects", ""))]
                if not actionable:
                    # Soft-only defects: keep audit in session reflection, skip redline habit seed
                    worst = None
                else:
                    worst = min(actionable, key=lambda x: x["score"])
                if worst is not None:
                    worst_img = _ensure_conv_asset(
                        worst.get("image", ""),
                        mod,
                        str(worst.get("prompt") or sess.get("goal") or ""),
                    )
                    red_summary = f"[收敛踩坑红线] {sess.get('goal', '')[:30]}：避免「{worst.get('defects', '')[:45]}」"
                    red_caption = (
                        f"❌ 第{worst['round']}轮收敛打回 ({worst['score']:.2f}分)："
                        f"{worst.get('defects', '')} → 修正：{worst.get('next_fix', '')}"
                    )
                    defect_bullets = "\n".join(
                        f"- 第 {r['round']} 轮 ({float(r.get('score') or 0):.2f}分) 不合理处：{r['defects']} → 修正：{r['next_fix']}"
                        for r in actionable
                    )
                    red_body = (
                        f"**【迭代过程中暴露的不合理项（下次生图直接规避）】**\n\n"
                        f"{defect_bullets}\n"
                    )
                    p_red = write_memory_entry(
                        root,
                        module=mod,
                        kind="style_redline",
                        summary=red_summary,
                        body=red_body,
                        asset=worst_img,
                        role="rejected",
                        caption=red_caption,
                        replace_same_asset=True,
                    )
                    saved_paths.append(str(p_red.relative_to(root)))

            sess["lessons_all"] = all_lessons
            reflection_path = write_session_reflection(root, sess, winner=winner, outcome=outcome_str)
            try:
                import json as _json
                ref_data = _json.loads(reflection_path.read_text(encoding="utf-8"))
                ref_data["lessons"] = all_lessons[:12]
                reflection_path.write_text(_json.dumps(ref_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            except Exception:
                pass
            saved_paths.append(str(reflection_path.relative_to(root)))

            md_lines.append("")
            md_lines.append("#### 🧠 已自动沉淀至 `.memory-art` 的记忆条目")
            for sp in saved_paths:
                md_lines.append(f"- `{sp}`")
            md_lines.append("")
            md_lines.append(
                "> 🔇 记忆沉淀已在后台完成（反思 + taste + learn 队列；不对用户旁白）。"
                "进阶 peek：`improve run` · `coach` · `learn suggest` · `progress`；只要一行结论用 `--quiet`。"
            )

            try:
                from improve import run_silent_autopilot
                auto = run_silent_autopilot(
                    root,
                    data,
                    session_id=session_id,
                    lessons=all_lessons,
                    defects=str(winner.get("defects") or ""),
                    strengths=str(winner.get("strengths") or ""),
                    winner=winner,
                    rounds=rounds,
                    source="converge_finish",
                )
                tip = auto.get("tip")
            except Exception as ex:
                tip = None
                if verbose:
                    print(f"⚠️ autopilot 跳过: {ex}")

        if action == "finish":
            try:
                from lifecycle import maybe_lazy_doctor_on_hook
                doctor_tip = maybe_lazy_doctor_on_hook(root, "converge_finish")
            except Exception:
                doctor_tip = None

        if action == "finish" and apply_memory:
            try:
                from pmem_art import refresh_atlas_silent
                refresh_atlas_silent(root)
            except Exception:
                pass
        board_rel = ""
        try:
            from skills_kit.process_board import write_process_board
            board_path = write_process_board(root, sess, winner=winner)
            board_rel = board_path.relative_to(root).as_posix()
            sess["process_board"] = board_rel
            _write_session_json(sf, sess)
            md_lines.extend(["", f"过程板（点开每张图）：`{board_rel}`", ""])
        except Exception as exc:
            md_lines.extend(["", f"过程板未写出：{exc}", ""])

        report_text = "\n".join(md_lines)
        report_file = root / ".memory-art" / "converge" / f"{session_id}_report.md"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        report_file.write_text(report_text + "\n", encoding="utf-8")

        want_full = (not silent) or action in ("table", "status") or verbose
        if action == "finish" and silent and not verbose:
            badge = "✅" if passing_rounds else "🏆"
            print(
                f"{badge} 收敛完成（{badge_text}）· 第 {winner.get('round')} 轮 "
                f"{_score_of(winner):.2f}/10 · `{winner.get('image')}`"
            )
            if board_rel:
                print(f"过程板（点开每张图）：{board_rel}")
            if tip:
                from improve import print_whisper_tip
                print_whisper_tip(tip)
            elif not apply_memory:
                print("（未写入记忆：已指定 --no-apply）")
            if doctor_tip:
                print(doctor_tip)
            print(f"📎 评分履历已写盘: {report_file.relative_to(root)} （去掉 --quiet 可在终端打印）")
        else:
            print(report_text)
            if action == "finish":
                if tip:
                    from improve import print_whisper_tip
                    print_whisper_tip(tip)
                if doctor_tip:
                    print(doctor_tip)
        return 0

    if action == "warm":
        from improve import build_warm_start_pack, print_warm_start
        mod = module
        if not mod and goal:
            from feedback import infer_module_from_text
            mod = infer_module_from_text(goal, data)
        pack = build_warm_start_pack(root, data, module=mod or "brand.WorldStyle", goal=goal or "")
        print_warm_start(pack)
        return 0

    print(f"未知 converge 子操作: {action}")
    return 1
