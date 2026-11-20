#!/usr/bin/env python3
"""B2 visual benchmark harness.

Dry-run / stub = plumbing only.
Empirical path: score real images with independent VLM, then assemble b2_last.json
with empirical=true. Doctor only flags regression when both last & baseline are empirical.

Usage:
  pyw -3 -u benchmarks/b2_visual_bench.py --dry-run
  pyw -3 -u benchmarks/b2_visual_bench.py --score-image path.png --task-id b2-char-expr --arm warm_start
  pyw -3 -u benchmarks/b2_visual_bench.py --assemble
  pyw -3 -u benchmarks/b2_visual_bench.py --compare-baseline
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

SUITE_PATH = Path(__file__).resolve().parent / "b2_visual_suite.yaml"
PROFILE_REL = Path(".memory-art") / "_profile" / "b2_last.json"
BASELINE_REL = Path(".memory-art") / "_profile" / "b2_baseline.json"
RESULTS_REL = Path(".memory-art") / "_profile" / "b2_results.jsonl"


def load_suite(path: Path = SUITE_PATH) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML required to load b2_visual_suite.yaml")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("suite root must be a mapping")
    tasks = data.get("tasks") or []
    if len(tasks) < 1:
        raise ValueError("suite needs at least one task")
    metrics = (data.get("compare") or {}).get("metrics") or []
    if len(metrics) < 1:
        raise ValueError("suite needs compare.metrics")
    return data


def validate_suite(suite: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    metric_ids = {m.get("id") for m in (suite.get("compare") or {}).get("metrics") or []}
    for t in suite.get("tasks") or []:
        tid = t.get("id") or "?"
        for mid in t.get("metrics") or []:
            if mid not in metric_ids:
                errors.append(f"task {tid} references unknown metric {mid}")
        if not (t.get("brief") or "").strip():
            errors.append(f"task {tid} missing brief")
    return errors


def stub_scores(suite: dict[str, Any]) -> dict[str, Any]:
    """Placeholder scores — explicitly marked non-empirical."""
    metric_ids = [m["id"] for m in (suite.get("compare") or {}).get("metrics") or []]
    arms = {}
    for arm in (suite.get("compare") or {}).get("arms") or ["cold_start", "warm_start"]:
        arms[arm] = {mid: None for mid in metric_ids}
    return {
        "layer": "B2",
        "empirical": False,
        "note": "stub only — replace with real VLM blind scores before claiming evolution",
        "suite_version": suite.get("version"),
        "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tasks": [t.get("id") for t in suite.get("tasks") or []],
        "arms": arms,
        "aggregate": {mid: None for mid in metric_ids},
    }


def write_profile(root: Path, payload: dict[str, Any], *, baseline: bool = False) -> Path:
    rel = BASELINE_REL if baseline else PROFILE_REL
    out = root / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out


def compare_to_baseline(root: Path, drop: float = 0.15) -> dict[str, Any]:
    last_p = root / PROFILE_REL
    base_p = root / BASELINE_REL
    if not last_p.is_file() or not base_p.is_file():
        return {"ok": True, "skipped": True, "reason": "missing b2_last or b2_baseline"}
    last = json.loads(last_p.read_text(encoding="utf-8"))
    base = json.loads(base_p.read_text(encoding="utf-8"))
    if not last.get("empirical") or not base.get("empirical"):
        return {
            "ok": True,
            "skipped": True,
            "reason": "non-empirical stub — no regression claim",
            "last_empirical": bool(last.get("empirical")),
            "baseline_empirical": bool(base.get("empirical")),
        }
    regressions: list[str] = []
    agg_l = last.get("aggregate") or {}
    agg_b = base.get("aggregate") or {}
    for mid, bval in agg_b.items():
        lval = agg_l.get(mid)
        if bval is None or lval is None:
            continue
        try:
            delta = float(lval) - float(bval)
        except (TypeError, ValueError):
            continue
        if delta <= -abs(drop):
            regressions.append(f"{mid}: {bval} → {lval} (Δ={delta:.3f})")
    return {
        "ok": not regressions,
        "skipped": False,
        "regressions": regressions,
        "drop_threshold": drop,
    }


def _parse_dim_map(dims: str) -> dict[str, float]:
    """Parse converge-style dims into English keys when possible."""
    out: dict[str, float] = {}
    aliases = {
        "构图": "composition",
        "光影": "lighting_color",
        "透视": "perspective_anatomy",
        "质感": "texture_detail",
        "风格": "spec_style",
        "无瑕度": "flawlessness",
        "无瑕疵": "flawlessness",
        "composition": "composition",
        "lighting_color": "lighting_color",
        "perspective_anatomy": "perspective_anatomy",
        "texture_detail": "texture_detail",
        "spec_style": "spec_style",
        "flawlessness": "flawlessness",
    }
    for part in re.split(r"[/,，|;]+", dims or ""):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"([A-Za-z_\u4e00-\u9fff]+)\s*[=:]?\s*(\d+(?:\.\d+)?)", part)
        if not m:
            continue
        key = aliases.get(m.group(1), m.group(1))
        out[key] = float(m.group(2))
    return out


def map_vlm_to_b2_metrics(
    *,
    task: dict[str, Any],
    dims: dict[str, float],
    overall: float | None,
) -> dict[str, float]:
    """Map six-dim / overall into suite metrics on 0–1 scale (honest proxy, not identity)."""
    def _n(v: float | None, default: float = 0.0) -> float:
        if v is None:
            return default
        return max(0.0, min(1.0, float(v) / 10.0))

    overall_n = _n(overall)
    wanted = list(task.get("metrics") or [])
    metrics: dict[str, float] = {}
    for mid in wanted:
        if mid == "brief_fit":
            metrics[mid] = overall_n
        elif mid == "style_consistency":
            metrics[mid] = _n(dims.get("spec_style"), overall_n)
        elif mid == "character_consistency":
            a = dims.get("perspective_anatomy")
            b = dims.get("composition")
            if a is not None and b is not None:
                metrics[mid] = (_n(a) + _n(b)) / 2.0
            else:
                metrics[mid] = overall_n
        elif mid == "layer_restore":
            metrics[mid] = _n(dims.get("flawlessness"), overall_n)
        elif mid == "spec_pass_rate":
            metrics[mid] = 1.0 if (overall is not None and float(overall) >= 9.5) else overall_n
        else:
            metrics[mid] = overall_n
    return metrics


def append_result(root: Path, row: dict[str, Any]) -> Path:
    path = root / RESULTS_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def score_task_image(
    root: Path,
    *,
    task_id: str,
    image: Path,
    arm: str = "warm_start",
    suite: dict[str, Any] | None = None,
    allow_agent_fallback: bool = False,
) -> dict[str, Any]:
    """Score one real image for a suite task via independent VLM (preferred)."""
    suite = suite or load_suite()
    task = next((t for t in (suite.get("tasks") or []) if t.get("id") == task_id), None)
    if task is None:
        raise ValueError(f"unknown task_id: {task_id}")
    img = image if image.is_file() else (root / image)
    if not img.is_file():
        raise FileNotFoundError(f"image not found: {image}")
    if img.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}:
        return {
            "ok": False,
            "empirical": False,
            "error": f"not an image file: {img.name}",
            "task_id": task_id,
            "arm": arm,
        }

    from vlm_judge import is_vlm_judge_configured, maybe_run_independent_vlm_judge

    if not is_vlm_judge_configured(root=root) and not allow_agent_fallback:
        return {
            "ok": False,
            "empirical": False,
            "error": "VLM API key not configured — pass --allow-agent-fallback only for plumbing tests",
            "task_id": task_id,
            "arm": arm,
        }

    res = maybe_run_independent_vlm_judge(
        str(img),
        root=root,
        goal=str(task.get("brief") or task.get("title") or ""),
        module=str(task.get("category") or ""),
        round_num=1,
    )
    source = str(res.get("source") or "")
    empirical = source == "independent_vlm"
    if not empirical and not allow_agent_fallback:
        return {
            "ok": False,
            "empirical": False,
            "error": res.get("error") or f"judge source={source}",
            "task_id": task_id,
            "arm": arm,
            "source": source,
        }

    dims_str = str(res.get("dims") or "")
    dim_map = _parse_dim_map(dims_str)
    overall = None
    try:
        # Prefer official weighted parse when dims present
        from skills_kit import parse_5d_dims as _p5

        parsed = _p5(dims_str) if dims_str else {}
        if isinstance(parsed, dict) and parsed.get("weighted_score") is not None:
            overall = float(parsed["weighted_score"])
            inner = parsed.get("parsed") if isinstance(parsed.get("parsed"), dict) else {}
            for k, v in inner.items():
                if isinstance(v, (int, float)):
                    dim_map[str(k)] = float(v)
    except Exception:
        if dim_map:
            overall = sum(dim_map.values()) / max(1, len(dim_map))

    metrics = map_vlm_to_b2_metrics(task=task, dims=dim_map, overall=overall)
    row = {
        "task_id": task_id,
        "arm": arm,
        "image": str(img.as_posix()),
        "source": source,
        "empirical": empirical,
        "overall": overall,
        "dims": dim_map,
        "metrics": metrics,
        "defects": res.get("defects") or "",
        "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    append_result(root, row)
    return {"ok": True, **row}


def assemble_empirical_report(
    root: Path,
    *,
    suite: dict[str, Any] | None = None,
    as_baseline: bool = False,
) -> dict[str, Any]:
    """Build aggregate from jsonl; empirical=true when ≥1 VLM row is used.

    Historical stub / agent-fallback lines are skipped and do not poison the report.
    """
    suite = suite or load_suite()
    results_path = root / RESULTS_REL
    rows: list[dict[str, Any]] = []
    if results_path.is_file():
        for line in results_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    metric_ids = [m["id"] for m in (suite.get("compare") or {}).get("metrics") or []]
    arms = list((suite.get("compare") or {}).get("arms") or ["cold_start", "warm_start"])
    arm_metrics: dict[str, dict[str, list[float]]] = {a: {mid: [] for mid in metric_ids} for a in arms}
    used = 0
    non_emp = 0
    for row in rows:
        if not row.get("ok", True) and row.get("metrics") is None:
            continue
        arm = str(row.get("arm") or "")
        if arm not in arm_metrics:
            continue
        if not row.get("empirical"):
            non_emp += 1
            continue
        metrics = row.get("metrics") or {}
        used += 1
        for mid, val in metrics.items():
            if mid in arm_metrics[arm] and val is not None:
                arm_metrics[arm][mid].append(float(val))

    def _mean(vals: list[float]) -> float | None:
        return round(sum(vals) / len(vals), 4) if vals else None

    arms_out: dict[str, dict[str, float | None]] = {}
    for arm, bucket in arm_metrics.items():
        arms_out[arm] = {mid: _mean(vs) for mid, vs in bucket.items()}

    # Aggregate prefers warm_start when present, else mean of arms with data
    aggregate: dict[str, float | None] = {}
    for mid in metric_ids:
        prefer = arms_out.get("warm_start", {}).get(mid)
        if prefer is not None:
            aggregate[mid] = prefer
            continue
        vals = [arms_out[a][mid] for a in arms if arms_out.get(a, {}).get(mid) is not None]
        aggregate[mid] = round(sum(vals) / len(vals), 4) if vals else None

    # Only VLM-backed rows contribute; leftover stubs must not block empirical=true.
    empirical = used > 0
    payload = {
        "layer": "B2",
        "empirical": empirical,
        "note": (
            "assembled from independent_vlm rows"
            + (f" (skipped {non_emp} non-empirical)" if non_emp else "")
            if empirical
            else "no VLM rows — not an evolution claim"
        ),
        "suite_version": suite.get("version"),
        "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tasks": [t.get("id") for t in suite.get("tasks") or []],
        "rows_used": used,
        "rows_non_empirical_skipped": non_emp,
        "arms": arms_out,
        "aggregate": aggregate,
    }
    path = write_profile(root, payload, baseline=as_baseline)
    payload["path"] = str(path)
    return payload


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="B2 visual benchmark harness")
    ap.add_argument("--suite", type=Path, default=SUITE_PATH)
    ap.add_argument("--root", type=Path, default=REPO)
    ap.add_argument("--dry-run", action="store_true", help="validate suite only")
    ap.add_argument("--record-stub", action="store_true", help="write non-empirical b2_last.json")
    ap.add_argument("--set-baseline-stub", action="store_true", help="write non-empirical b2_baseline.json")
    ap.add_argument("--compare-baseline", action="store_true")
    ap.add_argument("--score-image", type=Path, default=None, help="real image to score")
    ap.add_argument("--task-id", default="", help="suite task id for --score-image")
    ap.add_argument("--arm", default="warm_start", help="cold_start|warm_start")
    ap.add_argument(
        "--allow-agent-fallback",
        action="store_true",
        help="plumbing only: allow non-VLM judge (marks empirical=false)",
    )
    ap.add_argument("--assemble", action="store_true", help="build b2_last from jsonl results")
    ap.add_argument("--assemble-baseline", action="store_true", help="build b2_baseline from jsonl")
    args = ap.parse_args(argv)

    suite = load_suite(args.suite)
    errs = validate_suite(suite)
    if errs:
        print("SUITE_INVALID:")
        for e in errs:
            print(f"  - {e}")
        return 2
    print(f"SUITE_OK tasks={len(suite.get('tasks') or [])} layer={suite.get('layer')}")
    print("NOTE: B2 does not claim visual evolution until empirical=true scores are recorded.")

    acted = False
    if args.score_image is not None:
        acted = True
        if not args.task_id:
            print("ERROR: --task-id required with --score-image")
            return 2
        row = score_task_image(
            args.root,
            task_id=args.task_id,
            image=args.score_image,
            arm=args.arm,
            suite=suite,
            allow_agent_fallback=bool(args.allow_agent_fallback),
        )
        print(json.dumps(row, ensure_ascii=False, indent=2))
        if not row.get("ok"):
            return 1
    if args.assemble or args.assemble_baseline:
        acted = True
        payload = assemble_empirical_report(
            args.root, suite=suite, as_baseline=bool(args.assemble_baseline)
        )
        print(json.dumps({k: v for k, v in payload.items() if k != "path"}, ensure_ascii=False, indent=2))
        print(f"WROTE {payload.get('path')}")

    drop = float((suite.get("compare") or {}).get("regression_drop") or 0.15)
    if args.record_stub:
        acted = True
        path = write_profile(args.root, stub_scores(suite))
        print(f"WROTE_STUB {path.relative_to(args.root)}")
    if args.set_baseline_stub:
        acted = True
        path = write_profile(args.root, stub_scores(suite), baseline=True)
        print(f"WROTE_BASELINE_STUB {path.relative_to(args.root)}")
    if args.compare_baseline:
        acted = True
        report = compare_to_baseline(args.root, drop=drop)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report.get("ok") else 1

    if args.dry_run and not acted:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
