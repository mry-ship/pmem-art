"""Extra Art Doctor checks: skills on disk, candidate backlog, anchor gaps, repair tips."""
from __future__ import annotations

from pathlib import Path
from typing import Any

def _skill_install_roots(root: Path) -> list[Path]:
    return [
        root / ".cursor" / "skills",
        root / ".claude" / "skills",
        root / ".agents" / "skills",
    ]


_EXPECTED_SKILLS = (
    "pmem-agent",
    "pmem-draw",
    "pmem-lens",
    "pmem-touchup",
    "pmem-ui",
    "pmem-icon",
    "pmem-merge-ladder",
    "pmem-layer-split",
    "pmem-prompt",
    "pmem-style-lock",
    "pmem-critique",
    "pmem-atlas",
    "pmem-coach",
)


def check_skill_files(root: Path) -> dict[str, Any]:
    """Return missing skill folders across Cursor/Claude/Codex install roots."""
    missing: list[str] = []
    present_any: list[str] = []
    roots = [p for p in _skill_install_roots(root) if p.is_dir()]
    if not roots:
        return {
            "ok": False,
            "missing": list(_EXPECTED_SKILLS),
            "present": [],
            "hint": "未找到 .cursor/.claude/.agents skills 目录 — 可跑 skills --install",
        }
    for name in _EXPECTED_SKILLS:
        found = False
        for base in roots:
            skill_md = base / name / "SKILL.md"
            if skill_md.is_file():
                found = True
                break
        if found:
            present_any.append(name)
        else:
            missing.append(name)
    return {
        "ok": not missing,
        "missing": missing,
        "present": present_any,
        "hint": (
            f"缺失技能 {', '.join(missing)} → `{_cli()} skills --install`"
            if missing
            else ""
        ),
    }


def _cli() -> str:
    try:
        from art_cli import pmem_art_cli

        return pmem_art_cli()
    except Exception:
        return "pyw -3 -u pmem_art.py"


# Soft-signal kinds that Warm-Start can inject after promote-missing (default).
# recipe 缺 trust 只影响置信、不进 prompt；不进 doctor 迁移软信号，避免与 promote-missing 默认范围错位。
_PROMOTE_MISSING_KINDS = frozenset({"style_redline", "art_decision"})


def check_candidate_backlog(data: dict[str, Any], *, soft_limit: int = 20) -> dict[str, Any]:
    """Count explicit trust=candidate actives waiting for promote (not provisional fails)."""
    entries = [e for e in (data.get("entries") or []) if isinstance(e, dict)]
    live = [
        e
        for e in entries
        if str(e.get("status") or "active").lower()
        not in ("archived", "superseded", "inactive", "pending", "revoked", "provisional")
    ]
    # Explicit frontmatter only — missing trust is tracked separately (not promote-queue noise).
    candidates = [
        e
        for e in live
        if str(e.get("trust") or "").strip().lower() == "candidate"
    ]
    recipes = [e for e in candidates if e.get("kind") == "recipe"]
    redlines = [e for e in candidates if e.get("kind") == "style_redline"]
    overloaded = len(candidates) >= soft_limit
    return {
        "ok": not overloaded,
        "candidate_total": len(candidates),
        "candidate_recipes": len(recipes),
        "candidate_redlines": len(redlines),
        "soft_limit": soft_limit,
        "hint": (
            f"candidate 记忆 {len(candidates)} 条（recipe {len(recipes)}）—"
            f"请 `memory promote` 或 `memory revoke` 清理"
            if overloaded
            else ""
        ),
    }


def check_missing_trust(data: dict[str, Any], *, soft_limit: int = 1) -> dict[str, Any]:
    """Live redline/decision with no trust — blocked from prompt until promote-missing."""
    entries = [e for e in (data.get("entries") or []) if isinstance(e, dict)]
    missing = [
        e
        for e in entries
        if str(e.get("kind") or "") in _PROMOTE_MISSING_KINDS
        and str(e.get("status") or "active").lower()
        not in ("archived", "superseded", "inactive", "pending", "revoked", "provisional")
        and not str(e.get("trust") or "").strip()
    ]
    redlines = [e for e in missing if e.get("kind") == "style_redline"]
    decisions = [e for e in missing if e.get("kind") == "art_decision"]
    overloaded = len(missing) >= soft_limit
    return {
        "ok": not overloaded,
        "missing_total": len(missing),
        "missing_redlines": len(redlines),
        "missing_decisions": len(decisions),
        "missing_recipes": 0,
        "soft_limit": soft_limit,
        "hint": (
            f"缺 trust {len(missing)} 条（红线 {len(redlines)} · 拍板 {len(decisions)}）—"
            f"不进提示词；先 `memory audit`，确认后 "
            f"`memory promote-missing --to verified --by … --apply`"
            if overloaded
            else ""
        ),
    }


def check_visual_anchors(data: dict[str, Any]) -> dict[str, Any]:
    gaps = list(data.get("asset_gap_entries") or [])
    anchors = [
        e
        for e in (data.get("entries") or [])
        if isinstance(e, dict) and e.get("kind") == "visual_anchor"
    ]
    broken = [g for g in gaps if g]
    return {
        "ok": len(broken) == 0,
        "anchor_count": len(anchors),
        "gap_count": len(broken),
        "samples": [
            f"{g.get('module')}:{g.get('id')}" for g in broken[:6] if isinstance(g, dict)
        ],
        "hint": (
            f"缺图锚点 {len(broken)} → `{_cli()} hygiene` 或补资产"
            if broken
            else ""
        ),
    }


def build_repair_tips(
    *,
    skills: dict[str, Any],
    backlog: dict[str, Any],
    anchors: dict[str, Any],
    b2: dict[str, Any] | None = None,
    missing_trust: dict[str, Any] | None = None,
) -> list[str]:
    tips: list[str] = []
    for block in (skills, backlog, anchors, missing_trust or {}):
        hint = str(block.get("hint") or "").strip()
        if hint:
            tips.append(hint)
    b2 = b2 or {}
    if not b2.get("skipped") and not b2.get("ok"):
        regs = b2.get("regressions") or []
        tips.append(
            "B2 退化："
            + "；".join(str(x) for x in regs[:3])
            + f" → 复查 Warm-Start / 重跑 `benchmarks/b2_visual_bench.py`"
        )
    elif b2.get("skipped") and "missing" in str(b2.get("reason") or ""):
        tips.append(
            "尚无 B2 empirical 基线 — 真图盲评后 "
            "`pyw -3 -u benchmarks/b2_visual_bench.py --assemble`"
        )
    return tips


def collect_art_doctor_extras(root: Path, data: dict[str, Any]) -> dict[str, Any]:
    skills = check_skill_files(root)
    backlog = check_candidate_backlog(data)
    # Prefer on-disk audit: library JSON may omit or normalize trust differently.
    try:
        from .memory_trust import _DEFAULT_PROMOTE_MISSING_KINDS, audit_trust_entries

        report = audit_trust_entries(root, kinds=_DEFAULT_PROMOTE_MISSING_KINDS)
        missing = {
            "ok": report["missing_total"] < 1,
            "missing_total": report["missing_total"],
            "missing_redlines": sum(
                1 for r in report["missing_trust"] if r.get("kind") == "style_redline"
            ),
            "missing_decisions": sum(
                1 for r in report["missing_trust"] if r.get("kind") == "art_decision"
            ),
            "missing_recipes": 0,
            "soft_limit": 1,
            "hint": (
                f"缺 trust {report['missing_total']} 条（红线/拍板）—"
                f"不进提示词；先 `memory audit`，确认后 "
                f"`memory promote-missing --to verified --by … --apply`"
                if report["missing_total"]
                else ""
            ),
        }
    except Exception:
        missing = check_missing_trust(data)
    anchors = check_visual_anchors(data)
    return {
        "skills": skills,
        "candidate_backlog": backlog,
        "missing_trust": missing,
        "visual_anchors": anchors,
    }
