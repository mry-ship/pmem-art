"""技能套件可重复验证：section_cut + 关键单测 + 执行包行数。"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

from .skill_registry import build_registry, slice_route_body
from .skill_specs import SKILL_SPECS

# 执行包软上限：超了 verify 失败，逼裁执行卡（merge/draw 以「执行卡」为主包）
PACK_LINE_SOFT_MAX = 120


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def check_section_cut() -> dict[str, Any]:
    reg = build_registry(SKILL_SPECS)
    ok = bool(reg.get("section_cut_ok"))
    return {
        "name": "section_cut",
        "ok": ok,
        "fails": list(reg.get("section_cut_fails") or []),
        "stale_skills": list(reg.get("stale_skills") or []),
    }


def check_pack_line_limits() -> dict[str, Any]:
    reg = build_registry(SKILL_SPECS)
    bodies = {s["name"]: s["body"] for s in SKILL_SPECS}
    overs: list[str] = []
    sizes: dict[str, int] = {}
    for route in reg.get("routes") or []:
        rid = str(route.get("id") or "")
        skill = str(route.get("skill") or "")
        body = bodies.get(skill) or ""
        packed = slice_route_body(body, route)
        n = len(packed.splitlines()) if packed else 0
        sizes[rid] = n
        if n > PACK_LINE_SOFT_MAX:
            overs.append(f"{rid}:{n}>{PACK_LINE_SOFT_MAX}")
    return {
        "name": "pack_line_limits",
        "ok": not overs,
        "max": PACK_LINE_SOFT_MAX,
        "overs": overs,
        "sizes": sizes,
    }


def check_benchmark_cards(root: Path | None = None) -> dict[str, Any]:
    from .benchmark_catalog import load_all_cards

    cards = load_all_cards(root or _repo_root())
    need = {"merge.cabinet", "ui.casual_hud", "icon.app", "keyart.store"}
    missing = sorted(need - set(cards))
    return {
        "name": "benchmark_cards",
        "ok": not missing,
        "missing": missing,
        "count": len(cards),
    }


def check_installed_skills_match(root: Path | None = None) -> dict[str, Any]:
    """抽查已安装 SKILL.md 正文是否与 SKILL_SPECS 同步（防改了 specs 忘 install）。"""
    import hashlib
    import re

    from art_cli import rewrite_cli_invocations

    root = root or _repo_root()
    drifts: list[str] = []
    for spec in SKILL_SPECS:
        name = str(spec.get("name") or "")
        # install 会按本机改写 CLI 入口，比对前对齐
        body = rewrite_cli_invocations(str(spec.get("body") or ""))
        a = hashlib.sha256(body.strip().encode("utf-8")).hexdigest()[:16]
        for rel in (
            Path(".cursor") / "skills" / name / "SKILL.md",
            Path(".claude") / "skills" / name / "SKILL.md",
            Path(".agents") / "skills" / name / "SKILL.md",
        ):
            path = root / rel
            if not path.is_file():
                drifts.append(f"{name}:{rel.as_posix()}:missing_install")
                continue
            text = path.read_text(encoding="utf-8")
            if text.startswith("---"):
                m = re.match(r"^---\n.*?\n---\n?", text, flags=re.S)
                if m:
                    text = text[m.end() :]
            b = hashlib.sha256(text.strip().encode("utf-8")).hexdigest()[:16]
            if a != b:
                drifts.append(f"{name}:{rel.as_posix()}:body_drift")
    return {
        "name": "installed_skills_match",
        "ok": not drifts,
        "drifts": drifts,
        "hint": "不一致时跑 python3 pmem_art.py skills --install",
    }


def run_unittest_subset() -> dict[str, Any]:
    root = _repo_root()
    mods = [
        "tests.test_skill_hardening",
        "tests.test_skill_router",
        "tests.test_route_false_fire",
        "tests.test_route_advise",
        "tests.test_must_fix",
        "tests.test_warm_start_guardrails",
    ]
    env = dict(**{k: v for k, v in __import__("os").environ.items()})
    env["PMEM_ART_ALLOW_GATE_SKIP"] = "1"
    env["PMEM_ART_UNDER_TEST"] = "1"
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", *mods, "-q"],
        cwd=str(root),
        capture_output=True,
        text=True,
        env=env,
    )
    return {
        "name": "unittest_subset",
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout_tail": (proc.stdout or "")[-800:],
        "stderr_tail": (proc.stderr or "")[-800:],
    }


def verify_skills(root: Path | None = None, *, quick: bool = False) -> dict[str, Any]:
    checks = [
        check_section_cut(),
        check_pack_line_limits(),
        check_benchmark_cards(root),
        check_installed_skills_match(root),
    ]
    if not quick:
        checks.append(run_unittest_subset())
    ok = all(bool(c.get("ok")) for c in checks)
    return {"ok": ok, "checks": checks}


def cmd_skills_verify(root: Path, *, quick: bool = False) -> int:
    report = verify_skills(root, quick=quick)
    for c in report["checks"]:
        mark = "✅" if c.get("ok") else "❌"
        print(f"{mark} {c.get('name')}")
        if c.get("name") == "section_cut" and c.get("fails"):
            print("   fails:", "；".join(c["fails"][:8]))
        if c.get("name") == "pack_line_limits" and c.get("overs"):
            print("   overs:", "；".join(c["overs"][:12]))
            print(f"   soft_max={c.get('max')}")
        if c.get("name") == "benchmark_cards" and c.get("missing"):
            print("   missing:", ", ".join(c["missing"]))
        if c.get("name") == "installed_skills_match" and c.get("drifts"):
            print("   drifts:", "；".join(c["drifts"][:8]))
            print("  ", c.get("hint"))
        if c.get("name") == "unittest_subset" and not c.get("ok"):
            print((c.get("stderr_tail") or c.get("stdout_tail") or "")[-500:])
    if report["ok"]:
        print("✅ skills --verify 通过。若 pmem 记忆标 stale，请对照本结果 confirm/correction。")
        return 0
    print("❌ skills --verify 未通过。")
    return 1
